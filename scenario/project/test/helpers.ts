import { createServer } from 'node:http';
import type { AddressInfo } from 'node:net';
import { createApp } from '../src/app.ts';
import { Store } from '../src/store.ts';
import type { Shipment, TrackingEvent } from '../src/types.ts';

process.env.LOG_LEVEL = 'silent';

export interface TestServer {
  url: string;
  store: Store;
  /** Every call the app made to the (fake) ERP notifier. */
  erpCalls: Array<{ shipment: Shipment; event: TrackingEvent }>;
  close(): Promise<void>;
}

export async function startTestServer(): Promise<TestServer> {
  const store = new Store();
  const erpCalls: TestServer['erpCalls'] = [];
  const app = createApp({
    store,
    notify: async (shipment, event) => {
      erpCalls.push({ shipment, event });
    },
  });
  const server = createServer((req, res) => {
    void app.handle(req, res);
  });
  await new Promise<void>((resolve) => server.listen(0, '127.0.0.1', resolve));
  const { port } = server.address() as AddressInfo;
  return {
    url: `http://127.0.0.1:${port}`,
    store,
    erpCalls,
    close: () => new Promise((resolve, reject) => server.close((err) => (err ? reject(err) : resolve()))),
  };
}

export async function api(
  base: string,
  method: string,
  path: string,
  body?: unknown,
): Promise<{ status: number; body: any }> {
  const res = await fetch(base + path, {
    method,
    headers: body === undefined ? {} : { 'content-type': typeof body === 'string' ? 'text/csv' : 'application/json' },
    body: body === undefined ? undefined : typeof body === 'string' ? body : JSON.stringify(body),
  });
  const text = await res.text();
  return { status: res.status, body: text ? JSON.parse(text) : null };
}

export function validShipment(overrides: Record<string, unknown> = {}) {
  return {
    tracking_number: 'RR123456785AT',
    carrier: 'ATP',
    service_level: 'standard',
    recipient: {
      name: 'Anna Huber',
      street: 'Mariahilfer Straße 1',
      zip: '1060',
      city: 'Wien',
      country: 'AT',
    },
    ...overrides,
  };
}
