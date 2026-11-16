import { HttpError, readJson, sendJson } from '../lib/http.ts';
import type { Router } from '../router.ts';
import type { Notifier } from '../services/notify.ts';
import type { Store } from '../store.ts';
import { EVENT_TYPES, type EventType } from '../types.ts';

const ALLOWED: readonly EventType[] = EVENT_TYPES.filter((t) => t !== 'created');

/** Event types that are forwarded to the ERP. */
const FORWARDED: readonly EventType[] = ['delivered', 'exception'];

export function registerEventRoutes(router: Router, store: Store, notify: Notifier): void {
  router.post('/shipments/:id/events', async ({ req, res, params }) => {
    const shipment = store.getShipment(params.id);
    if (!shipment) throw new HttpError(404, 'SHIPMENT_NOT_FOUND', 'Shipment not found');

    const body = (await readJson(req)) as Record<string, unknown>;
    const type = body.type;
    if (typeof type !== 'string' || !ALLOWED.includes(type as EventType)) {
      throw new HttpError(400, 'VALIDATION_FAILED', `type must be one of ${ALLOWED.join(', ')}`);
    }
    if (shipment.status === 'delivered') {
      throw new HttpError(409, 'ALREADY_DELIVERED', 'Shipment is already delivered');
    }

    const at = typeof body.at === 'string' ? new Date(body.at) : new Date();
    if (Number.isNaN(at.getTime())) throw new HttpError(400, 'VALIDATION_FAILED', 'at must be an ISO-8601 timestamp');

    const event = store.addEvent(shipment.id, type as EventType, {
      at: at.toISOString(),
      location: typeof body.location === 'string' ? body.location : undefined,
      note: typeof body.note === 'string' ? body.note : undefined,
    });

    if (FORWARDED.includes(event.type)) void notify(shipment, event);

    sendJson(res, 201, { id: event.id, type: event.type, at: event.at, status: shipment.status });
  });
}
