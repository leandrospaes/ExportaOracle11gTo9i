Exporta Banco Oracle 11g para 9i (Node.js / TypeScript)
======================================================

Projeto utilitário em TypeScript/Node.js para copiar dados e objetos de um banco Oracle 11g para um banco Oracle 9i. Inclui rotinas de validação pós-cópia para garantir que tabelas, sinônimos, grants, views, triggers, procedures e funções foram replicados corretamente.

Pré-requisitos
--------------
- Node.js (recomenda-se uma versão LTS compatível com suas dependências, ex: 18.x ou 20.x)
- Oracle Instant Client 64-bit (versão 11.2 ou inferior recomendada para compatibilidade com 9i).
- Variáveis de ambiente ou arquivo `.env` com as credenciais dos bancos.

Instalação e execução rápida
---------------------------
```powershell
# instalar dependências (oracledb é opcional e pode ser instalado separadamente quando o Instant Client estiver pronto)
npm install

# executar em modo desenvolvimento (usa ts-node)
npm run dev -- test
```

Configuração
------------
Crie um arquivo `.env` com as variáveis do projeto (exemplos abaixo):
```
ORACLE_11G_DSN=svdesenv:1521/leandro
ORACLE_11G_USER=SINDU
ORACLE_11G_PASSWORD=relat

ORACLE_9I_DSN=ora9i_2:1521/MIGRAT
ORACLE_9I_USER=SINDU
ORACLE_9I_PASSWORD=RELAT

# Paths opcionais do Instant Client
ORACLE_11G_CLIENT_PATH=C:\oracle\instantclient_19_3
ORACLE_9I_CLIENT_PATH=C:\oracle\instantclient_11_2
```

Notas importantes
-----------------
- `oracledb` está listado como `optionalDependencies` para evitar falha total no `npm install` quando o Instant Client não estiver presente; instale `oracledb` separadamente depois de preparar o Instant Client.
- Para conectar ao Oracle 9i é recomendado usar Instant Client 11.2 (ou anterior). Versões modernas do client podem causar `ORA-03134`.

Arquivos principais
------------------
- `src/config.ts` - carrega variáveis de ambiente e monta `OracleConfig`.
- `src/db_utils.ts` - inicializa o Oracle Client (quando possível), abre conexões e fornece helpers `executeQuery`, `executeNonQuery`, `cleanDDL`, `testConnection`.
- `src/exporter.ts` - lógica de exportação (esqueleto, completar para paridade total).
- `src/validator.ts` - validações pós-import (esqueleto).
- `src/main.ts` - CLI com comandos `test`, `copy`, `validate`.

Próximos passos
---------------
- Implementar a lógica completa de exportação em `src/exporter.ts` e de validação em `src/validator.ts`.
- Rodar `npm install` e, se necessário, instalar `oracledb` depois de configurar o Instant Client.
