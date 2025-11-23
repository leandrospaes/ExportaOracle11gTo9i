Exporta Banco Oracle 11g para 9i
================================

Projeto utilitário em Python para copiar dados e objetos de um banco Oracle 11g para um banco Oracle 9i, preservando tabelas, dados e metadados essenciais. Inclui rotinas de validação pós-cópia para garantir que tabelas, sinônimos, grants, views, triggers, procedures e funções foram replicados corretamente.

Pré-requisitos
--------------
- **Python 3.11 ou 3.12** (recomendado para compatibilidade com Oracle 9i)
  - ⚠️ Python 3.13 pode ter problemas ao instalar versões antigas do cx_Oracle
- Oracle Instant Client 64-bit (versão 11.2 ou inferior recomendada para compatibilidade com 9i).
- Variáveis de ambiente ou arquivo `.env` com as credenciais dos bancos.
- Permissões de leitura completa no schema 11g e de criação/grant no schema alvo 9i.

Instalação
----------
**1. Verifique a compatibilidade do Python (recomendado):**
```
python check_python_version.py
```

**2. Para Oracle 11g e versões mais recentes:**
```
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

**3. Para Oracle 9i (requer versão específica do cx_Oracle):**
```
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements-9i.txt
```

⚠️ **IMPORTANTE - Compatibilidade:**
- **cx_Oracle 5.x** é recomendado para Oracle 9i (melhor compatibilidade)
- Versões antigas do cx_Oracle não têm wheels pré-compilados para Python 3.13
- **Recomendado**: Use Python 3.11 ou 3.12 para melhor compatibilidade com Oracle 9i
- Se estiver usando Python 3.13, pode ser necessário compilar o cx_Oracle a partir do código-fonte

⚠️ **Nota**: Se você precisa conectar tanto ao 11g quanto ao 9i, use `requirements-9i.txt` que é compatível com ambos.

Configuração
------------
Utilize variáveis de ambiente ou um arquivo `.env` na raiz contendo:
```
ORACLE_11G_DSN=host11g:1521/ORCL11G
ORACLE_11G_USER=usuario_origem
ORACLE_11G_PASSWORD=senha_origem
ORACLE_11G_CLIENT_PATH=C:\oracle\instantclient_19_3

ORACLE_9I_DSN=host9i:1521/ORCL9I
ORACLE_9I_USER=usuario_destino
ORACLE_9I_PASSWORD=senha_destino
ORACLE_9I_CLIENT_PATH=C:\oracle\instantclient_11_2
```

**Configuração do Oracle Client:**

⚠️ **IMPORTANTE PARA ORACLE 9i**: O Oracle 9i é muito antigo e requer versões específicas do Oracle Client e do cx_Oracle.

**Paths separados para cada banco (RECOMENDADO):**

O projeto suporta paths separados do Oracle Client para cada banco, permitindo usar versões diferentes:

- `ORACLE_11G_CLIENT_PATH`: Caminho do Oracle Client para o banco 11g (pode ser versão mais recente)
- `ORACLE_9I_CLIENT_PATH`: Caminho do Oracle Client para o banco 9i (deve ser 11.2 ou anterior)
- `ORACLE_CLIENT_PATH`: Path global (usado como fallback se os paths específicos não estiverem definidos)

**Exemplo de configuração:**
```
# Banco 11g pode usar versão mais recente do Client
ORACLE_11G_CLIENT_PATH=C:\oracle\instantclient_19_3

# Banco 9i precisa de versão antiga (11.2 ou anterior)
ORACLE_9I_CLIENT_PATH=C:\oracle\instantclient_11_2
```

**Se você encontrar o erro "ORA-03134: Connections to this server version are no longer supported":**

1. **Instale o Oracle Instant Client 11.2** (ou versão anterior):
   - Baixe de: https://www.oracle.com/database/technologies/instant-client/winx64-64-downloads.html
   - Procure por: "Instant Client for Microsoft Windows x64 (64-bit)" versão 11.2
   - Extraia para um diretório (ex: `C:\oracle\instantclient_11_2`)

2. **Configure o caminho específico para Oracle 9i**:
   ```
   ORACLE_9I_CLIENT_PATH=C:\oracle\instantclient_11_2
   ```

3. **Use cx_Oracle 6.x (compatível com Oracle 9i)**:
   ```
   pip install -r requirements-9i.txt
   ```
   Ou instale diretamente:
   ```
   pip install 'cx-Oracle>=6.0,<7.0'
   ```
   
   **Nota**: cx_Oracle 6.x tem boa compatibilidade com Oracle 9i quando usado com Oracle Client 11.2. 
   Versões 8.0+ podem não suportar Oracle 9i. cx_Oracle 5.x requer Oracle SDK para compilar.

4. **Reinicie o terminal/IDE** após configurar o PATH.

**Se você encontrar o erro "DPI-1047: Cannot locate Oracle Client library":**

Siga os passos acima para instalar e configurar o Oracle Instant Client.

Como usar
---------
**Testar conexões com os bancos (recomendado antes de copiar):**
```
# Testar ambas as conexões (11g e 9i)
python -m src.main test

# Testar apenas conexão com banco 11g (origem)
python -m src.main test --source

# Testar apenas conexão com banco 9i (destino)
python -m src.main test --target
```

**Copiar dados e objetos do 11g para o 9i:**
```
python -m src.main copy --schemas SCHEMA_A,SCHEMA_B
```

**Validar a importação comparando metadados e contagens:**
```
python -m src.main validate --schemas SCHEMA_A,SCHEMA_B
```

Estrutura do projeto
--------------------
- `src/config.py`: gestão de credenciais e parâmetros.
- `src/db_utils.py`: conexões, execução segura e utilidades.
- `src/exporter.py`: lógica de exportação/cópia.
- `src/validator.py`: checagens pós-importação.
- `src/main.py`: CLI com comandos `test`, `copy` e `validate`.

Limitações e cuidados
---------------------
- Para Oracle 9i é obrigatório utilizar o Oracle Client 11.2 (ou inferior) em modo thick.
- Objetos dependentes de funcionalidades exclusivas do 11g devem ser revisados manualmente.
- Recomenda-se rodar o processo em janela de manutenção, com backup prévio do 9i.

Licença
-------
Uso interno; adapte conforme a política da sua organização.

