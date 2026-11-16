import assert from 'node:assert/strict';
import { after, before, describe, it } from 'node:test';
import { api, startTestServer, validShipment, type TestServer } from './helpers.ts';

describe('shipments API', () => {
  let srv: TestServer;

  before(async () => {
    srv = await startTestServer();
  });

  after(async () => {
    await srv.close();
  });

  it('answers the health check', async () => {
    const res = await api(srv.url, 'GET', '/health');
    assert.equal(res.status, 200);
    assert.deepEqual(res.body, { ok: true });
  });

  it('creates a shipment', async () => {
    const res = await api(srv.url, 'POST', '/shipments', validShipment());
    assert.equal(res.status, 201);
    assert.match(res.body.id, /^shp_/);
    assert.equal(res.body.tracking_number, 'RR123456785AT');
    assert.equal(res.body.status, 'created');
    assert.match(res.body.eta, /^\d{4}-\d{2}-\d{2}$/);
  });

  it('rejects a duplicate tracking number', async () => {
    const res = await api(srv.url, 'POST', '/shipments', validShipment());
    assert.equal(res.status, 409);
    assert.equal(res.body.error.code, 'DUPLICATE_TRACKING_NUMBER');
  });

  it('rejects an unknown carrier', async () => {
    const res = await api(srv.url, 'POST', '/shipments', validShipment({ tracking_number: 'X1', carrier: 'FEDEX' }));
    assert.equal(res.status, 400);
    assert.equal(res.body.error.code, 'VALIDATION_FAILED');
  });

  it('rejects a missing recipient', async () => {
    const res = await api(srv.url, 'POST', '/shipments', { tracking_number: 'X2', carrier: 'DHL' });
    assert.equal(res.status, 400);
    assert.equal(res.body.error.code, 'VALIDATION_FAILED');
  });

  it('rejects invalid JSON', async () => {
    const res = await fetch(srv.url + '/shipments', {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: '{"tracking_number": ',
    });
    assert.equal(res.status, 400);
    assert.equal((await res.json()).error.code, 'INVALID_JSON');
  });

  it('gets one shipment with its events', async () => {
    const created = await api(srv.url, 'POST', '/shipments', validShipment({ tracking_number: 'JJD000390007788', carrier: 'DHL' }));
    const res = await api(srv.url, 'GET', `/shipments/${created.body.id}`);
    assert.equal(res.status, 200);
    assert.equal(res.body.carrier, 'DHL');
    assert.equal(res.body.events.length, 1);
    assert.equal(res.body.events[0].type, 'created');
  });

  it('returns 404 for an unknown shipment', async () => {
    const res = await api(srv.url, 'GET', '/shipments/shp_nope');
    assert.equal(res.status, 404);
    assert.equal(res.body.error.code, 'SHIPMENT_NOT_FOUND');
  });

  it('lists shipments and filters by carrier', async () => {
    const all = await api(srv.url, 'GET', '/shipments');
    assert.equal(all.status, 200);
    assert.equal(all.body.count, 2);
    const dhl = await api(srv.url, 'GET', '/shipments?carrier=DHL');
    assert.equal(dhl.body.count, 1);
    assert.equal(dhl.body.items[0].carrier, 'DHL');
  });

  it('returns 405 for a wrong method on a known route', async () => {
    const res = await api(srv.url, 'POST', '/health', {});
    assert.equal(res.status, 405);
  });
});
