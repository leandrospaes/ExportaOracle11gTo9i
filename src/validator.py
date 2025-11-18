from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Iterable, List

import cx_Oracle

from .config import OracleConfig
from .db_utils import oracle_connection


OBJECT_TYPES = ["VIEW", "TRIGGER", "PROCEDURE", "FUNCTION"]


@dataclass
class ValidationDetail:
    category: str
    mismatches: List[str] = field(default_factory=list)

    def ok(self) -> bool:
        return not self.mismatches


@dataclass
class ValidationReport:
    tables: ValidationDetail
    synonyms: ValidationDetail
    grants: ValidationDetail
    objects: Dict[str, ValidationDetail]

    def all_valid(self) -> bool:
        return (
            self.tables.ok()
            and self.synonyms.ok()
            and self.grants.ok()
            and all(detail.ok() for detail in self.objects.values())
        )


class OracleValidator:
    def __init__(self, source: OracleConfig, target: OracleConfig):
        self.source = source
        self.target = target

    def validate(self, schemas: Iterable[str]) -> ValidationReport:
        schema_list = list(schemas) or [self.source.schema or self.source.user.upper()]
        with oracle_connection(self.source) as source_conn, oracle_connection(self.target) as target_conn:
            tables = self._validate_tables(source_conn, target_conn, schema_list)
            synonyms = self._compare_sets(source_conn, target_conn, schema_list, "SYNONYM", "ALL_SYNONYMS", "SYNONYM_NAME")
            grants = self._compare_grants(source_conn, target_conn, schema_list)
            obj_details = {
                obj_type: self._compare_objects(source_conn, target_conn, schema_list, obj_type)
                for obj_type in OBJECT_TYPES
            }
        return ValidationReport(tables=tables, synonyms=synonyms, grants=grants, objects=obj_details)

    def _validate_tables(
        self,
        source_conn: cx_Oracle.Connection,
        target_conn: cx_Oracle.Connection,
        schemas: list[str],
    ) -> ValidationDetail:
        mismatches: list[str] = []
        for schema in schemas:
            tables = self._list_tables(source_conn, schema)
            for table in tables:
                source_count = self._count_rows(source_conn, schema, table)
                target_count = self._count_rows(target_conn, schema, table)
                if source_count != target_count:
                    mismatches.append(f"{schema}.{table}: origem={source_count} destino={target_count}")
        return ValidationDetail(category="tables", mismatches=mismatches)

    @staticmethod
    def _list_tables(connection: cx_Oracle.Connection, schema: str) -> list[str]:
        cursor = connection.cursor()
        cursor.execute(
            """
            SELECT table_name
            FROM all_tables
            WHERE owner = :owner
            """,
            owner=schema.upper(),
        )
        return [name for (name,) in cursor]

    @staticmethod
    def _count_rows(connection: cx_Oracle.Connection, schema: str, table: str) -> int:
        cursor = connection.cursor()
        cursor.execute(f"SELECT COUNT(*) FROM {schema}.{table}")
        (count,) = cursor.fetchone()
        return int(count)

    def _compare_sets(
        self,
        source_conn: cx_Oracle.Connection,
        target_conn: cx_Oracle.Connection,
        schemas: list[str],
        category: str,
        view_name: str,
        object_column: str,
    ) -> ValidationDetail:
        mismatches: list[str] = []
        for schema in schemas:
            source_set = self._fetch_names(source_conn, view_name, object_column, schema)
            target_set = self._fetch_names(target_conn, view_name, object_column, schema)
            missing = source_set - target_set
            extra = target_set - source_set
            if missing:
                mismatches.append(f"{schema} faltando no destino: {sorted(missing)}")
            if extra:
                mismatches.append(f"{schema} objetos extras no destino: {sorted(extra)}")
        return ValidationDetail(category=category, mismatches=mismatches)

    @staticmethod
    def _fetch_names(connection: cx_Oracle.Connection, view_name: str, column: str, owner: str) -> set[str]:
        cursor = connection.cursor()
        cursor.execute(
            f"""
            SELECT {column}
            FROM {view_name}
            WHERE owner = :owner
            """,
            owner=owner.upper(),
        )
        return {name for (name,) in cursor}

    def _compare_grants(
        self,
        source_conn: cx_Oracle.Connection,
        target_conn: cx_Oracle.Connection,
        schemas: list[str],
    ) -> ValidationDetail:
        mismatches: list[str] = []
        for schema in schemas:
            source = self._fetch_grants(source_conn, schema)
            target = self._fetch_grants(target_conn, schema)
            missing = source - target
            extra = target - source
            if missing:
                mismatches.append(f"{schema} grants faltantes: {sorted(missing)}")
            if extra:
                mismatches.append(f"{schema} grants extras: {sorted(extra)}")
        return ValidationDetail(category="grants", mismatches=mismatches)

    @staticmethod
    def _fetch_grants(connection: cx_Oracle.Connection, schema: str) -> set[str]:
        cursor = connection.cursor()
        cursor.execute(
            """
            SELECT grantee || ':' || privilege || ':' || table_name
            FROM all_tab_privs
            WHERE owner = :owner
            """,
            owner=schema.upper(),
        )
        return {row[0] for row in cursor}

    def _compare_objects(
        self,
        source_conn: cx_Oracle.Connection,
        target_conn: cx_Oracle.Connection,
        schemas: list[str],
        obj_type: str,
    ) -> ValidationDetail:
        detail = self._compare_sets(
            source_conn,
            target_conn,
            schemas,
            category=obj_type.lower(),
            view_name="ALL_OBJECTS",
            object_column="OBJECT_NAME",
        )
        detail.mismatches = [
            msg for msg in detail.mismatches if obj_type.upper() in msg.upper()
        ] or detail.mismatches
        return detail

