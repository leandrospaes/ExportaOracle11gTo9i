from __future__ import annotations

import os
import logging
import subprocess
from contextlib import contextmanager
from typing import Any, Dict, Iterable, Iterator, Sequence

import cx_Oracle
 
from .config import OracleConfig

logger = logging.getLogger(__name__)

# Cache de client paths j├í configurados para evitar reconfigura├º├úo
_configured_client_paths: set[str] = set()


def _configure_oracle_client(client_path: str | None) -> None:
    """
    Configura o Oracle Client com o caminho especificado.
    Evita reconfigurar o mesmo path m├║ltiplas vezes.
    
    Para cx_Oracle 8.0+: usa init_oracle_client()
    Para cx_Oracle 5.x: adiciona ao PATH do processo (se poss├¡vel)
    """
    if not client_path:
        return
    
    # Se j├í foi configurado, n├úo precisa fazer novamente
    if client_path in _configured_client_paths:
        return
    
    try:
        # init_oracle_client est├í dispon├¡vel no cx_Oracle 8.0+
        if hasattr(cx_Oracle, "init_oracle_client"):
            cx_Oracle.init_oracle_client(lib_dir=client_path)
            logger.info("Oracle Client configurado (cx_Oracle 8.0+): %s", client_path)
            _configured_client_paths.add(client_path)
        else:
            # Para cx_Oracle 5.x, o client precisa estar no PATH do sistema
            # Tentamos adicionar ao PATH do processo atual
            import sys
            if sys.platform == 'win32':
                # No Windows, adiciona ao PATH do processo
                current_path = os.environ.get('PATH', '')
                if client_path not in current_path:
                    os.environ['PATH'] = f"{client_path};{current_path}"
                    logger.info("Oracle Client path adicionado ao PATH do processo (cx_Oracle 5.x): %s", client_path)
                else:
                    logger.info("Oracle Client path j├í est├í no PATH: %s", client_path)
            else:
                # Linux/Unix
                current_path = os.environ.get('PATH', '')
                if client_path not in current_path:
                    os.environ['PATH'] = f"{client_path}:{current_path}"
                    logger.info("Oracle Client path adicionado ao PATH do processo (cx_Oracle 5.x): %s", client_path)
                else:
                    logger.info("Oracle Client path j├í est├í no PATH: %s", client_path)
            
            # Tamb├®m tenta configurar ORACLE_HOME se n├úo estiver definido
            if not os.environ.get('ORACLE_HOME'):
                os.environ['ORACLE_HOME'] = client_path
                logger.info("ORACLE_HOME configurado: %s", client_path)
            
            _configured_client_paths.add(client_path)
    except Exception as e:
        logger.warning("Falha ao configurar Oracle Client (%s): %s", client_path, e)


@contextmanager
def oracle_connection(config: OracleConfig) -> Iterator[cx_Oracle.Connection]:
    # Configurar o Oracle Client espec├¡fico para esta conex├úo, se especificado
    if config.client_path:
        _configure_oracle_client(config.client_path)
    
    try:
        connection = cx_Oracle.connect(
            user=config.user,
            password=config.password,
            dsn=config.dsn,
            encoding="UTF-8",
        )
    except cx_Oracle.DatabaseError as e:
        error, = e.args
        if error.code == 1047:  # DPI-1047: Cannot locate Oracle Client library
            logger.error(
                "Oracle Client n├úo encontrado. Configure uma das op├º├Áes:\n"
                "1. Instale o Oracle Instant Client e adicione ao PATH do sistema\n"
                "2. Defina a vari├ível de ambiente ORACLE_CLIENT_PATH com o caminho do Instant Client\n"
                "   Exemplo: set ORACLE_CLIENT_PATH=C:\\oracle\\instantclient_11_2"
            )
        elif error.code == 3134:  # ORA-03134: Connections to this server version are no longer supported
            logger.error("")
            logger.error("=" * 70)
            logger.error("ERRO: Vers├úo do Oracle Client incompat├¡vel!")
            logger.error("=" * 70)
            logger.error("")
            logger.error("O banco de destino (Oracle 9i) requer Oracle Instant Client 11.2 ou anterior.")
            logger.error("")
            logger.error("DSN que falhou: %s", config.dsn)
            logger.error("Usu├írio: %s", config.user)
            if config.client_path:
                logger.error("Oracle Client Path configurado: %s", config.client_path)
                logger.error("ÔÜá Este caminho pode n├úo conter o Oracle Client 11.2 correto")
            else:
                logger.error("ÔÜá ORACLE_9I_CLIENT_PATH N├âO EST├ü CONFIGURADO!")
            logger.error("")
            logger.error("SOLU├ç├âO:")
            logger.error("")
            logger.error("1. Baixe e instale o Oracle Instant Client 11.2:")
            logger.error("   https://www.oracle.com/database/technologies/instant-client/winx64-64-downloads.html")
            logger.error("   Procure por: 'Instant Client for Microsoft Windows x64 (64-bit)' vers├úo 11.2")
            logger.error("")
            logger.error("2. Extraia para um diret├│rio (ex: C:\\oracle\\instantclient_11_2)")
            logger.error("")
            logger.error("3. Configure no arquivo .env:")
            logger.error("   ORACLE_9I_CLIENT_PATH=C:\\oracle\\instantclient_11_2")
            logger.error("")
            logger.error("4. Reinicie o terminal/IDE ap├│s configurar")
            logger.error("")
            logger.error("=" * 70)
        elif error.code == 1017:  # ORA-01017: invalid username/password
            logger.error("Credenciais inv├ílidas para %s@%s", config.user, config.dsn)
        elif error.code == 12541:  # ORA-12541: TNS:no listener
            logger.error("N├úo foi poss├¡vel conectar ao banco %s. Verifique se o servidor est├í acess├¡vel.", config.dsn)
        else:
            logger.error("Erro ao conectar ao banco %s: %s (c├│digo %s)", config.dsn, error.message, error.code)
        raise
    except Exception as e:
        logger.error("Erro inesperado ao conectar ao banco %s: %s", config.dsn, e)
        raise
    
    try:
        yield connection
    finally:
        connection.close()


def execute_query(connection: cx_Oracle.Connection, sql: str, params: Sequence[Any] | None = None) -> list[Dict[str, Any]]:
    with connection.cursor() as cursor:
        cursor.execute(sql, params or [])
        columns = [col[0] for col in cursor.description]
        return [dict(zip(columns, row)) for row in cursor]


def clean_ddl(ddl: str) -> list[str]:
    """
    Limpa e divide o DDL em statements execut├íveis.
    Remove caracteres problem├íticos e divide por ponto e v├¡rgula.
    """
    if not ddl:
        return []
    
    # Se for um objeto LOB, ler o conte├║do
    if hasattr(ddl, "read"):
        ddl = ddl.read()
    
    # Converter para string se necess├írio
    ddl = str(ddl)
    
    # Remover caracteres de controle e BOM
    ddl = ddl.replace("\ufeff", "").replace("\u200b", "").replace("\r\n", "\n").replace("\r", "\n")
    
    # Remover caracteres n├úo-ASCII problem├íticos (manter apenas ASCII b├ísico e alguns especiais)
    # Mas preservar strings literais
    lines = ddl.split("\n")
    cleaned_lines = []
    for line in lines:
        # Remover caracteres de controle exceto tab e newline
        cleaned_line = "".join(c if (32 <= ord(c) <= 126) or c in ("\t", "\n") else " " for c in line)
        cleaned_lines.append(cleaned_line)
    ddl = "\n".join(cleaned_lines)
    
    # Dividir por ponto e v├¡rgula (mas manter dentro de strings)
    statements = []
    current_statement = ""
    in_string = False
    string_char = None
    escape_next = False
    
    i = 0
    while i < len(ddl):
        char = ddl[i]
        
        if escape_next:
            current_statement += char
            escape_next = False
            i += 1
            continue
        
        if char == "\\":
            escape_next = True
            current_statement += char
            i += 1
            continue
        
        if char in ("'", '"'):
            if not in_string:
                in_string = True
                string_char = char
            elif char == string_char:
                in_string = False
                string_char = None
            current_statement += char
        elif not in_string and char == ";":
            stmt = current_statement.strip()
            if stmt and not stmt.isspace():
                statements.append(stmt)
            current_statement = ""
        else:
            current_statement += char
        
        i += 1
    
    # Adicionar ├║ltimo statement se n├úo terminou com ponto e v├¡rgula
    if current_statement.strip():
        statements.append(current_statement.strip())
    
    # Limpar cada statement
    cleaned_statements = []
    for stmt in statements:
        # Remover ponto e v├¡rgula no final e espa├ºos extras
        stmt = stmt.rstrip(";").strip()
        # Remover caracteres de controle restantes
        stmt = "".join(c for c in stmt if ord(c) >= 32 or c in ("\n", "\t"))
        if stmt:
            cleaned_statements.append(stmt)
    
    return cleaned_statements if cleaned_statements else [ddl.strip().rstrip(";")]


def execute_non_query(connection: cx_Oracle.Connection, sql: str, params: Sequence[Any] | None = None) -> None:
    """
    Executa SQL sem retorno. Se o SQL contiver m├║ltiplos statements (separados por ;),
    executa cada um separadamente.
    """
    if params:
        # Se h├í par├ómetros, executar normalmente
        with connection.cursor() as cursor:
            cursor.execute(sql, params)
        connection.commit()
    else:
        # Se n├úo h├í par├ómetros, pode ser DDL - limpar e executar
        statements = clean_ddl(sql)
        with connection.cursor() as cursor:
            for stmt in statements:
                if stmt.strip():
                    try:
                        cursor.execute(stmt)
                    except cx_Oracle.DatabaseError as e:
                        error, = e.args
                        # Se for erro de sintaxe, tentar executar como est├í (pode ser necess├írio ponto e v├¡rgula)
                        if error.code == 911:  # ORA-00911: invalid character
                            # Tentar executar com ponto e v├¡rgula
                            if not stmt.rstrip().endswith(";"):
                                stmt = stmt + ";"
                            cursor.execute(stmt)
                        else:
                            raise
        connection.commit()


def chunked(iterable: Iterable[Any], size: int) -> Iterator[list[Any]]:
    bucket: list[Any] = []
    for item in iterable:
        bucket.append(item)
        if len(bucket) == size:
            yield bucket
            bucket = []
    if bucket:
        yield bucket


def test_connection_sqlplus(config: OracleConfig, label: str = "Banco") -> dict[str, Any]:
    """
    Testa conex├úo com Oracle 9i usando SQL*Plus nativo como fallback.
    Útil quando cx-Oracle falha com ORA-03134.
    
    Args:
        config: Configura├º├úo do banco Oracle
        label: R├│tulo para identificar o banco nos logs
        
    Returns:
        Dicion├írio com informa├º├Áes da conex├úo e status
    """
    result = {
        "success": False,
        "label": label,
        "dsn": config.dsn,
        "user": config.user,
        "error": None,
        "database_info": {},
    }
    
    # Procura pelo SQL*Plus em locais comuns
    sqlplus_paths = [
        r"C:\ORAWIN95\bin\SQLPLUS.EXE",
        r"C:\Oracle\bin\SQLPLUS.EXE",
        r"C:\Oracle\product\11.2.0\client_1\bin\SQLPLUS.EXE",
        r"C:\Oracle\product\10.2.0\client_1\bin\SQLPLUS.EXE",
    ]
    
    sqlplus_exe = None
    for path in sqlplus_paths:
        if os.path.exists(path):
            sqlplus_exe = path
            break
    
    if not sqlplus_exe:
        result["error"] = {
            "code": None,
            "message": "SQL*Plus n├úo encontrado. Instale Oracle Client com SQL*Plus.",
        }
        logger.error("  ✗ SQL*Plus n├úo encontrado nos caminhos comuns")
        return result
    
    logger.info("  SQL*Plus encontrado: %s", sqlplus_exe)
    
    # Prepara conex├úo em formato SQL*Plus: user/password@dsn
    connect_string = f"{config.user}/{config.password}@{config.dsn}"
    
    # Script SQL simples para teste
    sql_commands = """SET HEADING OFF FEEDBACK OFF PAGESIZE 0 LINESIZE 32767
SELECT * FROM v$version WHERE ROWNUM = 1;
SELECT name FROM v$database;
SELECT SYSDATE FROM DUAL;
SELECT USER FROM DUAL;
EXIT;
"""
    
    try:
        logger.info("Testando conex├úo com %s usando SQL*Plus...", label)
        logger.info("  DSN: %s", config.dsn)
        logger.info("  Usu├írio: %s", config.user)
        
        # Executa SQL*Plus com input
        proc = subprocess.run(
            [sqlplus_exe, "-s", connect_string],
            input=sql_commands,
            capture_output=True,
            text=True,
            timeout=30,
        )
        
        output = proc.stdout.strip()
        
        if proc.returncode != 0:
            result["error"] = {
                "code": None,
                "message": proc.stderr or "SQL*Plus retornou erro",
            }
            
            if "ORA-01017" in proc.stderr:
                logger.error("  ✗ Credenciais inv├ílidas")
            elif "ORA-12541" in proc.stderr:
                logger.error("  ✗ Listener n├úo encontrado")
            elif "TNS" in proc.stderr:
                logger.error("  ✗ Erro de conex├úo TNS")
            else:
                logger.error("  ✗ Erro SQL*Plus: %s", proc.stderr[:200])
            
            return result
        
        if not output or "ORA-" in output:
            result["error"] = {
                "code": None,
                "message": output or "SQL*Plus retornou vazio",
            }
            logger.error("  ✗ Erro na execu├º├úo: %s", output[:200])
            return result
        
        # Parse dos resultados (simplificado)
        lines = output.split('\n')
        result["database_info"] = {
            "version": lines[0] if len(lines) > 0 else "Desconhecida",
            "database_name": lines[1] if len(lines) > 1 else "Desconhecido",
            "server_date": lines[2] if len(lines) > 2 else "Desconhecido",
            "current_user": lines[3] if len(lines) > 3 else "Desconhecido",
        }
        
        result["success"] = True
        
        logger.info("  ✓ Conex├úo estabelecida com sucesso via SQL*Plus!")
        logger.info("  Vers├úo do Oracle: %s", result["database_info"]["version"][:50])
        logger.info("  Nome do banco: %s", result["database_info"]["database_name"])
        logger.info("  Usu├írio conectado: %s", result["database_info"]["current_user"])
        
    except subprocess.TimeoutExpired:
        result["error"] = {
            "code": None,
            "message": "SQL*Plus timeout (30s)",
        }
        logger.error("  ✗ SQL*Plus timeout")
    except Exception as e:
        result["error"] = {
            "code": None,
            "message": str(e),
        }
        logger.error("  ✗ Erro inesperado: %s", e)
    
    return result

def test_connection(config: OracleConfig, label: str = "Banco") -> dict[str, Any]:
    """
    Testa a conex├úo com um banco Oracle e retorna informa├º├Áes sobre a conex├úo.
    Para Oracle 9i, tenta usar SQL*Plus nativo como fallback.
    
    Args:
        config: Configura├º├úo do banco Oracle
        label: R├│tulo para identificar o banco nos logs
        
    Returns:
        Dicion├írio com informa├º├Áes da conex├úo e status
    """
    result = {
        "success": False,
        "label": label,
        "dsn": config.dsn,
        "user": config.user,
        "error": None,
        "database_info": {},
    }
    
    # Configurar o Oracle Client espec├¡fico para este teste, se especificado
    if config.client_path:
        _configure_oracle_client(config.client_path)
        logger.info("  Oracle Client Path: %s", config.client_path)
    
    try:
        logger.info("Testando conex├úo com %s...", label)
        logger.info("  DSN: %s", config.dsn)
        logger.info("  Usu├írio: %s", config.user)
        
        connection = cx_Oracle.connect(
            user=config.user,
            password=config.password,
            dsn=config.dsn,
            encoding="UTF-8",
        )
        
        try:
            with connection.cursor() as cursor:
                # Informa├º├Áes b├ísicas do banco
                cursor.execute("SELECT * FROM v$version WHERE banner LIKE 'Oracle%'")
                version_row = cursor.fetchone()
                version = version_row[0] if version_row else "Desconhecida"
                
                cursor.execute("SELECT instance_name, host_name, status FROM v$instance")
                instance_info = cursor.fetchone()
                
                cursor.execute("SELECT name FROM v$database")
                db_name_row = cursor.fetchone()
                db_name = db_name_row[0] if db_name_row else "Desconhecido"
                
                # Teste de query simples
                cursor.execute("SELECT SYSDATE FROM DUAL")
                sysdate = cursor.fetchone()[0]
                
                # Informa├º├Áes do usu├írio atual
                cursor.execute("SELECT USER FROM DUAL")
                current_user = cursor.fetchone()[0]
                
                result["database_info"] = {
                    "version": version,
                    "database_name": db_name,
                    "instance_name": instance_info[0] if instance_info else "Desconhecido",
                    "host_name": instance_info[1] if instance_info else "Desconhecido",
                    "status": instance_info[2] if instance_info else "Desconhecido",
                    "current_user": current_user,
                    "server_date": str(sysdate),
                }
                
                result["success"] = True
                
                logger.info("  ✓ Conex├úo estabelecida com sucesso!")
                logger.info("  Vers├úo do Oracle: %s", version)
                logger.info("  Nome do banco: %s", db_name)
                logger.info("  Inst├óncia: %s", instance_info[0] if instance_info else "N/A")
                logger.info("  Host: %s", instance_info[1] if instance_info else "N/A")
                logger.info("  Status: %s", instance_info[2] if instance_info else "N/A")
                logger.info("  Usu├írio conectado: %s", current_user)
                logger.info("  Data do servidor: %s", sysdate)
                
        finally:
            connection.close()
            logger.info("  ✓ Conex├úo fechada")
            
    except cx_Oracle.DatabaseError as e:
        error, = e.args
        result["error"] = {
            "code": error.code,
            "message": error.message,
        }
        
        if error.code == 1047:  # DPI-1047: Cannot locate Oracle Client library
            logger.error("  ✗ Oracle Client n├úo encontrado")
            logger.error("     Configure ORACLE_CLIENT_PATH ou adicione ao PATH")
        elif error.code == 1017:  # ORA-01017: invalid username/password
            logger.error("  ✗ Credenciais inv├ílidas")
        elif error.code == 12541:  # ORA-12541: TNS:no listener
            logger.error("  ✗ Listener n├úo encontrado - servidor pode estar inacess├¡vel")
        elif error.code == 12514:  # ORA-12514: TNS:listener does not currently know of service
            logger.error("  ✗ Servi├ºo n├úo conhecido pelo listener")
        elif error.code == 3134:  # ORA-03134: Connections to this server version are no longer supported
            logger.error("  ✗ Vers├úo do Oracle Client incompat├¡vel - tentando SQL*Plus nativo...")
            # Tentar usar SQL*Plus para 9i
            return test_connection_sqlplus(config, label)
        else:
            logger.error("  ✗ Erro de conex├úo: %s (c├│digo %s)", error.message, error.code)
            
    except Exception as e:
        result["error"] = {
            "code": None,
            "message": str(e),
        }
        logger.error("  ✗ Erro inesperado: %s", e)
    
    return result

