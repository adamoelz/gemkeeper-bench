// Ported from logistik-core (lib/import/csv.js), 2024.
// Expected header: tracking,carrier,service,name,street,zip,city,country,phone
import { mapLegacyCarrier } from './carrierCodes.ts';

export interface LegacyRow {
  tracking_number: string;
  carrier: string;
  service_level: string;
  recipient: {
    name: string;
    street: string;
    zip: string;
    city: string;
    country: string;
    phone?: string;
  };
}

export function parseLegacyCsv(text: string): LegacyRow[] {
  const lines = text.split(/\r?\n/).filter((l) => l.trim() !== '');
  if (lines.length === 0) return [];

  const header = lines[0].split(',').map((h) => h.trim().toLowerCase());
  const rows: LegacyRow[] = [];

  for (const line of lines.slice(1)) {
    const cells = line.split(',');
    const get = (name: string): string => (cells[header.indexOf(name)] ?? '').trim();
    const phone = get('phone');
    rows.push({
      tracking_number: get('tracking'),
      carrier: mapLegacyCarrier(get('carrier')),
      service_level: get('service') || 'standard',
      recipient: {
        name: get('name'),
        street: get('street'),
        zip: get('zip'),
        city: get('city'),
        country: get('country') || 'AT',
        ...(phone ? { phone } : {}),
      },
    });
  }
  return rows;
}
