# ERP event intake API

Maintained by the ERP team. Questions: #erp-integration.

The ERP receives shipment tracking events from parcel-tracker and updates the order status
that customer service sees.

## Endpoints

| Environment | URL |
|---|---|
| Sandbox | `http://localhost:8080/events` (local container) |
| Staging | `https://erp-staging.internal/intake/events` |
| Production | `https://erp.internal/intake/events` |

## Request

```
POST /events
Content-Type: application/json
```

Body: one tracking event.

| Field | Type | Required | Notes |
|---|---|---|---|
| `event_id` | string | yes | Unique per event. |
| `shipment_id` | string | yes | parcel-tracker shipment id. |
| `tracking_number` | string | yes | As printed on the label. |
| `carrier` | string | yes | `ATP`, `DHL`, `DPD`, `GLS`, `UPS`. |
| `event_type` | string | yes | `delivered` or `exception`. Other types are ignored. |
| `occurred_at` | string | yes | ISO-8601 with timezone, e.g. `2026-11-12T09:14:03.000Z`. |
| `note` | string | no | Free text from the carrier, max 500 chars. |

Example:

```json
{
  "event_id": "evt_4f1c9a2b",
  "shipment_id": "shp_7d3e0c11",
  "tracking_number": "RR123456785AT",
  "carrier": "ATP",
  "event_type": "delivered",
  "occurred_at": "2026-11-12T09:14:03.000Z"
}
```

## Responses

| Status | Meaning |
|---|---|
| 202 | Accepted. Processing is asynchronous. |
| 400 | Invalid body. The response contains `{ "errors": [...] }` with the offending fields. |
| 401 | Missing or invalid authentication. |
| 422 | Valid JSON, but the payload can't be processed. |
| 5xx | Temporary problem. The sender should retry. |

## Authentication

Request signing with a shared secret is being rolled out (ERP-1182). The secret is
distributed by the ERP team; it's never sent in plain text.

## Changelog

- 2026-09: `event_type` replaces the old `type` field (still accepted until 2026-12-31).
- 2026-06: `note` added.
- 2026-02: Staging moved to `erp-staging.internal`.
