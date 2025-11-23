"""
Script auxiliar para verificar a versão do Python e compatibilidade com Oracle 9i
"""
import sys
import io

# Configurar encoding UTF-8 para Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

def check_python_version():
    version = sys.version_info
    major, minor = version.major, version.minor
    
    print("=" * 70)
    print("VERIFICAÇÃO DE COMPATIBILIDADE - ORACLE 9i")
    print("=" * 70)
    print()
    print(f"Versão do Python detectada: {major}.{minor}.{version.micro}")
    print()
    
    if major == 3 and minor in (11, 12):
        print("[OK] Python 3.11 ou 3.12 - COMPATIVEL com Oracle 9i")
        print()
        print("Você pode instalar as dependências normalmente:")
        print("  pip install -r requirements-9i.txt")
        print()
        return True
    elif major == 3 and minor == 13:
        print("[AVISO] Python 3.13 - PODE TER PROBLEMAS com Oracle 9i")
        print()
        print("PROBLEMA:")
        print("  Versões antigas do cx_Oracle (< 8.0) não têm wheels")
        print("  pré-compilados para Python 3.13 e podem falhar na compilação.")
        print()
        print("SOLUÇÕES:")
        print("  1. RECOMENDADO: Use Python 3.11 ou 3.12")
        print("     Baixe de: https://www.python.org/downloads/")
        print()
        print("  2. Tente instalar versão específica:")
        print("     pip install cx-Oracle==7.3.0")
        print()
        print("  3. Consulte SOLUCAO_PYTHON_313.md para mais detalhes")
        print()
        return False
    elif major == 3 and minor >= 11:
        print("[OK] Python 3.11+ - COMPATIVEL")
        print()
        print("Você pode instalar as dependências normalmente:")
        print("  pip install -r requirements-9i.txt")
        print()
        return True
    else:
        print("[AVISO] Versao do Python nao testada")
        print()
        print("Recomendado: Use Python 3.11 ou 3.12")
        print()
        return False

if __name__ == "__main__":
    check_python_version()


