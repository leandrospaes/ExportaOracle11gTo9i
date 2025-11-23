import { Command } from 'commander';
import { loadProjectConfig } from './config';
import { testConnection } from './db_utils';
import winston from 'winston';

const logger = winston.createLogger({ transports: [new winston.transports.Console({ format: winston.format.simple() })] });

const program = new Command();

program
  .name('exporta11gto9i')
  .description('Exportador Oracle 11g -> 9i (TypeScript port)')
  .version('0.1.0');

program.command('test')
  .description('Test connections')
  .option('--source', 'Only source')
  .option('--target', 'Only target')
  .action(async (opts: any) => {
    const cfg = loadProjectConfig();
    if (!opts.target) {
      logger.info('Testing source...');
      const r = await testConnection(cfg.source, 'Banco Origem (11g)');
      logger.info(JSON.stringify(r, null, 2));
    }
    if (!opts.source) {
      logger.info('Testing target...');
      const r = await testConnection(cfg.target, 'Banco Destino (9i)');
      logger.info(JSON.stringify(r, null, 2));
    }
  });

program.command('copy')
  .description('Copy schemas (not fully implemented)')
  .option('--schemas <list>', 'Comma separated schemas')
  .action(async (opts: any) => {
    logger.info('COPY not yet implemented in Node port. Use Python tool or request full implementation.');
  });

program.command('validate')
  .description('Validate import (not fully implemented)')
  .option('--schemas <list>', 'Comma separated schemas')
  .action(async (opts: any) => {
    logger.info('VALIDATE not yet implemented in Node port.');
  });

program.parseAsync(process.argv).catch((err: any) => {
  logger.error(err);
  process.exit(1);
});
