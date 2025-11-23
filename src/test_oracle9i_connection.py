"""
Script de teste de conexão Oracle 9i
Compatível com cx_Oracle 5.x e 6.x
"""
import os
import sys

# Configurar Oracle Client path ANTES de importar cx_Oracle
oracle_client_path = r'D:\oracle\instantclient_11_2'  # Ajuste este caminho!

# Adicionar ao PATH do sistema (necessário para cx_Oracle 6.x)
if oracle_client_path not in os.environ.get('PATH', ''):
    os.environ['PATH'] = oracle_client_path + os.pathsep + os.environ.get('PATH', '')

# Adicionar LD_LIBRARY_PATH para Linux
if sys.platform.startswith('linux'):
    os.environ['LD_LIBRARY_PATH'] = oracle_client_path + ':' + os.environ.get('LD_LIBRARY_PATH', '')

print(f"Oracle Client Path configurado: {oracle_client_path}")
print(f"PATH: {os.environ['PATH'][:200]}...")
print()

# Agora importar cx_Oracle
try:
    import cx_Oracle
    print(f"✓ cx_Oracle importado com sucesso!")
    print(f"  Versão: {cx_Oracle.version}")
    print(f"  Client Version: {cx_Oracle.clientversion()}")
    print()
except ImportError as e:
    print(f"✗ ERRO ao importar cx_Oracle: {e}")
    print()
    print("Solução:")
    print("  pip install 'cx-Oracle>=6.0,<7.0'")
    sys.exit(1)
except Exception as e:
    print(f"✗ ERRO ao inicializar cx_Oracle: {e}")
    print()
    print("Verifique se o Oracle Instant Client 11.2 está instalado em:")
    print(f"  {oracle_client_path}")
    sys.exit(1)

# Configurações de conexão
# AJUSTE ESTES VALORES COM SUAS CREDENCIAIS!
config = {
    'user': 'SINDU',
    'password': 'sua_senha_aqui',  # ⚠️ ALTERE AQUI!
    'host': 'ora9i_2',
    'port': 1521,
    'service_name': 'MIGRAT'
}

print("=" * 70)
print("TESTE DE CONEXÃO ORACLE 9i")
print("=" * 70)
print()
print("Configuração:")
print(f"  Usuário: {config['user']}")
print(f"  Host: {config['host']}")
print(f"  Porta: {config['port']}")
print(f"  Service: {config['service_name']}")
print()

# Construir DSN
try:
    dsn = cx_Oracle.makedsn(
        config['host'],
        config['port'],
        service_name=config['service_name']
    )
    print(f"DSN construído: {dsn}")
    print()
except Exception as e:
    print(f"✗ Erro ao construir DSN: {e}")
    sys.exit(1)

# Tentar conectar
print("Tentando conectar...")
try:
    connection = cx_Oracle.connect(
        user=config['user'],
        password=config['password'],
        dsn=dsn,
        encoding='UTF-8'
    )
    
    print()
    print("=" * 70)
    print("✓✓✓ CONEXÃO ESTABELECIDA COM SUCESSO! ✓✓✓")
    print("=" * 70)
    print()
    
    # Obter informações do servidor
    print("Informações do Servidor Oracle:")
    cursor = connection.cursor()
    
    # Versão do Oracle
    cursor.execute("SELECT * FROM v$version WHERE banner LIKE 'Oracle%'")
    version = cursor.fetchone()
    if version:
        print(f"  Versão: {version[0]}")
    
    # Nome do banco
    cursor.execute("SELECT name FROM v$database")
    db_name = cursor.fetchone()
    if db_name:
        print(f"  Database: {db_name[0]}")
    
    # Usuário conectado
    cursor.execute("SELECT user FROM dual")
    current_user = cursor.fetchone()
    if current_user:
        print(f"  Usuário conectado: {current_user[0]}")
    
    # Data/hora do servidor
    cursor.execute("SELECT SYSDATE FROM dual")
    server_date = cursor.fetchone()
    if server_date:
        print(f"  Data/Hora servidor: {server_date[0]}")
    
    print()
    
    # Teste de query simples
    print("Teste de Query:")
    cursor.execute("SELECT 'Hello from Oracle 9i!' AS message FROM dual")
    result = cursor.fetchone()
    print(f"  Resultado: {result[0]}")
    print()
    
    # Listar algumas tabelas do schema
    print("Primeiras 10 tabelas do schema:")
    try:
        cursor.execute("""
            SELECT table_name 
            FROM user_tables 
            WHERE ROWNUM <= 10
            ORDER BY table_name
        """)
        tables = cursor.fetchall()
        if tables:
            for idx, (table,) in enumerate(tables, 1):
                print(f"  {idx}. {table}")
        else:
            print("  (Nenhuma tabela encontrada)")
    except Exception as e:
        print(f"  (Não foi possível listar tabelas: {e})")
    
    print()
    
    # Fechar conexão
    cursor.close()
    connection.close()
    
    print("=" * 70)
    print("✓ Conexão fechada com sucesso")
    print("=" * 70)
    print()
    print("🎉 TUDO FUNCIONANDO! Você pode prosseguir com a migração.")
    
except cx_Oracle.DatabaseError as e:
    error, = e.args
    print()
    print("=" * 70)
    print("✗✗✗ ERRO DE CONEXÃO ✗✗✗")
    print("=" * 70)
    print()
    print(f"Erro: {error.message}")
    print(f"Código: ORA-{error.code:05d}")
    print()
    
    # Mensagens de ajuda específicas por erro
    if error.code == 3134:
        print("CAUSA: Oracle Client muito moderno para Oracle 9i")
        print()
        print("SOLUÇÃO:")
        print("  1. Baixe Oracle Instant Client 11.2:")
        print("     https://www.oracle.com/database/technologies/instant-client/winx64-64-downloads.html")
        print()
        print("  2. Extraia para: D:\\oracle\\instantclient_11_2")
        print()
        print("  3. Ajuste a variável 'oracle_client_path' neste script")
        print()
        print("  4. Instale cx_Oracle 6.x:")
        print("     pip install 'cx-Oracle>=6.0,<7.0'")
        
    elif error.code == 1017:
        print("CAUSA: Usuário ou senha incorretos")
        print()
        print("SOLUÇÃO:")
        print("  1. Verifique o usuário e senha no arquivo .env")
        print("  2. Teste login com sqlplus:")
        print(f"     sqlplus {config['user']}/<senha>@{config['host']}:{config['port']}/{config['service_name']}")
        
    elif error.code == 12154:
        print("CAUSA: DSN não encontrado ou incorreto")
        print()
        print("SOLUÇÃO:")
        print("  1. Verifique se o host está correto")
        print("  2. Verifique se o service_name está correto")
        print("  3. Teste conectividade:")
        print(f"     ping {config['host']}")
        print(f"     telnet {config['host']} {config['port']}")
        
    elif error.code == 12541:
        print("CAUSA: Listener Oracle não está rodando")
        print()
        print("SOLUÇÃO:")
        print("  1. Verifique se o listener está ativo no servidor")
        print("  2. Verifique se a porta está correta (padrão: 1521)")
        print("  3. Teste conectividade:")
        print(f"     telnet {config['host']} {config['port']}")
        
    elif error.code == 12170:
        print("CAUSA: Timeout de conexão")
        print()
        print("SOLUÇÃO:")
        print("  1. Verifique firewall/proxy")
        print("  2. Verifique se o servidor está acessível")
        print(f"     ping {config['host']}")
        
    else:
        print("Consulte a documentação Oracle para este código de erro:")
        print(f"  https://docs.oracle.com/error-help/db/ora-{error.code:05d}/")
    
    sys.exit(1)

except Exception as e:
    print()
    print("=" * 70)
    print("✗✗✗ ERRO INESPERADO ✗✗✗")
    print("=" * 70)
    print()
    print(f"Erro: {type(e).__name__}: {e}")
    print()
    import traceback
    traceback.print_exc()
    sys.exit(1)
