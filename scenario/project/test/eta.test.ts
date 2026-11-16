import assert from 'node:assert/strict';
import { describe, it } from 'node:test';
import { addBusinessDays, calculateEta, isBusinessDay } from '../src/services/eta.ts';
import type { Shipment, TrackingEvent } from '../src/types.ts';

function shipment(overrides: Partial<Shipment> = {}): Shipment {
  return {
    id: 'shp_test',
    trackingNumber: 'RR123456785AT',
    carrier: 'ATP',
    serviceLevel: 'standard',
    recipient: { name: 'A', street: 'B', zip: '1010', city: 'Wien', country: 'AT' },
    status: 'created',
    createdAt: '2026-11-09T08:00:00.000Z', // Monday
    ...overrides,
  };
}

function event(type: TrackingEvent['type'], at: string): TrackingEvent {
  return { id: `evt_${type}_${at}`, shipmentId: 'shp_test', type, at };
}

describe('isBusinessDay', () => {
  it('treats Saturday and Sunday as non-business days', () => {
    assert.equal(isBusinessDay(new Date('2026-11-14T10:00:00Z')), false);
    assert.equal(isBusinessDay(new Date('2026-11-15T10:00:00Z')), false);
  });

  it('treats Monday to Friday as business days', () => {
    for (const day of ['09', '10', '11', '12', '13']) {
      assert.equal(isBusinessDay(new Date(`2026-11-${day}T10:00:00Z`)), true);
    }
  });
});

describe('addBusinessDays', () => {
  it('adds days within a week', () => {
    assert.equal(addBusinessDays(new Date('2026-11-09T10:00:00Z'), 2).toISOString().slice(0, 10), '2026-11-11');
  });

  it('skips the weekend', () => {
    assert.equal(addBusinessDays(new Date('2026-11-13T10:00:00Z'), 1).toISOString().slice(0, 10), '2026-11-16');
  });

  it('returns the same day for 0 days', () => {
    assert.equal(addBusinessDays(new Date('2026-11-10T10:00:00Z'), 0).toISOString().slice(0, 10), '2026-11-10');
  });
});

describe('calculateEta', () => {
  it('uses createdAt when there is no pickup yet', () => {
    assert.equal(calculateEta(shipment(), []), '2026-11-11');
  });

  it('counts from the pickup event', () => {
    const events = [event('picked_up', '2026-11-10T09:00:00.000Z')];
    assert.equal(calculateEta(shipment({ status: 'picked_up' }), events), '2026-11-12');
  });

  it('moves pickups after the cutoff to the next business day', () => {
    const events = [event('picked_up', '2026-11-10T15:30:00.000Z')];
    assert.equal(calculateEta(shipment({ status: 'picked_up' }), events), '2026-11-13');
  });

  it('treats a Saturday pickup as a Monday pickup', () => {
    const events = [event('picked_up', '2026-11-14T09:00:00.000Z')];
    assert.equal(calculateEta(shipment({ status: 'picked_up' }), events), '2026-11-18');
  });

  it('adds delay days for each exception', () => {
    const events = [
      event('picked_up', '2026-11-10T09:00:00.000Z'),
      event('exception', '2026-11-11T09:00:00.000Z'),
    ];
    assert.equal(calculateEta(shipment({ status: 'exception' }), events), '2026-11-16');
  });

  it('uses the carrier and service level transit times', () => {
    assert.equal(calculateEta(shipment({ carrier: 'UPS', serviceLevel: 'economy' }), []), '2026-11-16');
    assert.equal(calculateEta(shipment({ carrier: 'DHL', serviceLevel: 'express' }), []), '2026-11-10');
  });

  it('returns null once delivered', () => {
    assert.equal(calculateEta(shipment({ status: 'delivered' }), []), null);
  });
});
