"""
Script de teste de conexão Oracle 9i
Usando Oracle Client do Forms 4.5 (C:\ORAWIN95\bin)
"""
import os
import sys

# ============================================================================
# CONFIGURAÇÃO: Oracle Client do Forms 4.5
# ============================================================================
oracle_client_path = r'C:\ORAWIN95\bin'  # ✓ Seu Forms 4.5
oracle_home = r'C:\ORAWIN95'

print("=" * 70)
print("CONFIGURAÇÃO DO ORACLE CLIENT")
print("=" * 70)
print(f"Oracle Home: {oracle_home}")
print(f"Oracle Client Path: {oracle_client_path}")
print()

# Configurar variáveis de ambiente ANTES de importar cx_Oracle
os.environ['ORACLE_HOME'] = oracle_home
os.environ['TNS_ADMIN'] = os.path.join(oracle_home, 'network', 'admin')

# Adicionar ao PATH
if oracle_client_path not in os.environ.get('PATH', ''):
    os.environ['PATH'] = oracle_client_path + os.pathsep + os.environ.get('PATH', '')

print("Variáveis de ambiente configuradas:")
print(f"  ORACLE_HOME = {os.environ.get('ORACLE_HOME')}")
print(f"  TNS_ADMIN = {os.environ.get('TNS_ADMIN')}")
print(f"  PATH (Oracle) = {oracle_client_path}")
print()

# Verificar se os arquivos existem
print("Verificando arquivos do Oracle Client:")
required_files = ['oci.dll', 'sqlnet.dll', 'ifrun45.exe']
all_ok = True

for file in required_files:
    file_path = os.path.join(oracle_client_path, file)
    exists = os.path.exists(file_path)
    status = "✓" if exists else "✗"
    print(f"  {status} {file}")
    if not exists:
        all_ok = False

# Procurar por ora*.dll
ora_dlls = [f for f in os.listdir(oracle_client_path) if f.startswith('ora') and f.endswith('.dll')]
if ora_dlls:
    print(f"  ✓ {', '.join(ora_dlls[:3])}")  # Mostrar até 3
else:
    print(f"  ✗ Nenhum ora*.dll encontrado")
    all_ok = False

print()

if not all_ok:
    print("⚠️ AVISO: Alguns arquivos não foram encontrados!")
    print("Verifique se o Forms 4.5 está instalado corretamente em C:\\ORAWIN95")
    print()

# ============================================================================
# IMPORTAR CX_ORACLE
# ============================================================================
try:
    import cx_Oracle
    print(f"✓ cx_Oracle importado com sucesso!")
    print(f"  Versão: {cx_Oracle.version}")
    
    # Verificar versão do cliente
    try:
        client_version = cx_Oracle.clientversion()
        print(f"  Oracle Client detectado: {'.'.join(map(str, client_version))}")
    except:
        print(f"  Oracle Client: (versão antiga do Forms 4.5)")
    print()
    
except ImportError as e:
    print(f"✗ ERRO: cx_Oracle não está instalado!")
    print(f"  {e}")
    print()
    print("Solução:")
    print("  pip install 'cx-Oracle>=6.0,<7.0'")
    print()
    sys.exit(1)
    
except Exception as e:
    print(f"✗ ERRO ao carregar cx_Oracle: {e}")
    print()
    print("Possíveis causas:")
    print("  1. Faltam DLLs no diretório C:\\ORAWIN95\\bin")
    print("  2. Versão incompatível do cx_Oracle")
    print()
    print("Soluções:")
    print("  1. Verifique se o Forms 4.5 está funcionando")
    print("  2. Reinstale cx_Oracle 6.x: pip install 'cx-Oracle>=6.0,<7.0'")
    print()
    sys.exit(1)

# ============================================================================
# CONFIGURAÇÃO DE CONEXÃO
# ============================================================================
config = {
    'user': 'SINDU',
    'password': 'RELAT',
    'host': 'ora9i_2',
    'port': 1521,
    'service_name': 'MIGRAT'
}

print("=" * 70)
print("TESTE DE CONEXÃO ORACLE 9i")
print("=" * 70)
print()
print("Configuração da conexão:")
print(f"  Usuário: {config['user']}")
print(f"  Senha: {'*' * len(config['password'])}")
print(f"  Host: {config['host']}")
print(f"  Porta: {config['port']}")
print(f"  Service Name: {config['service_name']}")
print()

# ============================================================================
# TESTE DE CONEXÃO
# ============================================================================
try:
    # Construir DSN
    print("Construindo DSN...")
    dsn = cx_Oracle.makedsn(
        config['host'],
        config['port'],
        service_name=config['service_name']
    )
    print(f"DSN: {dsn}")
    print()
    
    print("Conectando ao Oracle 9i...")
    connection = cx_Oracle.connect(
        user=config['user'],
        password=config['password'],
        dsn=dsn
    )
    
    print()
    print("=" * 70)
    print("✓✓✓ CONEXÃO ESTABELECIDA COM SUCESSO! ✓✓✓")
    print("=" * 70)
    print()
    
    # Obter informações do servidor
    cursor = connection.cursor()
    
    # Teste 1: Versão do Oracle
    print("1. Informações do Servidor:")
    print("-" * 70)
    try:
        cursor.execute("SELECT banner FROM v$version WHERE ROWNUM = 1")
        version = cursor.fetchone()
        print(f"   Oracle: {version[0]}")
    except:
        print(f"   Oracle: {connection.version}")
    
    # Teste 2: Nome do banco
    try:
        cursor.execute("SELECT name FROM v$database")
        db_name = cursor.fetchone()
        print(f"   Database: {db_name[0]}")
    except Exception as e:
        print(f"   Database: (não acessível)")
    
    # Teste 3: Usuário conectado
    cursor.execute("SELECT USER FROM DUAL")
    current_user = cursor.fetchone()
    print(f"   Usuário conectado: {current_user[0]}")
    
    # Teste 4: Data/hora do servidor
    cursor.execute("SELECT TO_CHAR(SYSDATE, 'DD/MM/YYYY HH24:MI:SS') FROM DUAL")
    server_date = cursor.fetchone()
    print(f"   Data/Hora servidor: {server_date[0]}")
    print()
    
    # Teste 5: Query simples
    print("2. Teste de Query:")
    print("-" * 70)
    cursor.execute("SELECT 'Hello from Oracle 9i via Forms 4.5!' AS message FROM DUAL")
    result = cursor.fetchone()
    print(f"   Resultado: {result[0]}")
    print("   ✓ Query executada com sucesso!")
    print()
    
    # Teste 6: Listar tabelas do schema
    print("3. Tabelas do Schema:")
    print("-" * 70)
    try:
        cursor.execute("SELECT COUNT(*) FROM user_tables")
        table_count = cursor.fetchone()
        print(f"   Total de tabelas: {table_count[0]}")
        
        if table_count[0] > 0:
            cursor.execute("""
                SELECT table_name 
                FROM user_tables 
                WHERE ROWNUM <= 10
                ORDER BY table_name
            """)
            tables = cursor.fetchall()
            print(f"   Primeiras {len(tables)} tabelas:")
            for idx, (table,) in enumerate(tables, 1):
                print(f"     {idx:2d}. {table}")
        else:
            print("   (Nenhuma tabela encontrada no schema)")
    except Exception as e:
        print(f"   (Erro ao listar tabelas: {e})")
    print()
    
    # Teste 7: Contar views
    print("4. Objects do Schema:")
    print("-" * 70)
    try:
        cursor.execute("""
            SELECT object_type, COUNT(*) as total
            FROM user_objects
            GROUP BY object_type
            ORDER BY COUNT(*) DESC
        """)
        objects = cursor.fetchall()
        for obj_type, count in objects:
            print(f"   {obj_type:20s}: {count:4d}")
    except Exception as e:
        print(f"   (Erro ao contar objetos: {e})")
    print()
    
    # Fechar recursos
    cursor.close()
    connection.close()
    
    print("=" * 70)
    print("✓ Conexão fechada com sucesso")
    print("=" * 70)
    print()
    print("🎉 TUDO FUNCIONANDO PERFEITAMENTE!")
    print()
    print("✅ Oracle Forms 4.5 Client está funcionando corretamente")
    print("✅ Conexão com Oracle 9i estabelecida")
    print("✅ Queries executadas com sucesso")
    print()
    print("━" * 70)
    print("PRÓXIMOS PASSOS:")
    print("━" * 70)
    print()
    print("1. Testar conexão com o projeto principal:")
    print("   python -m src.main test --target")
    print()
    print("2. Copiar dados de um schema:")
    print("   python -m src.main copy --schemas SEU_SCHEMA")
    print()
    print("3. Validar a cópia:")
    print("   python -m src.main validate --schemas SEU_SCHEMA")
    print()
    print("━" * 70)
    
except cx_Oracle.DatabaseError as e:
    error, = e.args
    print()
    print("=" * 70)
    print("✗✗✗ ERRO DE CONEXÃO ✗✗✗")
    print("=" * 70)
    print()
    print(f"Mensagem: {error.message}")
    print(f"Código: ORA-{error.code:05d}")
    print()
    
    # Diagnóstico por código de erro
    if error.code == 3134:
        print("❌ DIAGNÓSTICO: Oracle Client ainda muito moderno")
        print()
        print("Isso é estranho, pois você está usando Forms 4.5...")
        print()
        print("POSSÍVEIS CAUSAS:")
        print("  1. cx_Oracle está usando outro Oracle Client do PATH")
        print("  2. Existe outro Oracle instalado (11g, 12c, 19c)")
        print()
        print("SOLUÇÃO:")
        print("  1. Verifique outras instalações Oracle:")
        print("     dir C:\\oracle /s /b | findstr oci.dll")
        print()
        print("  2. Garanta que C:\\ORAWIN95\\bin está no início do PATH")
        print()
        print("  3. Tente remover outros Oracles do PATH temporariamente")
        
    elif error.code == 1017:
        print("❌ DIAGNÓSTICO: Usuário ou senha incorretos")
        print()
        print("SOLUÇÃO:")
        print("  1. Verifique as credenciais (linhas 91-96 deste script)")
        print("  2. Teste com o Forms 4.5 se consegue conectar")
        print("  3. Verifique se o usuário SINDU existe no banco 9i")
        print()
        print("  Teste manual:")
        print(f"    sqlplus {config['user']}/{config['password']}@{config['host']}:{config['port']}/{config['service_name']}")
        
    elif error.code == 12154:
        print("❌ DIAGNÓSTICO: TNS não conseguiu resolver o identificador")
        print()
        print("SOLUÇÃO:")
        print("  1. Verifique o arquivo tnsnames.ora:")
        print("     C:\\ORAWIN95\\network\\admin\\tnsnames.ora")
        print()
        print("  2. Ou verifique se o host está acessível:")
        print(f"     ping {config['host']}")
        print()
        print("  3. Teste a porta:")
        print(f"     telnet {config['host']} {config['port']}")
        
    elif error.code == 12541:
        print("❌ DIAGNÓSTICO: Listener não encontrado")
        print()
        print("SOLUÇÃO:")
        print("  1. Verifique se o Oracle 9i está rodando no servidor")
        print("  2. Verifique se o listener está ativo")
        print("  3. Teste conectividade:")
        print(f"     telnet {config['host']} {config['port']}")
        
    elif error.code == 12170 or error.code == 12535:
        print("❌ DIAGNÓSTICO: Timeout de conexão")
        print()
        print("SOLUÇÃO:")
        print("  1. Verifique firewall")
        print("  2. Verifique conectividade:")
        print(f"     ping {config['host']}")
        print("  3. Verifique se está em VPN/proxy")
        
    else:
        print("Consulte a documentação Oracle:")
        print(f"  https://docs.oracle.com/error-help/db/ora-{error.code:05d}/")
    
    print()
    sys.exit(1)

except Exception as e:
    print()
    print("=" * 70)
    print("✗✗✗ ERRO INESPERADO ✗✗✗")
    print("=" * 70)
    print()
    print(f"Tipo: {type(e).__name__}")
    print(f"Mensagem: {e}")
    print()
    print("Stack trace completo:")
    import traceback
    traceback.print_exc()
    print()
    sys.exit(1)
