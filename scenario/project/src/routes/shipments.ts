import { HttpError, readJson, sendJson } from '../lib/http.ts';
import { validateShipmentInput } from '../lib/validate.ts';
import type { Router } from '../router.ts';
import { calculateEta } from '../services/eta.ts';
import type { Store } from '../store.ts';
import type { Shipment } from '../types.ts';

export function shipmentToApi(s: Shipment) {
  return {
    id: s.id,
    tracking_number: s.trackingNumber,
    carrier: s.carrier,
    service_level: s.serviceLevel,
    status: s.status,
    created_at: s.createdAt,
    recipient: { ...s.recipient },
  };
}

export function registerShipmentRoutes(router: Router, store: Store): void {
  router.post('/shipments', async ({ req, res }) => {
    const input = validateShipmentInput(await readJson(req));
    if (store.findByTrackingNumber(input.trackingNumber)) {
      throw new HttpError(409, 'DUPLICATE_TRACKING_NUMBER', 'A shipment with this tracking number already exists');
    }
    const shipment = store.addShipment(input);
    sendJson(res, 201, { ...shipmentToApi(shipment), eta: calculateEta(shipment, store.eventsFor(shipment.id)) });
  });

  router.get('/shipments', ({ res, query }) => {
    const limit = Math.min(Number(query.get('limit') ?? 50) || 50, 500);
    const items = store
      .listShipments({
        carrier: query.get('carrier') ?? undefined,
        status: query.get('status') ?? undefined,
        limit,
      })
      .map(shipmentToApi);
    sendJson(res, 200, { items, count: items.length });
  });

  router.get('/shipments/:id', ({ res, params }) => {
    const shipment = store.getShipment(params.id);
    if (!shipment) throw new HttpError(404, 'SHIPMENT_NOT_FOUND', 'Shipment not found');
    const events = store.eventsFor(shipment.id);
    sendJson(res, 200, {
      ...shipmentToApi(shipment),
      eta: calculateEta(shipment, events),
      events: events.map((e) => ({ type: e.type, at: e.at, location: e.location ?? null })),
    });
  });
}
