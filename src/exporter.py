from __future__ import annotations

import logging
from typing import Iterable

import cx_Oracle

from .config import OracleConfig
from .db_utils import chunked, execute_non_query, oracle_connection


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

DDL_OBJECTS = ["TABLE", "VIEW", "SYNONYM", "TRIGGER", "PROCEDURE", "FUNCTION", "PACKAGE", "PACKAGE BODY"]


class OracleExporter:
    def __init__(self, source: OracleConfig, target: OracleConfig, batch_size: int = 500):
        self.source = source
        self.target = target
        self.batch_size = batch_size

    def copy(self, schemas: Iterable[str]) -> None:
        schema_list = list(schemas) or [self.source.schema or self.source.user.upper()]
        for schema in schema_list:
            logger.info("Iniciando exportação do schema %s", schema)
            with oracle_connection(self.source) as source_conn, oracle_connection(self.target) as target_conn:
                self._copy_ddl(source_conn, target_conn, schema)
                self._copy_data(source_conn, target_conn, schema)
            logger.info("Schema %s concluído", schema)

    def _copy_ddl(self, source_conn: cx_Oracle.Connection, target_conn: cx_Oracle.Connection, schema: str) -> None:
        logger.info("Copiando objetos de metadados para %s", schema)
        cursor = source_conn.cursor()
        cursor.callproc("DBMS_METADATA.SET_TRANSFORM_PARAM", ("SESSION_TRANSFORM", "STORAGE", False))
        cursor.callproc("DBMS_METADATA.SET_TRANSFORM_PARAM", ("SESSION_TRANSFORM", "SEGMENT_ATTRIBUTES", False))
        cursor.callproc("DBMS_METADATA.SET_TRANSFORM_PARAM", ("SESSION_TRANSFORM", "SQLTERMINATOR", True))

        for object_type in DDL_OBJECTS:
            cursor.execute(
                """
                SELECT object_name, dbms_metadata.get_ddl(object_type => :obj_type, name => object_name, schema => owner) ddl
                FROM all_objects
                WHERE owner = :owner
                  AND object_type = :obj_type
                  AND generated = 'N'
                ORDER BY object_name
                """,
                obj_type=object_type,
                owner=schema.upper(),
            )
            for name, ddl in cursor:
                logger.debug("Aplicando DDL %s.%s (%s)", schema, name, object_type)
                try:
                    execute_non_query(target_conn, ddl.read() if hasattr(ddl, "read") else ddl)
                except cx_Oracle.DatabaseError as exc:
                    error, = exc.args
                    if error.code in (955, 2264, 1430):
                        logger.warning("Objeto %s já existe em %s, ignorando. %s", name, schema, error.message)
                    else:
                        raise

    def _copy_data(self, source_conn: cx_Oracle.Connection, target_conn: cx_Oracle.Connection, schema: str) -> None:
        logger.info("Copiando dados das tabelas de %s", schema)
        tables = self._list_tables(source_conn, schema)
        for table in tables:
            logger.info("Tabela %s.%s", schema, table)
            self._truncate_target_table(target_conn, schema, table)
            rows, columns = self._fetch_rows(source_conn, schema, table)
            self._insert_rows(target_conn, schema, table, columns, rows)

    @staticmethod
    def _list_tables(connection: cx_Oracle.Connection, schema: str) -> list[str]:
        cursor = connection.cursor()
        cursor.execute(
            """
            SELECT table_name
            FROM all_tables
            WHERE owner = :owner
              AND temporary = 'N'
            ORDER BY table_name
            """,
            owner=schema.upper(),
        )
        return [name for (name,) in cursor]

    @staticmethod
    def _fetch_rows(connection: cx_Oracle.Connection, schema: str, table: str):
        cursor = connection.cursor()
        cursor.execute(
            """
            SELECT column_name
            FROM all_tab_columns
            WHERE owner = :owner
              AND table_name = :table
            ORDER BY column_id
            """,
            owner=schema.upper(),
            table=table,
        )
        columns = [name for (name,) in cursor]
        query = f'SELECT {", ".join(columns)} FROM {schema}.{table}'
        cursor.execute(query)
        return cursor.fetchall(), columns

    def _insert_rows(
        self,
        connection: cx_Oracle.Connection,
        schema: str,
        table: str,
        columns: list[str],
        rows: list[tuple],
    ) -> None:
        if not rows:
            logger.info("Nenhuma linha para %s.%s", schema, table)
            return

        placeholders = ", ".join([f":{idx+1}" for idx in range(len(columns))])
        insert_sql = f'INSERT INTO {schema}.{table} ({", ".join(columns)}) VALUES ({placeholders})'

        with connection.cursor() as cursor:
            for batch in chunked(rows, self.batch_size):
                cursor.executemany(insert_sql, batch)
            connection.commit()

    @staticmethod
    def _truncate_target_table(connection: cx_Oracle.Connection, schema: str, table: str) -> None:
        sql = f"TRUNCATE TABLE {schema}.{table}"
        try:
            execute_non_query(connection, sql)
        except cx_Oracle.DatabaseError as exc:
            error, = exc.args
            if error.code == 942:
                logger.warning("Tabela %s.%s não encontrada no destino; será criada via DDL", schema, table)
            else:
                raise

