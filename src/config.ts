import { config as loadEnv } from 'dotenv';
loadEnv();

export type OracleConfig = {
  dsn: string;
  user: string;
  password: string;
  schema?: string | null;
  clientPath?: string | null;
};

export function fromEnv(prefix: string): OracleConfig {
  const env = prefix.toUpperCase();
  const dsn = process.env[`${env}_DSN`];
  const user = process.env[`${env}_USER`];
  const password = process.env[`${env}_PASSWORD`];
  const clientPath = process.env[`${env}_CLIENT_PATH`] || process.env.ORACLE_CLIENT_PATH || null;

  if (!dsn || !user || !password) {
    const missing = [
      [`${env}_DSN`, dsn],
      [`${env}_USER`, user],
      [`${env}_PASSWORD`, password]
    ].filter(([, v]) => !v).map(([n]) => n).join(', ');
    throw new Error(`Variáveis ausentes para ${env}: ${missing}`);
  }

  return {
    dsn,
    user,
    password,
    schema: process.env[`${env}_SCHEMA`] ?? null,
    clientPath,
  };
}

export type ProjectConfig = {
  source: OracleConfig;
  target: OracleConfig;
  schemas: string[];
};

export function loadProjectConfig(schemas?: string): ProjectConfig {
  const schemaList: string[] = [];
  if (schemas) {
    for (const part of schemas.split(',')) {
      const s = part.trim();
      if (s) schemaList.push(s.toUpperCase());
    }
  }

  return {
    source: fromEnv('ORACLE_11G'),
    target: fromEnv('ORACLE_9I'),
    schemas: schemaList,
  };
}
