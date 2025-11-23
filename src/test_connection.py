"""
Script de teste de conexão Oracle 9i
Usando Oracle Client do Forms 4.5 (C:\ORAWIN95)
VERSÃO COM LIMPEZA FORÇADA DO PATH
"""
import os
import sys

print("=" * 70)
print("CONFIGURAÇÃO FORÇADA - ORACLE FORMS 4.5 (ORAWIN95)")
print("=" * 70)
print()

# ============================================================================
# PASSO 1: LIMPAR PATH DE OUTROS ORACLES
# ============================================================================
print("1. Limpando PATH de outros Oracle Clients...")
print("-" * 70)

original_path = os.environ.get('PATH', '')
path_parts = original_path.split(os.pathsep)

cleaned_paths = []
removed_paths = []

for path in path_parts:
    path_lower = path.lower()
    # Remover QUALQUER coisa com 'oracle' ou 'instant'
    # EXCETO se for ORAWIN95
    if any(keyword in path_lower for keyword in ['oracle', 'instant', 'ora']):
        if 'orawin95' in path_lower:
            cleaned_paths.append(path)
            print(f"  ✓ Mantido: {path}")
        else:
            removed_paths.append(path)
            print(f"  ✗ Removido: {path}")
    else:
        cleaned_paths.append(path)

if removed_paths:
    print()
    print(f"⚠️ Removidos {len(removed_paths)} paths Oracle conflitantes")
    print("   Isso resolve o erro ORA-03134!")
else:
    print()
    print("✓ Nenhum Oracle conflitante no PATH")

print()

# ============================================================================
# PASSO 2: CONFIGURAR FORMS 4.5 (ORAWIN95)
# ============================================================================
print("2. Configurando Oracle Forms 4.5...")
print("-" * 70)

oracle_home = r'C:\ORAWIN95'
oracle_bin = r'C:\ORAWIN95\bin'

# Verificar se existe
if not os.path.exists(oracle_bin):
    print(f"✗ ERRO: {oracle_bin} não encontrado!")
    print()
    print("Verifique se o Forms 4.5 está realmente em C:\\ORAWIN95")
    print("Se estiver em outro lugar, ajuste as variáveis no início deste script.")
    sys.exit(1)

print(f"✓ Oracle Home: {oracle_home}")
print(f"✓ Oracle Bin: {oracle_bin}")
print()

# Verificar arquivos críticos
print("Verificando arquivos do Oracle Client:")
critical_files = ['oci.dll', 'sqlnet.dll', 'ifrun45.exe']
all_ok = True

for file in critical_files:
    file_path = os.path.join(oracle_bin, file)
    exists = os.path.exists(file_path)
    status = "✓" if exists else "✗"
    print(f"  {status} {file}")
    if not exists and file != 'ifrun45.exe':
        all_ok = False

# Procurar ora*.dll
ora_dlls = [f for f in os.listdir(oracle_bin) if f.startswith('ora') and f.endswith('.dll')]
if ora_dlls:
    print(f"  ✓ {len(ora_dlls)} arquivos ora*.dll encontrados")
else:
    print(f"  ⚠️ Nenhum ora*.dll encontrado")
    all_ok = False

print()

if not all_ok:
    print("⚠️ AVISO: Alguns arquivos podem estar faltando")
    print("   Mas vamos tentar conectar mesmo assim...")
    print()

# Adicionar ORAWIN95 NO INÍCIO do PATH limpo
new_path = oracle_bin + os.pathsep + os.pathsep.join(cleaned_paths)

# Configurar variáveis de ambiente
os.environ['PATH'] = new_path
os.environ['ORACLE_HOME'] = oracle_home
os.environ['TNS_ADMIN'] = os.path.join(oracle_home, 'network', 'admin')

print("Variáveis de ambiente configuradas:")
print(f"  ORACLE_HOME = {os.environ['ORACLE_HOME']}")
print(f"  TNS_ADMIN = {os.environ['TNS_ADMIN']}")
print(f"  PATH (primeiro) = {oracle_bin}")
print()

# ============================================================================
# PASSO 3: IMPORTAR CX_ORACLE (AGORA SIM!)
# ============================================================================
print("3. Importando cx_Oracle...")
print("-" * 70)

try:
    import cx_Oracle
    print(f"✓ cx_Oracle importado com sucesso!")
    print(f"  Versão: {cx_Oracle.version}")
    
    # Verificar versão do cliente
    try:
        client_version = cx_Oracle.clientversion()
        print(f"  Oracle Client: {'.'.join(map(str, client_version))}")
        
        if client_version[0] <= 11:
            print(f"  ✓ Versão {client_version[0]}.x - COMPATÍVEL com Oracle 9i!")
        else:
            print(f"  ⚠️ Versão {client_version[0]}.x - Pode não funcionar com Oracle 9i")
    except:
        print(f"  Oracle Client: (versão antiga do Forms 4.5 - OK)")
    
    print()
    
except ImportError as e:
    print(f"✗ ERRO: cx_Oracle não instalado!")
    print(f"  {e}")
    print()
    print("Solução:")
    print("  pip install 'cx-Oracle>=6.0,<7.0'")
    sys.exit(1)
    
except Exception as e:
    print(f"✗ ERRO ao importar cx_Oracle: {e}")
    print()
    print("Possíveis causas:")
    print("  1. Faltam DLLs no C:\\ORAWIN95\\bin")
    print("  2. Versão incompatível do cx_Oracle")
    print()
    print("Solução:")
    print("  pip uninstall cx_Oracle")
    print("  pip install 'cx-Oracle>=6.0,<7.0'")
    sys.exit(1)

# ============================================================================
# PASSO 4: CONFIGURAÇÃO DE CONEXÃO
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
print("Configuração:")
print(f"  Usuário: {config['user']}")
print(f"  Senha: {'*' * len(config['password'])}")
print(f"  Host: {config['host']}")
print(f"  Porta: {config['port']}")
print(f"  Service Name: {config['service_name']}")
print()

# ============================================================================
# PASSO 5: TESTE DE CONEXÃO
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
    print("✓✓✓ SUCESSO! CONEXÃO ESTABELECIDA! ✓✓✓")
    print("=" * 70)
    print()
    
    # Executar testes
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
    except:
        print(f"   Database: (não acessível)")
    
    # Teste 3: Usuário
    cursor.execute("SELECT USER FROM DUAL")
    current_user = cursor.fetchone()
    print(f"   Usuário: {current_user[0]}")
    
    # Teste 4: Data/hora
    cursor.execute("SELECT TO_CHAR(SYSDATE, 'DD/MM/YYYY HH24:MI:SS') FROM DUAL")
    server_date = cursor.fetchone()
    print(f"   Data/Hora: {server_date[0]}")
    print()
    
    # Teste 5: Query simples
    print("2. Teste de Query:")
    print("-" * 70)
    cursor.execute("SELECT 'Hello from Oracle 9i via ORAWIN95!' FROM DUAL")
    result = cursor.fetchone()
    print(f"   {result[0]}")
    print("   ✓ Query executada com sucesso!")
    print()
    
    # Teste 6: Tabelas
    print("3. Schema Info:")
    print("-" * 70)
    try:
        cursor.execute("SELECT COUNT(*) FROM user_tables")
        count = cursor.fetchone()
        print(f"   Tabelas: {count[0]}")
        
        if count[0] > 0:
            cursor.execute("""
                SELECT table_name 
                FROM user_tables 
                WHERE ROWNUM <= 5
                ORDER BY table_name
            """)
            tables = cursor.fetchall()
            print(f"   Primeiras 5:")
            for table, in tables:
                print(f"     - {table}")
    except Exception as e:
        print(f"   (Erro: {e})")
    
    print()
    
    # Fechar
    cursor.close()
    connection.close()
    
    print("=" * 70)
    print("✓ Conexão fechada")
    print("=" * 70)
    print()
    print("🎉🎉🎉 PROBLEMA RESOLVIDO! 🎉🎉🎉")
    print()
    print("O Oracle Forms 4.5 (ORAWIN95) está funcionando!")
    print()
    print("━" * 70)
    print("PRÓXIMO PASSO: INTEGRAR COM O PROJETO")
    print("━" * 70)
    print()
    print("Você precisa modificar o arquivo src/db_utils.py do projeto")
    print("para fazer a mesma limpeza do PATH.")
    print()
    print("Adicione este código NO INÍCIO do arquivo src/db_utils.py,")
    print("ANTES de importar cx_Oracle:")
    print()
    print("=" * 70)
    print("# CÓDIGO PARA ADICIONAR EM src/db_utils.py")
    print("=" * 70)
    print('''
import os
import sys

# ============================================================================
# FORÇAR USO DO ORACLE FORMS 4.5 (ORAWIN95)
# ============================================================================
def _force_orawin95_client():
    """
    Remove outros Oracle Clients do PATH e força uso do ORAWIN95
    """
    original_path = os.environ.get('PATH', '')
    path_parts = original_path.split(os.pathsep)
    
    # Limpar PATH
    cleaned_paths = []
    for path in path_parts:
        path_lower = path.lower()
        if any(kw in path_lower for kw in ['oracle', 'instant', 'ora']):
            if 'orawin95' in path_lower:
                cleaned_paths.append(path)
        else:
            cleaned_paths.append(path)
    
    # Adicionar ORAWIN95 no início
    orawin95_bin = r'C:\\ORAWIN95\\bin'
    new_path = orawin95_bin + os.pathsep + os.pathsep.join(cleaned_paths)
    
    os.environ['PATH'] = new_path
    os.environ['ORACLE_HOME'] = r'C:\\ORAWIN95'
    os.environ['TNS_ADMIN'] = r'C:\\ORAWIN95\\network\\admin'

# Executar antes de importar cx_Oracle
_force_orawin95_client()

# Agora sim, importar cx_Oracle
import cx_Oracle
# ... resto do código
''')
    print("=" * 70)
    print()
    print("Depois de adicionar esse código:")
    print()
    print("1. Teste o projeto:")
    print("   python -m src.main test --target")
    print()
    print("2. Se funcionar, copie dados:")
    print("   python -m src.main copy --schemas SEU_SCHEMA")
    print()
    print("3. Valide:")
    print("   python -m src.main validate --schemas SEU_SCHEMA")
    print()
    print("=" * 70)
    
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
    
    if error.code == 3134:
        print("❌ AINDA RECEBENDO ORA-03134!")
        print()
        print("Isso significa que OUTRO Oracle Client ainda está sendo usado.")
        print()
        print("DIAGNÓSTICO AVANÇADO:")
        print()
        print("Execute no CMD:")
        print("  where oci.dll")
        print()
        print("Deve mostrar C:\\ORAWIN95\\bin\\oci.dll PRIMEIRO")
        print()
        print("Se mostrar outro caminho primeiro, tente:")
        print()
        print("SOLUÇÃO EXTREMA - Renomear outros Oracles temporariamente:")
        print("  1. No CMD como Administrador:")
        print("     cd C:\\")
        print("     ren oracle oracle_backup")
        print()
        print("  2. Execute este script novamente")
        print()
        print("  3. Se funcionar, restaure depois:")
        print("     ren oracle_backup oracle")
        
    elif error.code == 1017:
        print("❌ Usuário ou senha incorretos")
        print(f"   Verifique: {config['user']} / {config['password']}")
        
    elif error.code == 12154:
        print("❌ TNS não conseguiu resolver")
        print(f"   Host: {config['host']}")
        print(f"   Service: {config['service_name']}")
        print()
        print("Verifique:")
        print(f"   ping {config['host']}")
        
    elif error.code == 12541:
        print("❌ Listener não encontrado")
        print(f"   telnet {config['host']} {config['port']}")
    
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
