# Solução para Problemas com Python 3.13 e Oracle 9i

## Problema

Ao tentar instalar `cx-Oracle<8.0` no Python 3.13, você pode encontrar erros de compilação como:
```
error LNK2001: símbolo externo não resolvido PyUnicode_GET_SIZE
fatal error LNK1120: 1 externo não resolvidos
```

Isso ocorre porque versões antigas do cx_Oracle não têm wheels pré-compilados para Python 3.13.

## Soluções

### Opção 1: Usar Python 3.11 ou 3.12 (RECOMENDADO)

A melhor solução é usar Python 3.11 ou 3.12, que têm melhor suporte para versões antigas do cx_Oracle:

1. Baixe Python 3.11 ou 3.12 de: https://www.python.org/downloads/
2. Crie um novo ambiente virtual:
   ```
   py -3.11 -m venv .venv
   .venv\Scripts\activate
   pip install -r requirements-9i.txt
   ```

### Opção 2: Instalar versão específica do cx_Oracle

Se você precisa usar Python 3.13, tente instalar uma versão específica do cx_Oracle:

```
pip install cx-Oracle==7.3.0
```

**Nota**: Mesmo assim, pode haver problemas de compatibilidade.

### Opção 3: Usar oracle-instantclient (alternativa moderna)

Se possível, considere usar `oracle-instantclient` que é uma alternativa mais moderna:

```
pip install oracle-instantclient
```

Porém, esta opção pode não funcionar com Oracle 9i devido ao erro ORA-03134.

## Recomendação Final

**Use Python 3.11 ou 3.12** para garantir compatibilidade total com Oracle 9i e evitar problemas de compilação.



