// Ported from logistik-core (lib/carriers/codes.js), 2024.
// Old carrier codes used by the warehouse terminals -> current carrier codes.
const LEGACY_CARRIERS: Record<string, string> = {
  OEPOST: 'ATP',
  POST: 'ATP',
  ATP: 'ATP',
  DHLDE: 'DHL',
  DHL: 'DHL',
  DPDAT: 'DPD',
  DPD: 'DPD',
  GLSAT: 'GLS',
  GLS: 'GLS',
  UPSAT: 'UPS',
  UPS: 'UPS',
};

export function mapLegacyCarrier(code: string): string {
  const key = code.trim().toUpperCase();
  return LEGACY_CARRIERS[key] ?? key;
}
