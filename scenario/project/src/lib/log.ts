type Level = 'debug' | 'info' | 'warn' | 'error';

const ORDER: Record<Level, number> = { debug: 10, info: 20, warn: 30, error: 40 };

function threshold(): number {
  const level = process.env.LOG_LEVEL;
  if (level === 'silent') return Number.POSITIVE_INFINITY;
  return ORDER[level as Level] ?? ORDER.info;
}

function write(level: Level, msg: string, fields: Record<string, unknown> = {}): void {
  if (ORDER[level] < threshold()) return;
  const line = JSON.stringify({ ts: new Date().toISOString(), level, msg, ...fields });
  process.stdout.write(line + '\n');
}

/** JSON-lines logger. One object per line on stdout. */
export const log = {
  debug: (msg: string, fields?: Record<string, unknown>) => write('debug', msg, fields),
  info: (msg: string, fields?: Record<string, unknown>) => write('info', msg, fields),
  warn: (msg: string, fields?: Record<string, unknown>) => write('warn', msg, fields),
  error: (msg: string, fields?: Record<string, unknown>) => write('error', msg, fields),
};
