import { CARRIERS, SERVICE_LEVELS, type Carrier, type Recipient, type ServiceLevel } from '../types.ts';
import { HttpError } from './http.ts';

export interface ShipmentInput {
  trackingNumber: string;
  carrier: Carrier;
  serviceLevel: ServiceLevel;
  recipient: Recipient;
}

function fail(message: string): never {
  throw new HttpError(400, 'VALIDATION_FAILED', message);
}

function requireString(obj: Record<string, unknown>, key: string, label: string = key): string {
  const value = obj[key];
  if (typeof value !== 'string' || value.trim() === '') fail(`${label} is required`);
  return value.trim();
}

function isObject(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value);
}

/** Validates the body of POST /shipments (and the rows of POST /import). */
export function validateShipmentInput(body: unknown): ShipmentInput {
  if (!isObject(body)) fail('body must be a JSON object');

  const trackingNumber = requireString(body, 'tracking_number').toUpperCase();

  const carrier = requireString(body, 'carrier').toUpperCase();
  if (!CARRIERS.includes(carrier as Carrier)) fail(`carrier must be one of ${CARRIERS.join(', ')}`);

  const serviceLevel = body.service_level ?? 'standard';
  if (typeof serviceLevel !== 'string' || !SERVICE_LEVELS.includes(serviceLevel as ServiceLevel)) {
    fail(`service_level must be one of ${SERVICE_LEVELS.join(', ')}`);
  }

  const r = body.recipient;
  if (!isObject(r)) fail('recipient is required');
  const recipient: Recipient = {
    name: requireString(r, 'name', 'recipient.name'),
    street: requireString(r, 'street', 'recipient.street'),
    zip: requireString(r, 'zip', 'recipient.zip'),
    city: requireString(r, 'city', 'recipient.city'),
    country: typeof r.country === 'string' && r.country.trim() !== '' ? r.country.trim().toUpperCase() : 'AT',
    ...(typeof r.phone === 'string' && r.phone.trim() !== '' ? { phone: r.phone.trim() } : {}),
  };

  return { trackingNumber, carrier: carrier as Carrier, serviceLevel: serviceLevel as ServiceLevel, recipient };
}
