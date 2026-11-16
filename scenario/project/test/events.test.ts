import assert from 'node:assert/strict';
import { after, before, describe, it } from 'node:test';
import { api, startTestServer, validShipment, type TestServer } from './helpers.ts';

describe('tracking events', () => {
  let srv: TestServer;
  let id: string;

  before(async () => {
    srv = await startTestServer();
    const created = await api(srv.url, 'POST', '/shipments', validShipment());
    id = created.body.id;
  });

  after(async () => {
    await srv.close();
  });

  it('adds a pickup event and updates the status', async () => {
    const res = await api(srv.url, 'POST', `/shipments/${id}/events`, {
      type: 'picked_up',
      at: '2026-11-10T09:00:00.000Z',
      location: 'Wien Inzersdorf',
    });
    assert.equal(res.status, 201);
    assert.equal(res.body.status, 'picked_up');
  });

  it('rejects an unknown event type', async () => {
    const res = await api(srv.url, 'POST', `/shipments/${id}/events`, { type: 'teleported' });
    assert.equal(res.status, 400);
  });

  it('rejects an invalid timestamp', async () => {
    const res = await api(srv.url, 'POST', `/shipments/${id}/events`, { type: 'in_transit', at: 'yesterday' });
    assert.equal(res.status, 400);
  });

  it('does not notify the ERP for in_transit', async () => {
    const before = srv.erpCalls.length;
    const res = await api(srv.url, 'POST', `/shipments/${id}/events`, { type: 'in_transit' });
    assert.equal(res.status, 201);
    assert.equal(srv.erpCalls.length, before);
  });

  it('emits webhook on delivered', async () => {
    const res = await api(srv.url, 'POST', `/shipments/${id}/events`, { type: 'delivered' });
    assert.equal(res.status, 201);
    assert.equal(srv.erpCalls.length, 1);
    assert.equal(srv.erpCalls[0].event.type, 'delivered');
    assert.equal(srv.erpCalls[0].shipment.id, id);
  });

  it('rejects events after delivery', async () => {
    const res = await api(srv.url, 'POST', `/shipments/${id}/events`, { type: 'exception' });
    assert.equal(res.status, 409);
    assert.equal(res.body.error.code, 'ALREADY_DELIVERED');
  });

  it('shows all events on the shipment', async () => {
    const res = await api(srv.url, 'GET', `/shipments/${id}`);
    assert.deepEqual(
      res.body.events.map((e: { type: string }) => e.type),
      ['created', 'picked_up', 'in_transit', 'delivered'],
    );
    assert.equal(res.body.eta, null);
  });
});
