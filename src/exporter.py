from __future__ import annotations

import logging
from typing import Iterable

import cx_Oracle

from .config import OracleConfig
from .db_utils import chunked, execute_non_query, oracle_connection


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Para Oracle 9i, usar PACKAGE_BODY (com underscore) ao invés de "PACKAGE BODY"
DDL_OBJECTS = ["TABLE", "VIEW", "SYNONYM", "TRIGGER", "PROCEDURE", "FUNCTION", "PACKAGE", "PACKAGE_BODY"]


class OracleExporter:
    def __init__(self, source: OracleConfig, target: OracleConfig, batch_size: int = 500):
        self.source = source
        self.target = target
        self.batch_size = batch_size

    def copy(self, schemas: Iterable[str]) -> None:
        schema_list = list(schemas) or [self.source.schema or self.source.user.upper()]
        total_schemas = len(schema_list)
        logger.info("=" * 70)
        logger.info("INICIANDO PROCESSO DE EXPORTAÇÃO")
        logger.info("=" * 70)
        logger.info("Schemas a processar: %s", ", ".join(schema_list))
        logger.info("Banco de origem: %s", self.source.dsn)
        logger.info("Banco de destino: %s", self.target.dsn)
        logger.info("Tamanho do lote: %d linhas", self.batch_size)
        logger.info("")
        
        for idx, schema in enumerate(schema_list, 1):
            logger.info("=" * 70)
            logger.info("PROCESSANDO SCHEMA %d/%d: %s", idx, total_schemas, schema)
            logger.info("=" * 70)
            
            # Estabelecer conexões separadamente para melhor tratamento de erros
            try:
                logger.info("Conectando ao banco de origem (11g)...")
                source_conn = None
                target_conn = None
                try:
                    source_conn_context = oracle_connection(self.source)
                    source_conn = source_conn_context.__enter__()
                    logger.info("✓ Conexão com banco de origem estabelecida")
                except Exception as e:
                    logger.error("✗ Falha ao conectar ao banco de ORIGEM (11g): %s", e)
                    logger.error("  DSN: %s", self.source.dsn)
                    logger.error("  Usuário: %s", self.source.user)
                    if self.source.client_path:
                        logger.error("  Oracle Client Path: %s", self.source.client_path)
                    raise
                
                try:
                    logger.info("Conectando ao banco de destino (9i)...")
                    target_conn_context = oracle_connection(self.target)
                    target_conn = target_conn_context.__enter__()
                    logger.info("✓ Conexão com banco de destino estabelecida")
                except Exception as e:
                    logger.error("✗ Falha ao conectar ao banco de DESTINO (9i): %s", e)
                    logger.error("  DSN: %s", self.target.dsn)
                    logger.error("  Usuário: %s", self.target.user)
                    if self.target.client_path:
                        logger.error("  Oracle Client Path configurado: %s", self.target.client_path)
                    else:
                        logger.error("  ⚠ ORACLE_9I_CLIENT_PATH NÃO ESTÁ CONFIGURADO!")
                        logger.error("")
                        logger.error("  Para conectar ao Oracle 9i, você PRECISA configurar:")
                        logger.error("  ORACLE_9I_CLIENT_PATH=C:\\caminho\\para\\instantclient_11_2")
                        logger.error("  no arquivo .env ou como variável de ambiente")
                    raise
                
                try:
                    self._copy_ddl(source_conn, target_conn, schema)
                    self._copy_data(source_conn, target_conn, schema)
                finally:
                    # Fechar conexões
                    if target_conn:
                        try:
                            target_conn_context.__exit__(None, None, None)
                        except:
                            pass
                    if source_conn:
                        try:
                            source_conn_context.__exit__(None, None, None)
                        except:
                            pass
            except Exception as e:
                # Re-raise para manter o comportamento original
                raise
            logger.info("")
            logger.info("✓ Schema %s concluído com sucesso", schema)
            logger.info("")
        
        logger.info("=" * 70)
        logger.info("EXPORTAÇÃO CONCLUÍDA COM SUCESSO")
        logger.info("Total de schemas processados: %d", total_schemas)
        logger.info("=" * 70)

    def _copy_ddl(self, source_conn: cx_Oracle.Connection, target_conn: cx_Oracle.Connection, schema: str) -> None:
        logger.info(">>> Etapa 1/2: Copiando objetos DDL (metadados)")
        logger.info("Configurando DBMS_METADATA...")
        cursor = source_conn.cursor()
        
        # Usar execute ao invés de callproc para melhor compatibilidade com cx_Oracle 6.x
        try:
            cursor.execute("""
                BEGIN
                    DBMS_METADATA.SET_TRANSFORM_PARAM(DBMS_METADATA.SESSION_TRANSFORM, 'STORAGE', FALSE);
                    DBMS_METADATA.SET_TRANSFORM_PARAM(DBMS_METADATA.SESSION_TRANSFORM, 'SEGMENT_ATTRIBUTES', FALSE);
                    DBMS_METADATA.SET_TRANSFORM_PARAM(DBMS_METADATA.SESSION_TRANSFORM, 'SQLTERMINATOR', TRUE);
                END;
            """)
            logger.info("✓ Configuração do DBMS_METADATA concluída")
        except cx_Oracle.DatabaseError as e:
            error, = e.args
            # Se DBMS_METADATA não estiver disponível, continuar sem as transformações
            if error.code in (4043, 6550):  # Package não existe ou não acessível
                logger.warning("DBMS_METADATA não disponível, continuando sem transformações")
            else:
                raise

        total_objects = 0
        for object_type in DDL_OBJECTS:
            logger.info("  Processando objetos do tipo: %s", object_type)
            
            # Para Oracle 9i, "PACKAGE BODY" deve ser consultado como "PACKAGE BODY" mas usado como "PACKAGE_BODY" no GET_DDL
            query_object_type = object_type
            if object_type == "PACKAGE_BODY":
                # No all_objects, o tipo é "PACKAGE BODY" (com espaço)
                query_object_type = "PACKAGE BODY"
            
            try:
                cursor.execute(
                    """
                    SELECT object_name, dbms_metadata.get_ddl(object_type => :obj_type, name => object_name, schema => owner) ddl
                    FROM all_objects
                    WHERE owner = :owner
                      AND object_type = :query_type
                      AND generated = 'N'
                    ORDER BY object_name
                    """,
                    obj_type=object_type.replace("_", " "),  # Converter PACKAGE_BODY para "PACKAGE BODY" para GET_DDL
                    query_type=query_object_type,  # Usar "PACKAGE BODY" para consulta em all_objects
                    owner=schema.upper(),
                )
                objects = list(cursor)
            except cx_Oracle.DatabaseError as e:
                error, = e.args
                if error.code == 31600:  # ORA-31600: invalid input value for parameter OBJECT_TYPE
                    logger.warning("    Tipo de objeto '%s' não suportado pelo DBMS_METADATA neste banco, pulando...", object_type)
                    objects = []
                else:
                    raise
            if objects:
                logger.info("    Encontrados %d objeto(s) do tipo %s", len(objects), object_type)
                for name, ddl in objects:
                    try:
                        # Converter DDL para string e limpar
                        # Para objetos grandes (PACKAGE, PACKAGE_BODY), ler completamente
                        if hasattr(ddl, "read"):
                            # Se for um LOB, ler todo o conteúdo
                            try:
                                if hasattr(ddl, "size"):
                                    # LOB tem método size(), ler tudo de uma vez
                                    ddl_str = ddl.read(ddl.size())
                                else:
                                    # Tentar ler em chunks
                                    chunks = []
                                    while True:
                                        chunk = ddl.read(8192)  # Ler 8KB por vez
                                        if not chunk:
                                            break
                                        chunks.append(chunk)
                                    ddl_str = "".join(chunks)
                            except Exception as e_read:
                                logger.warning("    ⚠ Erro ao ler LOB completo, tentando método alternativo: %s", e_read)
                                # Fallback: tentar ler como string
                                ddl_str = str(ddl)
                        else:
                            ddl_str = str(ddl)
                        
                        # Verificar se o DDL está vazio ou muito curto (pode indicar truncamento)
                        if not ddl_str or len(ddl_str.strip()) < 10:
                            logger.warning("    ⚠ %s.%s: DDL muito curto ou vazio, pode estar truncado", schema, name)
                            if object_type in ("PACKAGE", "PACKAGE_BODY"):
                                logger.warning("    Tentando obter DDL completo usando método alternativo...")
                                # Tentar obter via ALL_SOURCE para packages
                                try:
                                    ddl_str = self._get_package_ddl_from_source(source_conn, schema, name, object_type)
                                except Exception as e_alt:
                                    logger.error("    ✗ Não foi possível obter DDL alternativo: %s", e_alt)
                        
                        # Para tabelas, fazer DROP se já existir antes de criar
                        if object_type == "TABLE":
                            if self._table_exists(target_conn, schema, name):
                                logger.info("    Tabela %s.%s já existe, removendo para recriar...", schema, name)
                                self._drop_table(target_conn, schema, name)
                            
                            logger.info("    Criando tabela %s.%s...", schema, name)
                            # Log uma amostra do DDL para debug (primeiras 200 caracteres)
                            ddl_preview = ddl_str[:200].replace("\n", " ").strip()
                            logger.debug("    DDL preview: %s...", ddl_preview)
                        
                        execute_non_query(target_conn, ddl_str)
                        logger.info("    ✓ %s.%s criado/aplicado", schema, name)
                        total_objects += 1
                    except cx_Oracle.DatabaseError as exc:
                        error, = exc.args
                        if error.code in (955, 2264, 1430):
                            if object_type == "TABLE":
                                # Se a tabela ainda existe após tentar criar, tentar dropar e recriar
                                logger.warning("    ⚠ Tabela %s.%s já existe, tentando remover para recriar...", schema, name)
                                if self._drop_table(target_conn, schema, name):
                                    # Tentar criar novamente após remover
                                    try:
                                        execute_non_query(target_conn, ddl_str)
                                        logger.info("    ✓ %s.%s recriado com sucesso", schema, name)
                                        total_objects += 1
                                    except Exception as e3:
                                        logger.error("    ✗ Erro ao recriar %s.%s após DROP: %s", schema, name, e3)
                                        logger.warning("    Continuando com próximo objeto...")
                                else:
                                    logger.error("    ✗ Não foi possível remover tabela %s.%s para recriar", schema, name)
                            else:
                                logger.warning("    ⚠ %s.%s já existe, ignorando", schema, name)
                                total_objects += 1
                        elif error.code in (911, 900, 6550):  # ORA-00911, ORA-00900, ORA-06550: invalid SQL/character/end-of-file
                            logger.warning("    ⚠ %s.%s: DDL contém problemas (código %s), tentando alternativa...", schema, name, error.code)
                            # Para packages, tentar obter DDL de ALL_SOURCE
                            if object_type in ("PACKAGE", "PACKAGE_BODY") and error.code in (900, 6550):
                                try:
                                    logger.info("    Tentando obter DDL completo de ALL_SOURCE...")
                                    ddl_str = self._get_package_ddl_from_source(source_conn, schema, name, object_type)
                                    execute_non_query(target_conn, ddl_str)
                                    logger.info("    ✓ %s.%s criado/aplicado (via ALL_SOURCE)", schema, name)
                                    total_objects += 1
                                    continue
                                except Exception as e_source:
                                    logger.warning("    Falha ao obter de ALL_SOURCE: %s", e_source)
                            
                            # Tentar executar statement por statement após limpeza
                            try:
                                from .db_utils import clean_ddl
                                statements = clean_ddl(ddl_str)
                                with target_conn.cursor() as cur:
                                    for stmt in statements:
                                        if stmt.strip():
                                            cur.execute(stmt)
                                target_conn.commit()
                                logger.info("    ✓ %s.%s criado/aplicado (após limpeza)", schema, name)
                                total_objects += 1
                            except Exception as e2:
                                logger.error("    ✗ Erro ao criar %s.%s após limpeza: %s", schema, name, e2)
                                # Continuar com próximo objeto ao invés de falhar completamente
                                logger.warning("    Continuando com próximo objeto...")
                        else:
                            logger.error("    ✗ Erro ao criar %s.%s: %s (código %s)", schema, name, error.message, error.code)
                            # Continuar com próximo objeto ao invés de falhar completamente
                            logger.warning("    Continuando com próximo objeto...")
            else:
                logger.info("    Nenhum objeto do tipo %s encontrado", object_type)
        
        logger.info("✓ Etapa 1/2 concluída: %d objeto(s) DDL processado(s)", total_objects)

    def _copy_data(self, source_conn: cx_Oracle.Connection, target_conn: cx_Oracle.Connection, schema: str) -> None:
        logger.info(">>> Etapa 2/2: Copiando dados das tabelas")
        tables = self._list_tables(source_conn, schema)
        total_tables = len(tables)
        logger.info("Encontradas %d tabela(s) no schema %s", total_tables, schema)
        logger.info("")
        
        if not tables:
            logger.info("Nenhuma tabela encontrada para copiar")
            return
        
        total_rows_copied = 0
        tables_missing = []
        for idx, table in enumerate(tables, 1):
            logger.info("  [%d/%d] Processando tabela: %s.%s", idx, total_tables, schema, table)
            
            # Verificar se a tabela existe no destino antes de tentar copiar dados
            if not self._table_exists(target_conn, schema, table):
                logger.error("    ✗ Tabela %s.%s NÃO EXISTE no destino!", schema, table)
                logger.error("    A tabela precisa ser criada na etapa de DDL antes de copiar dados.")
                tables_missing.append(f"{schema}.{table}")
                continue
            
            try:
                self._truncate_target_table(target_conn, schema, table)
                rows, columns = self._fetch_rows(source_conn, schema, table)
                row_count = len(rows)
                if row_count > 0:
                    logger.info("    Lendo %d linha(s) da origem...", row_count)
                    self._insert_rows(target_conn, schema, table, columns, rows)
                    logger.info("    ✓ %d linha(s) copiada(s) com sucesso", row_count)
                    total_rows_copied += row_count
                else:
                    logger.info("    ✓ Tabela vazia (0 linhas)")
            except Exception as e:
                logger.error("    ✗ Erro ao processar tabela %s.%s: %s", schema, table, e)
                # Continuar com próxima tabela ao invés de parar tudo
                logger.warning("    Continuando com próxima tabela...")
        
        if tables_missing:
            logger.error("")
            logger.error("=" * 70)
            logger.error("ATENÇÃO: %d TABELA(S) NÃO FORAM CRIADAS NO DESTINO", len(tables_missing))
            logger.error("=" * 70)
            for table in tables_missing:
                logger.error("  - %s", table)
            logger.error("")
            logger.error("Essas tabelas precisam ser criadas manualmente ou o DDL precisa ser executado novamente.")
            logger.error("")
        
        logger.info("")
        logger.info("✓ Etapa 2/2 concluída: %d tabela(s) processada(s), %d linha(s) copiada(s) no total", 
                   total_tables, total_rows_copied)

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
            return

        placeholders = ", ".join([f":{idx+1}" for idx in range(len(columns))])
        insert_sql = f'INSERT INTO {schema}.{table} ({", ".join(columns)}) VALUES ({placeholders})'

        total_batches = (len(rows) + self.batch_size - 1) // self.batch_size
        with connection.cursor() as cursor:
            for batch_idx, batch in enumerate(chunked(rows, self.batch_size), 1):
                cursor.executemany(insert_sql, batch)
                if total_batches > 1:
                    logger.info("      Inserindo lote %d/%d (%d linhas)...", batch_idx, total_batches, len(batch))
            connection.commit()
            if total_batches > 1:
                logger.info("      ✓ Commit realizado")

    @staticmethod
    def _table_exists(connection: cx_Oracle.Connection, schema: str, table: str) -> bool:
        """Verifica se uma tabela existe no banco de destino"""
        cursor = connection.cursor()
        try:
            cursor.execute(
                """
                SELECT COUNT(*)
                FROM all_tables
                WHERE owner = :owner AND table_name = :table_name
                """,
                owner=schema.upper(),
                table_name=table.upper(),
            )
            count, = cursor.fetchone()
            return int(count) > 0
        except Exception:
            return False
        finally:
            cursor.close()

    @staticmethod
    def _drop_table(connection: cx_Oracle.Connection, schema: str, table: str) -> bool:
        """
        Remove (DROP) uma tabela se ela existir.
        Retorna True se a tabela foi removida, False se não existia.
        """
        if not OracleExporter._table_exists(connection, schema, table):
            return False
        
        sql = f'DROP TABLE {schema}.{table} CASCADE CONSTRAINTS'
        try:
            execute_non_query(connection, sql)
            logger.info("    Tabela %s.%s removida (DROP)", schema, table)
            return True
        except cx_Oracle.DatabaseError as exc:
            error, = exc.args
            logger.warning("    ⚠ Erro ao remover tabela %s.%s: %s (código %s)", schema, table, error.message, error.code)
            # Tentar sem CASCADE CONSTRAINTS
            try:
                sql = f'DROP TABLE {schema}.{table}'
                execute_non_query(connection, sql)
                logger.info("    Tabela %s.%s removida (DROP sem CASCADE)", schema, table)
                return True
            except Exception as e2:
                logger.error("    ✗ Não foi possível remover tabela %s.%s: %s", schema, table, e2)
                return False

    @staticmethod
    def _get_package_ddl_from_source(connection: cx_Oracle.Connection, schema: str, package_name: str, object_type: str) -> str:
        """
        Obtém o DDL de um package ou package body a partir de ALL_SOURCE.
        Útil quando DBMS_METADATA retorna DDL truncado ou inválido.
        """
        cursor = connection.cursor()
        try:
            # Determinar o tipo correto para ALL_SOURCE
            if object_type == "PACKAGE_BODY":
                type_filter = "PACKAGE BODY"
            else:
                type_filter = "PACKAGE"
            
            cursor.execute(
                """
                SELECT text
                FROM all_source
                WHERE owner = :owner
                  AND name = :name
                  AND type = :type
                ORDER BY line
                """,
                owner=schema.upper(),
                name=package_name.upper(),
                type=type_filter,
            )
            
            lines = [row[0] for row in cursor]
            ddl = "".join(lines)
            
            if not ddl or len(ddl.strip()) < 10:
                raise ValueError(f"DDL obtido de ALL_SOURCE está vazio ou muito curto para {schema}.{package_name}")
            
            return ddl
        finally:
            cursor.close()

    @staticmethod
    def _truncate_target_table(connection: cx_Oracle.Connection, schema: str, table: str) -> None:
        # Verificar se a tabela existe antes de tentar truncar
        if not OracleExporter._table_exists(connection, schema, table):
            logger.error("    ✗ ERRO: Tabela %s.%s não existe no destino! Não é possível copiar dados.", schema, table)
            raise ValueError(f"Tabela {schema}.{table} não existe no destino. Execute a cópia de DDL primeiro.")
        
        sql = f"TRUNCATE TABLE {schema}.{table}"
        try:
            execute_non_query(connection, sql)
            logger.info("    Tabela truncada no destino")
        except cx_Oracle.DatabaseError as exc:
            error, = exc.args
            if error.code == 942:
                logger.error("    ✗ Tabela %s.%s não encontrada no destino", schema, table)
                raise
            else:
                raise

