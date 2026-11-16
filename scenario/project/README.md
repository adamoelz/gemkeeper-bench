# parcel-tracker

Small HTTP service that tracks outgoing parcels of the Vienna warehouse: shipments are
created when a parcel is labelled, carriers report tracking events, and every `delivered`
or `exception` event is forwarded to the ERP.

Node 24 runs the TypeScript sources directly (type stripping), so there is no build step.

## Run

```
npm start            # listens on PORT (default 3000)
npm test             # node:test, all files in test/
```

Configuration lives in `config/default.json`. Environment overrides: `PORT`, `DATA_FILE`, `ERP_URL`.

## API

| Method | Path | |
|---|---|---|
| GET | /health | liveness |
| POST | /shipments | create a shipment |
| GET | /shipments | list (filters: `carrier`, `status`, `limit`) |
| GET | /shipments/:id | one shipment incl. ETA and events |
| POST | /shipments/:id/events | add a tracking event |
| POST | /import | bulk import (legacy CSV format) |

## ERP

Tracking events are forwarded to the ERP event intake (see `docs/erp-api.md`).
For local development use the ERP sandbox at `http://localhost:8080/events`.
