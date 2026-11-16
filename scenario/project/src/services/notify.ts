import { getConfig } from '../config.ts';
import { log } from '../lib/log.ts';
import type { Shipment, TrackingEvent } from '../types.ts';

/** Body we POST to the ERP event intake. */
export interface ErpPayload {
  event_id: string;
  shipment_id: string;
  tracking_number: string;
  carrier: string;
  type: string;
  at: string;
}

export type Notifier = (shipment: Shipment, event: TrackingEvent) => Promise<void>;

export function toErpPayload(shipment: Shipment, event: TrackingEvent): ErpPayload {
  return {
    event_id: event.id,
    shipment_id: shipment.id,
    tracking_number: shipment.trackingNumber,
    carrier: shipment.carrier,
    type: event.type,
    at: event.at,
  };
}

/** Sends one event to the ERP. Single attempt; throws on network errors and non-2xx responses. */
export async function postToErp(
  payload: ErpPayload,
  url: string = getConfig().erp.url,
  fetchImpl: typeof fetch = fetch,
): Promise<number> {
  const res = await fetchImpl(url, {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify(payload),
    signal: AbortSignal.timeout(getConfig().erp.timeoutMs),
  });
  if (!res.ok) throw new Error(`ERP responded ${res.status}`);
  return res.status;
}

/** Default notifier used by the app: forwards the event, logs failures, never throws. */
export const notifyErp: Notifier = async (shipment, event) => {
  try {
    await postToErp(toErpPayload(shipment, event));
    log.info('erp notified', { event_id: event.id, shipment_id: shipment.id, type: event.type });
  } catch (err) {
    log.warn('erp notify failed', { event_id: event.id, err: String(err) });
  }
};
