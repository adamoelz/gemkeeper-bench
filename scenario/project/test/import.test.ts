import assert from 'node:assert/strict';
import { after, before, describe, it } from 'node:test';
import { parseLegacyCsv } from '../src/legacy/csvImport.ts';
import { api, startTestServer, type TestServer } from './helpers.ts';

const CSV = [
  'tracking,carrier,service,name,street,zip,city,country,phone',
  'RR987654326AT,OEPOST,standard,Maria Gruber,Landstraßer Hauptstraße 5,1030,Wien,AT,+43 660 1234567',
  '00340434161094042557,DPDAT,express,Lukas Berger,Herrengasse 12,8010,Graz,AT,',
].join('\n');

describe('legacy CSV parser', () => {
  it('maps legacy carrier codes', () => {
    const rows = parseLegacyCsv(CSV);
    assert.equal(rows.length, 2);
    assert.equal(rows[0].carrier, 'ATP');
    assert.equal(rows[1].carrier, 'DPD');
    assert.equal(rows[0].recipient.phone, '+43 660 1234567');
    assert.equal(rows[1].recipient.phone, undefined);
  });
});

describe('POST /import', () => {
  let srv: TestServer;

  before(async () => {
    srv = await startTestServer();
  });

  after(async () => {
    await srv.close();
  });

  it('imports all valid rows', async () => {
    const res = await api(srv.url, 'POST', '/import', CSV);
    assert.equal(res.status, 200);
    assert.equal(res.body.created, 2);
    assert.deepEqual(res.body.errors, []);
  });

  it('reports duplicates per line', async () => {
    const res = await api(srv.url, 'POST', '/import', CSV);
    assert.equal(res.body.created, 0);
    assert.equal(res.body.errors.length, 2);
    assert.equal(res.body.errors[0].line, 2);
  });
});
