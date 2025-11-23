from __future__ import annotations

import os
import logging
from contextlib import contextmanager
from typing import Any, Dict, Iterable, Iterator, Sequence

import cx_Oracle
 
from .config import OracleConfig

logger = logging.getLogger(__name__)

# Cache de client paths já configurados para evitar reconfiguração
_configured_client_paths: set[str] = set()


def _configure_oracle_client(client_path: str | None) -> None:
    """
    Configura o Oracle Client com o caminho especificado.
    Evita reconfigurar o mesmo path múltiplas vezes.
    
    Para cx_Oracle 8.0+: usa init_oracle_client()
    Para cx_Oracle 5.x: adiciona ao PATH do processo (se possível)
    """
    if not client_path:
        return
    
    # Se já foi configurado, não precisa fazer novamente
    if client_path in _configured_client_paths:
        return
    
    try:
        # init_oracle_client está disponível no cx_Oracle 8.0+
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
                    logger.info("Oracle Client path já está no PATH: %s", client_path)
            else:
                # Linux/Unix
                current_path = os.environ.get('PATH', '')
                if client_path not in current_path:
                    os.environ['PATH'] = f"{client_path}:{current_path}"
                    logger.info("Oracle Client path adicionado ao PATH do processo (cx_Oracle 5.x): %s", client_path)
                else:
                    logger.info("Oracle Client path já está no PATH: %s", client_path)
            
            # Também tenta configurar ORACLE_HOME se não estiver definido
            if not os.environ.get('ORACLE_HOME'):
                os.environ['ORACLE_HOME'] = client_path
                logger.info("ORACLE_HOME configurado: %s", client_path)
            
            _configured_client_paths.add(client_path)
    except Exception as e:
        logger.warning("Falha ao configurar Oracle Client (%s): %s", client_path, e)


@contextmanager
def oracle_connection(config: OracleConfig) -> Iterator[cx_Oracle.Connection]:
    # Configurar o Oracle Client específico para esta conexão, se especificado
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
                "Oracle Client não encontrado. Configure uma das opções:\n"
                "1. Instale o Oracle Instant Client e adicione ao PATH do sistema\n"
                "2. Defina a variável de ambiente ORACLE_CLIENT_PATH com o caminho do Instant Client\n"
                "   Exemplo: set ORACLE_CLIENT_PATH=C:\\oracle\\instantclient_11_2"
            )
        elif error.code == 3134:  # ORA-03134: Connections to this server version are no longer supported
            logger.error("")
            logger.error("=" * 70)
            logger.error("ERRO: Versão do Oracle Client incompatível!")
            logger.error("=" * 70)
            logger.error("")
            logger.error("O banco de destino (Oracle 9i) requer Oracle Instant Client 11.2 ou anterior.")
            logger.error("")
            logger.error("DSN que falhou: %s", config.dsn)
            logger.error("Usuário: %s", config.user)
            if config.client_path:
                logger.error("Oracle Client Path configurado: %s", config.client_path)
                logger.error("⚠ Este caminho pode não conter o Oracle Client 11.2 correto")
            else:
                logger.error("⚠ ORACLE_9I_CLIENT_PATH NÃO ESTÁ CONFIGURADO!")
            logger.error("")
            logger.error("SOLUÇÃO:")
            logger.error("")
            logger.error("1. Baixe e instale o Oracle Instant Client 11.2:")
            logger.error("   https://www.oracle.com/database/technologies/instant-client/winx64-64-downloads.html")
            logger.error("   Procure por: 'Instant Client for Microsoft Windows x64 (64-bit)' versão 11.2")
            logger.error("")
            logger.error("2. Extraia para um diretório (ex: C:\\oracle\\instantclient_11_2)")
            logger.error("")
            logger.error("3. Configure no arquivo .env:")
            logger.error("   ORACLE_9I_CLIENT_PATH=C:\\oracle\\instantclient_11_2")
            logger.error("")
            logger.error("4. Reinicie o terminal/IDE após configurar")
            logger.error("")
            logger.error("=" * 70)
        elif error.code == 1017:  # ORA-01017: invalid username/password
            logger.error("Credenciais inválidas para %s@%s", config.user, config.dsn)
        elif error.code == 12541:  # ORA-12541: TNS:no listener
            logger.error("Não foi possível conectar ao banco %s. Verifique se o servidor está acessível.", config.dsn)
        else:
            logger.error("Erro ao conectar ao banco %s: %s (código %s)", config.dsn, error.message, error.code)
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
    Limpa e divide o DDL em statements executáveis.
    Remove caracteres problemáticos e divide por ponto e vírgula.
    """
    if not ddl:
        return []
    
    # Se for um objeto LOB, ler o conteúdo
    if hasattr(ddl, "read"):
        ddl = ddl.read()
    
    # Converter para string se necessário
    ddl = str(ddl)
    
    # Remover caracteres de controle e BOM
    ddl = ddl.replace("\ufeff", "").replace("\u200b", "").replace("\r\n", "\n").replace("\r", "\n")
    
    # Remover caracteres não-ASCII problemáticos (manter apenas ASCII básico e alguns especiais)
    # Mas preservar strings literais
    lines = ddl.split("\n")
    cleaned_lines = []
    for line in lines:
        # Remover caracteres de controle exceto tab e newline
        cleaned_line = "".join(c if (32 <= ord(c) <= 126) or c in ("\t", "\n") else " " for c in line)
        cleaned_lines.append(cleaned_line)
    ddl = "\n".join(cleaned_lines)
    
    # Dividir por ponto e vírgula (mas manter dentro de strings)
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
    
    # Adicionar último statement se não terminou com ponto e vírgula
    if current_statement.strip():
        statements.append(current_statement.strip())
    
    # Limpar cada statement
    cleaned_statements = []
    for stmt in statements:
        # Remover ponto e vírgula no final e espaços extras
        stmt = stmt.rstrip(";").strip()
        # Remover caracteres de controle restantes
        stmt = "".join(c for c in stmt if ord(c) >= 32 or c in ("\n", "\t"))
        if stmt:
            cleaned_statements.append(stmt)
    
    return cleaned_statements if cleaned_statements else [ddl.strip().rstrip(";")]


def execute_non_query(connection: cx_Oracle.Connection, sql: str, params: Sequence[Any] | None = None) -> None:
    """
    Executa SQL sem retorno. Se o SQL contiver múltiplos statements (separados por ;),
    executa cada um separadamente.
    """
    if params:
        # Se há parâmetros, executar normalmente
        with connection.cursor() as cursor:
            cursor.execute(sql, params)
        connection.commit()
    else:
        # Se não há parâmetros, pode ser DDL - limpar e executar
        statements = clean_ddl(sql)
        with connection.cursor() as cursor:
            for stmt in statements:
                if stmt.strip():
                    try:
                        cursor.execute(stmt)
                    except cx_Oracle.DatabaseError as e:
                        error, = e.args
                        # Se for erro de sintaxe, tentar executar como está (pode ser necessário ponto e vírgula)
                        if error.code == 911:  # ORA-00911: invalid character
                            # Tentar executar com ponto e vírgula
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


def test_connection(config: OracleConfig, label: str = "Banco") -> dict[str, Any]:
    """
    Testa a conexão com um banco Oracle e retorna informações sobre a conexão.
    
    Args:
        config: Configuração do banco Oracle
        label: Rótulo para identificar o banco nos logs
        
    Returns:
        Dicionário com informações da conexão e status
    """
    result = {
        "success": False,
        "label": label,
        "dsn": config.dsn,
        "user": config.user,
        "error": None,
        "database_info": {},
    }
    
    # Configurar o Oracle Client específico para este teste, se especificado
    if config.client_path:
        _configure_oracle_client(config.client_path)
        logger.info("  Oracle Client Path: %s", config.client_path)
    
    try:
        logger.info("Testando conexão com %s...", label)
        logger.info("  DSN: %s", config.dsn)
        logger.info("  Usuário: %s", config.user)
        
        connection = cx_Oracle.connect(
            user=config.user,
            password=config.password,
            dsn=config.dsn,
            encoding="UTF-8",
        )
        
        try:
            with connection.cursor() as cursor:
                # Informações básicas do banco
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
                
                # Informações do usuário atual
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
                
                logger.info("  ✓ Conexão estabelecida com sucesso!")
                logger.info("  Versão do Oracle: %s", version)
                logger.info("  Nome do banco: %s", db_name)
                logger.info("  Instância: %s", instance_info[0] if instance_info else "N/A")
                logger.info("  Host: %s", instance_info[1] if instance_info else "N/A")
                logger.info("  Status: %s", instance_info[2] if instance_info else "N/A")
                logger.info("  Usuário conectado: %s", current_user)
                logger.info("  Data do servidor: %s", sysdate)
                
        finally:
            connection.close()
            logger.info("  ✓ Conexão fechada")
            
    except cx_Oracle.DatabaseError as e:
        error, = e.args
        result["error"] = {
            "code": error.code,
            "message": error.message,
        }
        
        if error.code == 1047:  # DPI-1047: Cannot locate Oracle Client library
            logger.error("  ✗ Oracle Client não encontrado")
            logger.error("     Configure ORACLE_CLIENT_PATH ou adicione ao PATH")
        elif error.code == 1017:  # ORA-01017: invalid username/password
            logger.error("  ✗ Credenciais inválidas")
        elif error.code == 12541:  # ORA-12541: TNS:no listener
            logger.error("  ✗ Listener não encontrado - servidor pode estar inacessível")
        elif error.code == 12514:  # ORA-12514: TNS:listener does not currently know of service
            logger.error("  ✗ Serviço não conhecido pelo listener")
        elif error.code == 3134:  # ORA-03134: Connections to this server version are no longer supported
            logger.error("  ✗ Versão do Oracle Client incompatível com Oracle 9i")
            logger.error("")
            logger.error("  SOLUÇÃO:")
            logger.error("  1. Instale Oracle Instant Client 11.2 (ou anterior)")
            logger.error("  2. Configure ORACLE_CLIENT_PATH ou adicione ao PATH")
            logger.error("  3. Use cx_Oracle < 8.0: pip install 'cx_Oracle<8.0'")
            logger.error("  4. Reinicie o terminal após configurar")
        else:
            logger.error("  ✗ Erro de conexão: %s (código %s)", error.message, error.code)
            
    except Exception as e:
        result["error"] = {
            "code": None,
            "message": str(e),
        }
        logger.error("  ✗ Erro inesperado: %s", e)
    
    return result

