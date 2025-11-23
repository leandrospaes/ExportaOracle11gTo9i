## Quick orientation for AI coding agents

This repository is a small Python utility to copy/export data and objects from Oracle 11g to Oracle 9i.
Focus on the files in `src/` and the environment requirements in the repo root (see `requirements-9i.txt` and `README.TXT`).

Key areas (read these first)
- `src/config.py` — canonical source of environment variable names and how `OracleConfig` is built.
- `src/db_utils.py` — connection handling (uses `cx_Oracle`), Oracle Client initialization logic, helper functions (`execute_query`, `execute_non_query`, `clean_ddl`, `test_connection`). Read this file to understand how clients are configured and how errors such as `DPI-1047` and `ORA-03134` are handled.
- `src/exporter.py` — export/copy logic (what gets moved and how DDL/data are produced).
- `src/validator.py` — post-import validation rules and example queries used to compare source vs target.
- `src/main.py` — CLI entrypoint (commands: `test`, `copy`, `validate`). Typical developer commands call `python -m src.main`.

Big picture and important constraints
- The tool talks directly to Oracle databases using `cx_Oracle` (thick client). That means the runtime environment must provide a compatible Oracle Instant Client.
- Oracle 9i requires an older client (recommended Instant Client 11.2 or earlier). Modern clients/drivers may refuse connections and raise `ORA-03134`. The repo already contains detection and user-facing error messages in `src/db_utils.py`.
- The project intentionally supports different Oracle Client paths per-target: `ORACLE_11G_CLIENT_PATH` and `ORACLE_9I_CLIENT_PATH` are documented in `README.TXT`. The code uses `config.client_path` to decide which client to initialize.

Developer workflows and exact commands
- Create a venv and install dependencies (PowerShell example):
```powershell
python -m venv .venv
.venv\Scripts\Activate
pip install -r requirements.txt          # for modern targets
pip install -r requirements-9i.txt       # if you need 9i-compatible cx_Oracle
```
- Test connections (recommended before running any copy):
```powershell
# test both
python -m src.main test
# test only target (9i)
python -m src.main test --target
```
- Copy and validate (examples):
```powershell
python -m src.main copy --schemas SCHEMA_A,SCHEMA_B
python -m src.main validate --schemas SCHEMA_A,SCHEMA_B
```

Project-specific conventions and patterns
- Error handling: `cx_Oracle.DatabaseError` is unwrapped and `error.code` is used heavily (see `src/db_utils.py`). When modifying DB code, preserve or extend this mapping so CLI messages remain meaningful.
- Client init: code calls `cx_Oracle.init_oracle_client(lib_dir=...)` when available, otherwise it alters `PATH`/`ORACLE_HOME` for older `cx_Oracle` versions. If you change client handling, maintain both code paths for cx_Oracle 8+ and older 5.x behaviors.
- DDL handling: `clean_ddl()` attempts to split and sanitize DDL strings and is used by `execute_non_query()`. Modifications to DDL processing should keep the “preserve strings, split by semicolon outside strings” semantics.
- Return shapes: `execute_query()` returns a list[dict] (columns->values). Tests and callers expect this shape.

Integration points and external dependencies
- Oracle Instant Client (native DLLs): required for `cx_Oracle` to work. Paths are configured via env vars `ORACLE_CLIENT_PATH`, `ORACLE_11G_CLIENT_PATH`, `ORACLE_9I_CLIENT_PATH` (documented in `README.TXT`).
- Python driver: `cx_Oracle` pinned in `requirements-9i.txt` for compatibility with old Oracle servers. See `requirements-9i.txt` before changing driver versions.

Examples to reference in edits
- How connections are opened (copy this pattern to preserve logging and client setup):
```
with oracle_connection(config) as conn:
    rows = execute_query(conn, "SELECT * FROM ...")
```
- How errors are surfaced in tests: `test_connection()` returns a dict with keys `success`, `error`, and `database_info`. Use that shape for programmatic checks.

Where to update docs or config
- Update `README.TXT` when you change env var names, client setup instructions, or the recommended Python versions. That file is the canonical user-facing doc.
- `SOLUCAO_PYTHON_313.md` contains notes about Python 3.13 compatibility; edit it if you adjust supported Python ranges or add compilation guidance for older cx_Oracle.

When making changes, run these quick validations
1. Unit smoke: run `python -m src.main test --target` pointing to a dev/test DB (or a local Docker DB if available).
2. Lint/type check: repository uses type annotations—run your editor’s type checking (mypy/pyright) if configured.
3. Integration: verify both source (11g) and target (9i) connections in the environment you intend to run (bitness and Instant Client version matter).

If something is unclear
- Ask for the specific goal (e.g., “add support for oracledb thin mode”, “migrate to python-oracledb”, or “run exports in a separate process to allow different client PATHs”). I can propose an implementation plan with tests.

-- End of agent-oriented instructions
