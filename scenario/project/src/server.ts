import { createServer } from 'node:http';
import { createApp } from './app.ts';
import { getConfig } from './config.ts';
import { log } from './lib/log.ts';
import { Store } from './store.ts';

const config = getConfig();
const store = new Store(config.dataFile);
const app = createApp({ store });

const server = createServer((req, res) => {
  void app.handle(req, res);
});

server.listen(config.port, () => {
  log.info('parcel-tracker listening', { port: config.port });
});

for (const signal of ['SIGINT', 'SIGTERM'] as const) {
  process.on(signal, () => {
    server.close(() => process.exit(0));
  });
}
