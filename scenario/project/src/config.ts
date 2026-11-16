import { readFileSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

export interface Config {
  port: number;
  dataFile: string;
  erp: {
    url: string;
    timeoutMs: number;
  };
}

export const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
export const CONFIG_FILE = path.join(ROOT, 'config', 'default.json');

export function loadConfig(env: NodeJS.ProcessEnv = process.env): Config {
  const raw = JSON.parse(readFileSync(CONFIG_FILE, 'utf8')) as Config;
  return {
    port: env.PORT ? Number(env.PORT) : raw.port,
    dataFile: path.resolve(ROOT, env.DATA_FILE ?? raw.dataFile),
    erp: {
      url: env.ERP_URL ?? raw.erp.url,
      timeoutMs: raw.erp.timeoutMs,
    },
  };
}

let current: Config | undefined;

export function getConfig(): Config {
  current ??= loadConfig();
  return current;
}

/** Test hook: replace the active configuration. */
export function setConfig(config: Config): void {
  current = config;
}
