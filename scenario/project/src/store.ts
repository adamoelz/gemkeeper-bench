import { randomUUID } from 'node:crypto';
import { existsSync, mkdirSync, readFileSync, writeFileSync } from 'node:fs';
import path from 'node:path';
import type { EventType, Shipment, TrackingEvent } from './types.ts';

interface StoreData {
  shipments: Shipment[];
  events: TrackingEvent[];
}

export interface ListFilter {
  carrier?: string;
  status?: string;
  limit?: number;
}

export type NewShipment = Omit<Shipment, 'id' | 'status' | 'createdAt'>;

/**
 * In-memory store, persisted as one JSON file (data/store.json).
 * Without a file path it is memory-only (used by the tests).
 */
export class Store {
  private shipments = new Map<string, Shipment>();
  private events = new Map<string, TrackingEvent[]>();
  private file: string | undefined;

  constructor(file?: string) {
    this.file = file;
    if (file && existsSync(file)) this.load(file);
  }

  private load(file: string): void {
    const data = JSON.parse(readFileSync(file, 'utf8')) as StoreData;
    for (const shipment of data.shipments) this.shipments.set(shipment.id, shipment);
    for (const event of data.events) {
      const list = this.events.get(event.shipmentId) ?? [];
      list.push(event);
      this.events.set(event.shipmentId, list);
    }
  }

  /** Writes the whole store to disk. Called after every mutation. */
  save(): void {
    if (!this.file) return;
    const data: StoreData = {
      shipments: [...this.shipments.values()],
      events: [...this.events.values()].flat(),
    };
    mkdirSync(path.dirname(this.file), { recursive: true });
    writeFileSync(this.file, JSON.stringify(data, null, 2));
  }

  addShipment(input: NewShipment, now: Date = new Date()): Shipment {
    const shipment: Shipment = {
      ...input,
      id: `shp_${randomUUID().slice(0, 8)}`,
      status: 'created',
      createdAt: now.toISOString(),
    };
    this.shipments.set(shipment.id, shipment);
    this.events.set(shipment.id, [
      { id: `evt_${randomUUID().slice(0, 8)}`, shipmentId: shipment.id, type: 'created', at: shipment.createdAt },
    ]);
    this.save();
    return shipment;
  }

  getShipment(id: string): Shipment | undefined {
    return this.shipments.get(id);
  }

  findByTrackingNumber(trackingNumber: string): Shipment | undefined {
    for (const shipment of this.shipments.values()) {
      if (shipment.trackingNumber === trackingNumber) return shipment;
    }
    return undefined;
  }

  listShipments(filter: ListFilter = {}): Shipment[] {
    let result = [...this.shipments.values()];
    if (filter.carrier) result = result.filter((s) => s.carrier === filter.carrier);
    if (filter.status) result = result.filter((s) => s.status === filter.status);
    result.sort((a, b) => b.createdAt.localeCompare(a.createdAt));
    return filter.limit ? result.slice(0, filter.limit) : result;
  }

  addEvent(
    shipmentId: string,
    type: EventType,
    fields: { at?: string; location?: string; note?: string } = {},
  ): TrackingEvent {
    const shipment = this.shipments.get(shipmentId);
    if (!shipment) throw new Error(`unknown shipment ${shipmentId}`);
    const event: TrackingEvent = {
      id: `evt_${randomUUID().slice(0, 8)}`,
      shipmentId,
      type,
      at: fields.at ?? new Date().toISOString(),
      ...(fields.location ? { location: fields.location } : {}),
      ...(fields.note ? { note: fields.note } : {}),
    };
    const list = this.events.get(shipmentId) ?? [];
    list.push(event);
    this.events.set(shipmentId, list);
    shipment.status = type;
    this.save();
    return event;
  }

  eventsFor(shipmentId: string): TrackingEvent[] {
    return [...(this.events.get(shipmentId) ?? [])];
  }
}
