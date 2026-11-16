export type Carrier = 'ATP' | 'DHL' | 'DPD' | 'GLS' | 'UPS';
export type ServiceLevel = 'economy' | 'standard' | 'express';
export type EventType = 'created' | 'picked_up' | 'in_transit' | 'out_for_delivery' | 'delivered' | 'exception';

export const CARRIERS: readonly Carrier[] = ['ATP', 'DHL', 'DPD', 'GLS', 'UPS'];
export const SERVICE_LEVELS: readonly ServiceLevel[] = ['economy', 'standard', 'express'];
export const EVENT_TYPES: readonly EventType[] = [
  'created',
  'picked_up',
  'in_transit',
  'out_for_delivery',
  'delivered',
  'exception',
];

export interface Recipient {
  name: string;
  street: string;
  zip: string;
  city: string;
  country: string;
  phone?: string;
}

export interface Shipment {
  id: string;
  trackingNumber: string;
  carrier: Carrier;
  serviceLevel: ServiceLevel;
  recipient: Recipient;
  status: EventType;
  /** ISO-8601, UTC */
  createdAt: string;
}

export interface TrackingEvent {
  id: string;
  shipmentId: string;
  type: EventType;
  /** ISO-8601, UTC */
  at: string;
  location?: string;
  note?: string;
}
