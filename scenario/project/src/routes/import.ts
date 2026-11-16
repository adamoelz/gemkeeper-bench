import { parseLegacyCsv } from '../legacy/csvImport.ts';
import { readBody, sendJson } from '../lib/http.ts';
import { validateShipmentInput } from '../lib/validate.ts';
import type { Router } from '../router.ts';
import type { Store } from '../store.ts';

/** POST /import: bulk import in the legacy CSV format (text/csv body). */
export function registerImportRoutes(router: Router, store: Store): void {
  router.post('/import', async ({ req, res }) => {
    const rows = parseLegacyCsv(await readBody(req));
    let created = 0;
    const errors: Array<{ line: number; message: string }> = [];

    rows.forEach((row, i) => {
      const line = i + 2; // 1-based, after the header line
      try {
        const input = validateShipmentInput(row);
        if (store.findByTrackingNumber(input.trackingNumber)) {
          errors.push({ line, message: `duplicate tracking number ${input.trackingNumber}` });
          return;
        }
        store.addShipment(input);
        created++;
      } catch (err) {
        errors.push({ line, message: err instanceof Error ? err.message : String(err) });
      }
    });

    sendJson(res, 200, { created, errors });
  });
}
