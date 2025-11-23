"""
Script para verificar configuração do ambiente Oracle 9i
Verifica Python, cx_Oracle e Oracle Client
"""
import sys
import os
import platform

print("=" * 70)
print("VERIFICAÇÃO DE AMBIENTE - ORACLE 9i")
print("=" * 70)
print()

# 1. Verificar Python
print("1. PYTHON")
print("-" * 70)
print(f"   Versão: {sys.version}")
print(f"   Executável: {sys.executable}")
print(f"   Arquitetura: {platform.architecture()[0]}")

python_version = sys.version_info
if python_version.major == 3 and python_version.minor in [11, 12]:
    print("   Status: ✓ Versão compatível com Oracle 9i")
elif python_version.major == 3 and python_version.minor == 13:
    print("   Status: ⚠️ Python 3.13 pode ter problemas com cx_Oracle 6.x")
    print("   Recomendação: Use Python 3.11 ou 3.12")
else:
    print(f"   Status: ⚠️ Versão não testada para Oracle 9i")
print()

# 2. Verificar cx_Oracle
print("2. CX_ORACLE")
print("-" * 70)
try:
    import cx_Oracle
    print(f"   Status: ✓ Instalado")
    print(f"   Versão: {cx_Oracle.version}")
    
    version_parts = cx_Oracle.version.split('.')
    major_version = int(version_parts[0])
    
    if major_version == 6:
        print("   Compatibilidade: ✓ Versão 6.x - COMPATÍVEL com Oracle 9i")
    elif major_version == 5:
        print("   Compatibilidade: ✓ Versão 5.x - COMPATÍVEL com Oracle 9i")
    elif major_version >= 7:
        print("   Compatibilidade: ✗ Versão 7.x+ - NÃO recomendada para Oracle 9i")
        print("   Recomendação: pip install 'cx-Oracle>=6.0,<7.0'")
    else:
        print(f"   Compatibilidade: ⚠️ Versão {major_version}.x - não testada")
    
    # Verificar se consegue obter versão do cliente
    try:
        client_version = cx_Oracle.clientversion()
        print(f"   Oracle Client detectado: {'.'.join(map(str, client_version))}")
        
        if client_version[0] == 11 and client_version[1] == 2:
            print("   Oracle Client: ✓ Versão 11.2 - COMPATÍVEL com Oracle 9i")
        elif client_version[0] <= 11:
            print("   Oracle Client: ✓ Versão antiga - provavelmente compatível")
        else:
            print(f"   Oracle Client: ✗ Versão {client_version[0]}.{client_version[1]} - muito moderna para Oracle 9i")
            print("   Recomendação: Use Oracle Client 11.2 ou anterior")
    except Exception as e:
        print(f"   Oracle Client: ✗ Não detectado ({e})")
        print("   Recomendação: Configure ORACLE_9I_CLIENT_PATH ou PATH")
    
except ImportError:
    print("   Status: ✗ NÃO instalado")
    print("   Solução: pip install 'cx-Oracle>=6.0,<7.0'")
except Exception as e:
    print(f"   Status: ✗ Erro ao importar: {e}")
print()

# 3. Verificar variáveis de ambiente
print("3. VARIÁVEIS DE AMBIENTE")
print("-" * 70)

env_vars = [
    'ORACLE_9I_CLIENT_PATH',
    'ORACLE_CLIENT_PATH',
    'ORACLE_HOME',
    'PATH',
    'LD_LIBRARY_PATH'  # Linux
]

for var in env_vars:
    value = os.environ.get(var)
    if value:
        if var == 'PATH':
            # Mostrar apenas paths relacionados a Oracle
            oracle_paths = [p for p in value.split(os.pathsep) if 'oracle' in p.lower() or 'instant' in p.lower()]
            if oracle_paths:
                print(f"   {var} (Oracle paths):")
                for path in oracle_paths:
                    print(f"     - {path}")
            else:
                print(f"   {var}: (nenhum path Oracle encontrado)")
        else:
            print(f"   {var}: {value}")
    else:
        if var in ['ORACLE_9I_CLIENT_PATH', 'ORACLE_CLIENT_PATH']:
            print(f"   {var}: ✗ NÃO configurada")
        else:
            print(f"   {var}: (não configurada)")
print()

# 4. Procurar por Oracle Instant Client
print("4. ORACLE INSTANT CLIENT")
print("-" * 70)

possible_locations = []

if platform.system() == 'Windows':
    possible_locations = [
        r'C:\oracle\instantclient_11_2',
        r'C:\oracle\instantclient_12_2',
        r'C:\oracle\instantclient_19_3',
        r'C:\oracle\instantclient_21_1',
        r'D:\oracle\instantclient_11_2',
        r'D:\oracle\instantclient_12_2',
        r'D:\oracle\instantclient_19_3',
        r'D:\oracle\instantclient_21_1',
    ]
else:  # Linux/Mac
    possible_locations = [
        '/opt/oracle/instantclient_11_2',
        '/opt/oracle/instantclient_12_2',
        '/opt/oracle/instantclient_19_3',
        '/opt/oracle/instantclient_21_1',
        '/usr/lib/oracle/11.2/client64',
        '/usr/lib/oracle/12.2/client64',
        '/usr/lib/oracle/19.3/client64',
        os.path.expanduser('~/oracle/instantclient_11_2'),
        os.path.expanduser('~/oracle/instantclient_12_2'),
    ]

found_clients = []
for location in possible_locations:
    if os.path.exists(location):
        found_clients.append(location)
        
        # Verificar arquivos importantes
        if platform.system() == 'Windows':
            required_files = ['oci.dll', 'oraociei11.dll']
        else:
            required_files = ['libclntsh.so', 'libnnz11.so']
        
        files_found = []
        for file in required_files:
            file_path = os.path.join(location, file)
            if os.path.exists(file_path):
                files_found.append(file)
        
        version = location.split('_')[-1] if '_' in location else 'desconhecida'
        status = "✓ Completo" if len(files_found) == len(required_files) else "⚠️ Incompleto"
        
        print(f"   Encontrado: {location}")
        print(f"     Versão: {version}")
        print(f"     Status: {status}")
        print(f"     Arquivos: {', '.join(files_found) if files_found else 'nenhum arquivo crítico encontrado'}")
        print()

if not found_clients:
    print("   ✗ Nenhum Oracle Instant Client encontrado nas localizações comuns")
    print()
    print("   Recomendação:")
    print("   1. Baixe Oracle Instant Client 11.2:")
    print("      https://www.oracle.com/database/technologies/instant-client/downloads.html")
    if platform.system() == 'Windows':
        print("   2. Extraia para: C:\\oracle\\instantclient_11_2")
    else:
        print("   2. Extraia para: /opt/oracle/instantclient_11_2")
    print()
else:
    # Verificar qual é o mais adequado
    compatible_clients = [c for c in found_clients if '11_2' in c or '11.2' in c]
    if compatible_clients:
        print(f"   ✓ Cliente compatível encontrado: {compatible_clients[0]}")
        print(f"   Recomendação: Configure ORACLE_9I_CLIENT_PATH={compatible_clients[0]}")
    else:
        print("   ⚠️ Nenhum cliente 11.2 encontrado (recomendado para Oracle 9i)")
        if found_clients:
            print(f"   Clientes disponíveis: {', '.join(found_clients)}")
            newer_clients = [c for c in found_clients if any(v in c for v in ['19_', '21_', '12_'])]
            if newer_clients:
                print(f"   ⚠️ Atenção: Clientes modernos ({', '.join(newer_clients)}) podem não funcionar com Oracle 9i")
print()

# 5. Verificar arquivo .env
print("5. ARQUIVO .ENV")
print("-" * 70)

env_file = '.env'
if os.path.exists(env_file):
    print(f"   Status: ✓ Encontrado")
    print(f"   Localização: {os.path.abspath(env_file)}")
    print()
    print("   Conteúdo (credenciais ocultadas):")
    with open(env_file, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                if '=' in line:
                    key, value = line.split('=', 1)
                    if 'PASSWORD' in key.upper():
                        print(f"     {key}=***")
                    else:
                        print(f"     {key}={value}")
else:
    print(f"   Status: ✗ NÃO encontrado")
    print()
    print("   Recomendação: Crie um arquivo .env na raiz do projeto com:")
    print()
    print("   ORACLE_9I_DSN=ora9i_2:1521/MIGRAT")
    print("   ORACLE_9I_USER=SINDU")
    print("   ORACLE_9I_PASSWORD=sua_senha")
    print("   ORACLE_9I_CLIENT_PATH=C:\\oracle\\instantclient_11_2")
print()

# 6. Resumo e recomendações
print("=" * 70)
print("RESUMO E RECOMENDAÇÕES")
print("=" * 70)
print()

issues = []
recommendations = []

# Verificar Python
if python_version.major == 3 and python_version.minor == 13:
    issues.append("Python 3.13 pode ter incompatibilidades")
    recommendations.append("Use Python 3.11 ou 3.12")

# Verificar cx_Oracle
try:
    import cx_Oracle
    version_parts = cx_Oracle.version.split('.')
    major_version = int(version_parts[0])
    if major_version >= 7:
        issues.append(f"cx_Oracle {cx_Oracle.version} não recomendado para Oracle 9i")
        recommendations.append("pip install 'cx-Oracle>=6.0,<7.0'")
except:
    issues.append("cx_Oracle não instalado")
    recommendations.append("pip install 'cx-Oracle>=6.0,<7.0'")

# Verificar Oracle Client
if not found_clients:
    issues.append("Nenhum Oracle Instant Client encontrado")
    recommendations.append("Baixe e instale Oracle Instant Client 11.2")
elif not any('11_2' in c or '11.2' in c for c in found_clients):
    issues.append("Oracle Client 11.2 não encontrado")
    recommendations.append("Instale Oracle Instant Client 11.2 para compatibilidade com Oracle 9i")

# Verificar .env
if not os.path.exists('.env'):
    issues.append("Arquivo .env não encontrado")
    recommendations.append("Crie arquivo .env com credenciais de conexão")

if issues:
    print("⚠️ PROBLEMAS ENCONTRADOS:")
    for i, issue in enumerate(issues, 1):
        print(f"   {i}. {issue}")
    print()
    print("📋 AÇÕES RECOMENDADAS:")
    for i, rec in enumerate(recommendations, 1):
        print(f"   {i}. {rec}")
else:
    print("✓✓✓ AMBIENTE PARECE ESTAR CONFIGURADO CORRETAMENTE!")
    print()
    print("Próximo passo:")
    print("   python test_connection.py")

print()
print("=" * 70)
