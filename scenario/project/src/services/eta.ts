import type { Carrier, ServiceLevel, Shipment, TrackingEvent } from '../types.ts';

/** Transit time in business days, counted from the (effective) pickup day. */
const TRANSIT_DAYS: Record<Carrier, Record<ServiceLevel, number>> = {
  ATP: { economy: 4, standard: 2, express: 1 },
  DHL: { economy: 5, standard: 2, express: 1 },
  DPD: { economy: 4, standard: 2, express: 1 },
  GLS: { economy: 4, standard: 3, express: 1 },
  UPS: { economy: 5, standard: 3, express: 1 },
};

/** Parcels picked up at or after this hour (UTC) count as picked up on the next business day. */
export const CUTOFF_HOUR_UTC = 14;

/** Every exception event (failed delivery attempt, damaged label, ...) adds this many business days. */
export const EXCEPTION_DELAY_DAYS = 2;

export function isBusinessDay(date: Date): boolean {
  const day = date.getUTCDay();
  return day !== 0 && day !== 6;
}

function startOfDayUtc(date: Date): Date {
  return new Date(Date.UTC(date.getUTCFullYear(), date.getUTCMonth(), date.getUTCDate()));
}

export function addBusinessDays(start: Date, days: number): Date {
  const date = startOfDayUtc(start);
  let left = days;
  while (left > 0) {
    date.setUTCDate(date.getUTCDate() + 1);
    if (isBusinessDay(date)) left--;
  }
  return date;
}

/**
 * Expected delivery date as YYYY-MM-DD, or null once the shipment is delivered.
 * Weekends are skipped. Times are UTC.
 */
export function calculateEta(shipment: Shipment, events: TrackingEvent[]): string | null {
  if (shipment.status === 'delivered') return null;

  const sorted = [...events].sort((a, b) => a.at.localeCompare(b.at));
  const pickup = sorted.find((e) => e.type === 'picked_up');
  const start = new Date(pickup ? pickup.at : shipment.createdAt);

  let pickupDay = startOfDayUtc(start);
  if (start.getUTCHours() >= CUTOFF_HOUR_UTC || !isBusinessDay(pickupDay)) {
    pickupDay = addBusinessDays(pickupDay, 1);
  }

  const exceptions = sorted.filter((e) => e.type === 'exception').length;
  const days = TRANSIT_DAYS[shipment.carrier][shipment.serviceLevel] + exceptions * EXCEPTION_DELAY_DAYS;

  return addBusinessDays(pickupDay, days).toISOString().slice(0, 10);
}
