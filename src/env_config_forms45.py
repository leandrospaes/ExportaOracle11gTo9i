"""
Script para configurar o arquivo .env com Oracle Forms 4.5
"""
import os

env_content = """# ============================================================================
# CONFIGURAÇÃO ORACLE - USANDO FORMS 4.5
# ============================================================================

# Oracle 11g (fonte) - se você tiver
ORACLE_11G_DSN=host11g:1521/ORCL11G
ORACLE_11G_USER=usuario_origem
ORACLE_11G_PASSWORD=senha_origem
ORACLE_11G_CLIENT_PATH=C:\\oracle\\instantclient_19_3

# Oracle 9i (destino) - USANDO FORMS 4.5
ORACLE_9I_DSN=ora9i_2:1521/MIGRAT
ORACLE_9I_USER=SINDU
ORACLE_9I_PASSWORD=RELAT
ORACLE_9I_CLIENT_PATH=C:\\Oracle45\\bin

# Configurações globais do Forms 4.5
ORACLE_HOME=C:\\Oracle45
TNS_ADMIN=C:\\Oracle45\\network\\admin

# ============================================================================
# OBSERVAÇÕES:
# ============================================================================
# - ORACLE_9I_CLIENT_PATH aponta para o bin do Forms 4.5
# - Essa configuração é compatível com Oracle 9i
# - Não precisa baixar Oracle Instant Client adicional
# - O Forms 4.5 já tem tudo que você precisa
# ============================================================================
"""

print("=" * 70)
print("CONFIGURAÇÃO DO ARQUIVO .ENV")
print("=" * 70)
print()

env_file = '.env'

# Verificar se já existe
if os.path.exists(env_file):
    print(f"⚠️  Arquivo .env JÁ EXISTE!")
    print()
    print("Opções:")
    print("  1. Fazer backup e criar novo")
    print("  2. Cancelar")
    print()
    
    choice = input("Escolha (1 ou 2): ").strip()
    
    if choice == '1':
        # Fazer backup
        backup_file = '.env.backup'
        counter = 1
        while os.path.exists(backup_file):
            backup_file = f'.env.backup.{counter}'
            counter += 1
        
        os.rename(env_file, backup_file)
        print(f"✓ Backup criado: {backup_file}")
        print()
    else:
        print("Operação cancelada.")
        print()
        print("Você pode editar manualmente o .env com estas configurações:")
        print()
        print(env_content)
        exit(0)

# Criar novo arquivo
with open(env_file, 'w', encoding='utf-8') as f:
    f.write(env_content)

print(f"✓ Arquivo .env criado com sucesso!")
print()
print("Configurações aplicadas:")
print("  - Oracle 9i DSN: ora9i_2:1521/MIGRAT")
print("  - Usuário: SINDU")
print("  - Senha: RELAT")
print("  - Client Path: C:\\Oracle45\\bin")
print()
print("━" * 70)
print("PRÓXIMOS PASSOS:")
print("━" * 70)
print()
print("1. Ajuste as credenciais se necessário:")
print("   - Edite o arquivo .env")
print("   - Altere ORACLE_9I_USER e ORACLE_9I_PASSWORD")
print()
print("2. Teste a conexão:")
print("   python test_connection.py")
print()
print("3. Se funcionar, teste o projeto:")
print("   python -m src.main test --target")
print()
print("━" * 70)
