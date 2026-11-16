import { sendJson } from './lib/http.ts';
import { Router } from './router.ts';
import { registerEventRoutes } from './routes/events.ts';
import { registerImportRoutes } from './routes/import.ts';
import { registerShipmentRoutes } from './routes/shipments.ts';
import { notifyErp, type Notifier } from './services/notify.ts';
import type { Store } from './store.ts';

export interface AppDeps {
  store: Store;
  notify?: Notifier;
}

export function createApp({ store, notify = notifyErp }: AppDeps): Router {
  const router = new Router();
  router.get('/health', ({ res }) => sendJson(res, 200, { ok: true }));
  registerShipmentRoutes(router, store);
  registerEventRoutes(router, store, notify);
  registerImportRoutes(router, store);
  return router;
}
