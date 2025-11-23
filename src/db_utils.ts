import oracledb from 'oracledb';
import { OracleConfig } from './config';
import { Logger } from 'winston';
import winston from 'winston';

const logger: Logger = winston.createLogger({
  level: 'info',
  transports: [new winston.transports.Console({ format: winston.format.simple() })],
});

const configuredClientPaths = new Set<string>();

function configureOracleClient(clientPath?: string | null) {
  if (!clientPath) return;
  if (configuredClientPaths.has(clientPath)) return;

  try {
    // node-oracledb supports initOracleClient({libDir})
    if ((oracledb as any).initOracleClient) {
      (oracledb as any).initOracleClient({ libDir: clientPath });
      logger.info(`Oracle Client configured (initOracleClient): ${clientPath}`);
      configuredClientPaths.add(clientPath);
    } else {
      // fallback: prepend to PATH and set ORACLE_HOME
      const p = process.env.PATH || '';
      if (!p.includes(clientPath)) {
        process.env.PATH = `${clientPath};${p}`;
        logger.info(`Oracle Client path added to PATH: ${clientPath}`);
      } else {
        logger.info(`Oracle Client path already in PATH: ${clientPath}`);
      }
      if (!process.env.ORACLE_HOME) {
        process.env.ORACLE_HOME = clientPath;
        logger.info(`ORACLE_HOME set to: ${clientPath}`);
      }
      configuredClientPaths.add(clientPath);
    }
  } catch (e: any) {
    logger.warn(`Failed to configure Oracle Client (${clientPath}): ${e}`);
  }
}

export async function oracleConnection(config: OracleConfig) {
  if (config.clientPath) configureOracleClient(config.clientPath);

  try {
    const conn = await oracledb.getConnection({
      user: config.user,
      password: config.password,
      connectString: config.dsn,
    });
    return conn;
  } catch (e: any) {
    const errNum = e && (e.errorNum ?? e.errnum ?? e.errno ?? null);
    // Re-throw after logging similar messages from Python
    if (errNum === 1047) {
      logger.error('Oracle Client not found. Configure ORACLE_CLIENT_PATH or add to PATH');
    } else if (errNum === 3134) {
      logger.error('ERROR: Incompatible Oracle Client version (server 9i requires older client like 11.2)');
      logger.error(`DSN that failed: ${config.dsn}`);
      logger.error(`User: ${config.user}`);
      if (config.clientPath) logger.error(`Oracle Client Path configured: ${config.clientPath}`);
      else logger.error('⚠ ORACLE_9I_CLIENT_PATH NOT CONFIGURED!');
    } else if (errNum === 1017) {
      logger.error(`Invalid credentials for ${config.user}@${config.dsn}`);
    } else {
      logger.error(`Error connecting to ${config.dsn}: ${e && e.message}`);
    }
    throw e;
  }
}

export async function executeQuery(connection: any, sql: string, params?: any[]) {
  const opts = { outFormat: oracledb.OUT_FORMAT_OBJECT } as any;
  const result = await connection.execute(sql, params || [], opts);
  return result.rows || [];
}

export function cleanDDL(ddl: string | { read?: () => string } | null): string[] {
  if (!ddl) return [];
  if ((ddl as any).read) ddl = (ddl as any).read();
  ddl = String(ddl);
  ddl = ddl.replace('\ufeff', '').replace('\u200b', '').replace('\r\n', '\n').replace('\r', '\n');

  const lines = ddl.split('\n');
  const cleanedLines: string[] = [];
  for (const line of lines) {
    const cleaned = Array.from(line).map(c => ((c.charCodeAt(0) >= 32) || c === '\t' || c === '\n') ? c : ' ').join('');
    cleanedLines.push(cleaned);
  }
  ddl = cleanedLines.join('\n');

  const statements: string[] = [];
  let current = '';
  let inString = false;
  let stringChar: string | null = null;
  let escapeNext = false;

  for (let i = 0; i < ddl.length; i++) {
    const ch = ddl[i];
    if (escapeNext) {
      current += ch;
      escapeNext = false;
      continue;
    }
    if (ch === '\\') {
      escapeNext = true;
      current += ch;
      continue;
    }
    if (ch === '"' || ch === "'") {
      if (!inString) {
        inString = true;
        stringChar = ch;
      } else if (ch === stringChar) {
        inString = false;
        stringChar = null;
      }
      current += ch;
    } else if (!inString && ch === ';') {
      const stmt = current.trim();
      if (stmt) statements.push(stmt);
      current = '';
    } else {
      current += ch;
    }
  }
  if (current.trim()) statements.push(current.trim());

  const cleanedStatements = statements.map(s => s.replace(/;+$/g, '').trim()).filter(Boolean);
  return cleanedStatements.length ? cleanedStatements : [ddl.trim().replace(/;+$/g, '')];
}

export async function executeNonQuery(connection: any, sql: string, params?: any[]) {
  if (params && params.length) {
    await connection.execute(sql, params);
    await connection.commit();
    return;
  }
  const stmts = cleanDDL(sql);
  for (const stmt of stmts) {
    if (!stmt.trim()) continue;
    try {
      await connection.execute(stmt);
    } catch (e: any) {
      const errNum = e && (e.errorNum ?? e.errnum ?? null);
      if (errNum === 911) {
        // ORA-00911 invalid character - try with semicolon
        let s = stmt;
        if (!s.trim().endsWith(';')) s = s + ';';
        await connection.execute(s);
      } else {
        throw e;
      }
    }
  }
  await connection.commit();
}

export function chunked<T>(iterable: T[], size: number): T[][] {
  const out: T[][] = [];
  for (let i = 0; i < iterable.length; i += size) out.push(iterable.slice(i, i + size));
  return out;
}

export async function testConnection(config: OracleConfig, label = 'Banco') {
  const result: any = {
    success: false,
    label,
    dsn: config.dsn,
    user: config.user,
    error: null,
    database_info: {},
  };

  if (config.clientPath) configureOracleClient(config.clientPath);
  try {
    logger.info(`Testando conexão com ${label}...`);
    logger.info(`  DSN: ${config.dsn}`);
    logger.info(`  Usuário: ${config.user}`);

    const conn = await oracleConnection(config);
    try {
      const v = await executeQuery(conn, "SELECT * FROM v$version WHERE banner LIKE 'Oracle%'");
      const version = (v && v[0] && (v[0] as any).BANNER) || 'Desconhecida';
      const instanceInfo = await executeQuery(conn, 'SELECT instance_name, host_name, status FROM v$instance');
      const dbNameRow = await executeQuery(conn, 'SELECT name FROM v$database');
      const dbName = (dbNameRow && dbNameRow[0] && (dbNameRow[0] as any).NAME) || 'Desconhecido';
      const sysdateRow = await executeQuery(conn, 'SELECT SYSDATE FROM DUAL');
      const sysdate = sysdateRow && sysdateRow[0] ? Object.values(sysdateRow[0])[0] : null;
      const currentUserRow = await executeQuery(conn, 'SELECT USER FROM DUAL');
      const currentUser = currentUserRow && currentUserRow[0] ? Object.values(currentUserRow[0])[0] : null;

      result.database_info = {
        version,
        database_name: dbName,
        instance_name: instanceInfo && instanceInfo[0] ? (instanceInfo[0] as any).INSTANCE_NAME : 'Desconhecido',
        host_name: instanceInfo && instanceInfo[0] ? (instanceInfo[0] as any).HOST_NAME : 'Desconhecido',
        status: instanceInfo && instanceInfo[0] ? (instanceInfo[0] as any).STATUS : 'Desconhecido',
        current_user: currentUser,
        server_date: sysdate ? String(sysdate) : null,
      };

      result.success = true;
      logger.info('  ✓ Conexão estabelecida com sucesso!');
      logger.info(`  Versão do Oracle: ${version}`);
    } finally {
      try { await (conn as any).close(); } catch (e) { /* ignore */ }
      logger.info('  ✓ Conexão fechada');
    }
  } catch (e: any) {
    result.error = { code: e && (e.errorNum ?? e.errnum ?? null), message: e && e.message };
    const code = result.error.code;
    if (code === 1047) logger.error('  ✗ Oracle Client não encontrado');
    else if (code === 1017) logger.error('  ✗ Credenciais inválidas');
    else if (code === 12541) logger.error('  ✗ Listener não encontrado - servidor pode estar inacessível');
    else if (code === 12514) logger.error('  ✗ Serviço não conhecido pelo listener');
    else if (code === 3134) {
      logger.error('  ✗ Versão do Oracle Client incompatível com Oracle 9i');
      logger.error('  SOLUÇÃO: instalar Oracle Instant Client 11.2 e usar cx_Oracle/oracledb compatível');
    } else logger.error(`  ✗ Erro de conexão: ${result.error.message} (código ${result.error.code})`);
  }

  return result;
}
