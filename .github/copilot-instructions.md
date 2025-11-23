## Quick orientation for AI coding agents (Node.js / TypeScript port)

This repository has been ported to Node.js/TypeScript with **full feature parity** to the original Python version. Focus on `src/` and the runtime requirements in `README.TXT`.

Key files
- `src/config.ts` — loads environment variables into `OracleConfig` and `ProjectConfig` types.
- `src/db_utils.ts` — Oracle Client initialization (when possible), connection helpers, `executeQuery`, `executeNonQuery`, `cleanDDL`, and `testConnection` with comprehensive error mapping.
- `src/exporter.ts` — complete export/copy logic: DDL extraction via `DBMS_METADATA`, data copying with batching, LOB handling, table recreation, and grant/view/trigger/procedure/function/package DDL.
- `src/validator.ts` — post-import validation: table row count comparison, synonym validation, grant comparison, and object type validation (views, triggers, procedures, functions).
- `src/main.ts` — CLI entrypoint with full command handlers (test, copy, validate) including decorative logging and error messages in Portuguese.

Big picture
- The app connects to two Oracle databases (11g source and 9i target) using `oracledb` (thick client). Native Oracle Instant Client DLLs are required for `oracledb` to work; 9i target requires an older client (11.2) to avoid `ORA-03134`.
- **Status**: All three major components (exporter, validator, CLI) are fully ported and compilation verified. Ready for integration testing with real Oracle databases.

Developer workflows
- Install dependencies (note: `oracledb` is optional and can be installed after the Instant Client is configured):
```powershell
npm install
npm run build     # or just npm run build (compiles TypeScript to dist/)
```
- Run the CLI in dev mode (ts-node):
```powershell
npm run dev -- test
npm run dev -- test --target
npm run dev -- copy --schemas SCHEMA1,SCHEMA2
npm run dev -- validate
```
- Run compiled version:
```powershell
node dist/main.js test
node dist/main.js copy --schemas SCHEMA1,SCHEMA2 --batch-size 1000
node dist/main.js validate
```

Project-specific patterns
- Client init: `src/db_utils.ts` calls `oracledb.initOracleClient({libDir})` when available; otherwise it prepends the client path to `PATH` and sets `ORACLE_HOME`.
- Error handling: database errors are inspected by `errorNum` and mapped to friendly messages (see `testConnection`). Keep these mappings when changing DB code.
- DDL processing: `cleanDDL()` preserves string literals and splits statements by semicolons outside strings — preserve this behavior in DDL processing.
- Batching: `chunked()` helper in `db_utils.ts` enables efficient bulk inserts with configurable batch size (default 500 rows).

Integration notes
- `oracledb` is an optional dependency; installing it without the Instant Client may fail. The repo includes `scripts/diag_oracle_client.ps1` to help Windows users verify their Instant Client installation.
- TypeScript strict mode enabled; all source files type-safe and compile without errors.

Completed implementation details
- **exporter.ts**: Full DDL extraction (DBMS_METADATA with fallback to ALL_SOURCE), PACKAGE/PACKAGE_BODY LOB handling, table drop/create/truncate logic, data export/import with batching, error recovery.
- **validator.ts**: ValidationDetail/ValidationReport classes, table row count comparison, synonym/grant/object set comparison, detailed mismatch reporting.
- **main.ts**: Full CLI with decorative box logging, formatted error messages in Portuguese, proper exit codes, comprehensive usage examples.

Run and test
- Use the `test` command to verify connections before attempting `copy` or `validate`.
- For integration testing: run the exporter in a controlled environment with real Oracle databases.
- Examine log output for detailed progress (batch counts, object creation attempts, error recovery).

If anything is unclear or needs enhancement, ask for specific feature improvements (thin-client mode, subprocess isolation for different client paths, performance optimization, etc.).
