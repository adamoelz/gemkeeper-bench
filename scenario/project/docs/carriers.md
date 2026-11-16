# Carriers

| Code | Carrier | Tracking number format (as printed on our labels) |
|---|---|---|
| ATP | Österreichische Post | UPU S10: 2 letters, 8 digits, 1 check digit, `AT` (e.g. `RR123456785AT`) |
| DHL | DHL Paket | 12–20 digits, or `JJD` + digits |
| DPD | DPD Austria | 14 digits, or 20 digits incl. depot prefix |
| GLS | GLS Austria | 11–12 digits |
| UPS | UPS | `1Z` + 16 alphanumerics |

Carrier codes from the old warehouse terminals (`OEPOST`, `DHLDE`, ...) are mapped in
`src/legacy/carrierCodes.ts`.

## UPU S10 check digit (ATP)

An S10 number looks like `RR123456785AT`: service indicator (2 letters), serial number
(8 digits), check digit (1 digit), country code (2 letters, `AT` for Austrian Post).

To compute the check digit from the 8 serial digits:

1. Multiply the digits by the weights `8 6 4 2 3 5 9 7` (left to right) and add the products.
2. Take the sum modulo 11 and compute `11 - remainder`.
3. If the result is 10, the check digit is 0. If it is 11, the check digit is 5.
   Otherwise the result is the check digit.

Example: serial `12345678` → 1·8 + 2·6 + 3·4 + 4·2 + 5·3 + 6·5 + 7·9 + 8·7 = 204,
204 mod 11 = 6, 11 − 6 = 5 → `RR123456785AT`.

## Service levels

| Level | Meaning |
|---|---|
| economy | cheapest, no delivery promise |
| standard | default |
| express | next business day where the carrier offers it |

Transit times per carrier and level are in `src/services/eta.ts`.
