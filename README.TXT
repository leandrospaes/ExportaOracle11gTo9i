Exporta Banco Oracle 11g para 9i
================================

Projeto utilitário em Python para copiar dados e objetos de um banco Oracle 11g para um banco Oracle 9i, preservando tabelas, dados e metadados essenciais. Inclui rotinas de validação pós-cópia para garantir que tabelas, sinônimos, grants, views, triggers, procedures e funções foram replicados corretamente.

Pré-requisitos
--------------
- Python 3.11+ com acesso ao Oracle Client compatível com Oracle 9i.
- Variáveis de ambiente ou arquivo `.env` com as credenciais dos bancos.
- Permissões de leitura completa no schema 11g e de criação/grant no schema alvo 9i.

Instalação
----------
```
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

Configuração
------------
Utilize variáveis de ambiente ou um arquivo `.env` na raiz contendo:
```
ORACLE_11G_DSN=host11g:1521/ORCL11G
ORACLE_11G_USER=usuario_origem
ORACLE_11G_PASSWORD=senha_origem

ORACLE_9I_DSN=host9i:1521/ORCL9I
ORACLE_9I_USER=usuario_destino
ORACLE_9I_PASSWORD=senha_destino
```

Como usar
---------
Copiar dados e objetos do 11g para o 9i:
```
python -m src.main copy --schemas SCHEMA_A,SCHEMA_B
```

Validar a importação comparando metadados e contagens:
```
python -m src.main validate --schemas SCHEMA_A,SCHEMA_B
```

Estrutura do projeto
--------------------
- `src/config.py`: gestão de credenciais e parâmetros.
- `src/db_utils.py`: conexões, execução segura e utilidades.
- `src/exporter.py`: lógica de exportação/cópia.
- `src/validator.py`: checagens pós-importação.
- `src/main.py`: CLI com comandos `copy` e `validate`.

Limitações e cuidados
---------------------
- Para Oracle 9i é obrigatório utilizar o Oracle Client 11.2 (ou inferior) em modo thick.
- Objetos dependentes de funcionalidades exclusivas do 11g devem ser revisados manualmente.
- Recomenda-se rodar o processo em janela de manutenção, com backup prévio do 9i.

Licença
-------
Uso interno; adapte conforme a política da sua organização.

