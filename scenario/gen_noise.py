"""Generates the two large "noise" files of the toy project (deterministic, seeded).

    python bench/scenario/gen_noise.py

Writes project/data/fixtures/shipments.sample.json and project/logs/staging-2026-11-12.log.
They exist so the scripted session reads big files, like real sessions do.
"""
import json
import random
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent / "project"
rng = random.Random(20261112)

FIRST = ["Anna", "Maria", "Lukas", "Elias", "Lena", "Sophie", "Jakob", "Felix", "Laura", "David",
         "Sarah", "Paul", "Hannah", "Tobias", "Julia", "Florian", "Katharina", "Stefan", "Theresa", "Michael"]
LAST = ["Huber", "Gruber", "Wagner", "Müller", "Pichler", "Steiner", "Moser", "Mayer", "Hofer", "Leitner",
        "Berger", "Fuchs", "Eder", "Fischer", "Schmid", "Winkler", "Weber", "Schwarz", "Maier", "Reiter"]
STREETS = ["Mariahilfer Straße", "Landstraßer Hauptstraße", "Herrengasse", "Getreidegasse", "Wiener Straße",
           "Hauptplatz", "Bahnhofstraße", "Linzer Gasse", "Kirchengasse", "Annenstraße", "Schillerstraße"]
CITIES = [("1060", "Wien"), ("1030", "Wien"), ("1100", "Wien"), ("8010", "Graz"), ("4020", "Linz"),
          ("5020", "Salzburg"), ("6020", "Innsbruck"), ("9020", "Klagenfurt"), ("3100", "St. Pölten"),
          ("7000", "Eisenstadt"), ("6900", "Bregenz")]
LOCATIONS = ["Wien Inzersdorf", "Wien Hietzing Zustellbasis", "Graz Puntigam", "Linz Hafen", "Salzburg Hbf",
             "Allhaming Logistikzentrum", "Hagenbrunn Verteilzentrum", "Innsbruck Rossau", "Klagenfurt Ost"]
EXCEPTION_NOTES = [
    "Empfänger nicht angetroffen, Benachrichtigung hinterlegt",
    "Adresse unvollständig, Rückfrage beim Versender",
    "Paket beschädigt, Nachverpackung im Verteilzentrum",
    "Annahme verweigert",
    "Zustellung wegen Witterung verzögert",
    "Hausnummer nicht auffindbar",
]
SERVICE = ["standard"] * 6 + ["express"] * 2 + ["economy"] * 2


def s10_check(serial: str) -> int:
    weights = [8, 6, 4, 2, 3, 5, 9, 7]
    r = 11 - sum(int(d) * w for d, w in zip(serial, weights)) % 11
    return 0 if r == 10 else 5 if r == 11 else r


def tracking(carrier: str, bad_check: bool = False) -> str:
    if carrier == "ATP":
        serial = "".join(rng.choice("0123456789") for _ in range(8))
        check = s10_check(serial)
        if bad_check:
            check = (check + rng.randint(1, 9)) % 10
        return rng.choice(["RR", "RX", "CX", "LX"]) + serial + str(check) + "AT"
    if carrier == "DHL":
        return "JJD" + "".join(rng.choice("0123456789") for _ in range(15))
    if carrier == "DPD":
        return "".join(rng.choice("0123456789") for _ in range(14))
    if carrier == "GLS":
        return "".join(rng.choice("0123456789") for _ in range(11))
    return "1Z" + "".join(rng.choice("0123456789ABCDEFGHJKLMNPRSTUVWXYZ") for _ in range(16))


def recipient() -> dict:
    zip_, city = rng.choice(CITIES)
    r = {
        "name": f"{rng.choice(FIRST)} {rng.choice(LAST)}",
        "street": f"{rng.choice(STREETS)} {rng.randint(1, 140)}",
        "zip": zip_,
        "city": city,
        "country": "AT",
    }
    if rng.random() < 0.6:
        r["phone"] = f"+43 6{rng.randint(50, 99)} {rng.randint(1000000, 9999999)}"
    return r


def gen_fixture(n: int = 70) -> list[dict]:
    bad = set(rng.sample(range(n), 7))
    start = datetime(2026, 11, 2, 6, 0, tzinfo=timezone.utc)
    rows = []
    for i in range(n):
        carrier = rng.choices(["ATP", "DHL", "DPD", "GLS", "UPS"], weights=[40, 25, 15, 10, 10])[0]
        if i in bad:
            carrier = "ATP"
        created = start + timedelta(minutes=rng.randint(0, 60 * 24 * 9))
        rows.append({
            "tracking_number": tracking(carrier, bad_check=i in bad),
            "carrier": carrier,
            "service_level": rng.choice(SERVICE),
            "recipient": recipient(),
            "created_at": created.strftime("%Y-%m-%dT%H:%M:%S.000Z"),
            "status": rng.choice(["created", "picked_up", "in_transit", "out_for_delivery", "delivered", "delivered"]),
        })
    return rows


def write_fixture() -> None:
    rows = gen_fixture()
    out = ROOT / "data" / "fixtures" / "shipments.sample.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    lines = ",\n".join("  " + json.dumps(r, ensure_ascii=False) for r in rows)
    out.write_text("[\n" + lines + "\n]\n", encoding="utf-8")


def write_log() -> None:
    t = datetime(2026, 11, 12, 6, 0, 0, tzinfo=timezone.utc)
    lines: list[str] = []
    shipments: list[tuple[str, str, str, dict]] = []

    def ts() -> str:
        return t.strftime("%Y-%m-%dT%H:%M:%S.") + f"{rng.randint(0, 999):03d}Z"

    def sid() -> str:
        return "shp_" + "".join(rng.choice("0123456789abcdef") for _ in range(8))

    def eid() -> str:
        return "evt_" + "".join(rng.choice("0123456789abcdef") for _ in range(8))

    lines.append(f"{ts()} INFO  parcel-tracker listening port=3000 pid=4121 node=v24.11.0")
    while len(lines) < 200:
        # Peak between 10:00 and 10:06 (morning delivery wave), quieter otherwise.
        peak = t.hour == 10 and t.minute < 6
        t += timedelta(seconds=rng.randint(2, 9) if peak else rng.randint(20, 110))
        roll = rng.random()
        if roll < 0.22 or len(shipments) < 5:
            carrier = rng.choices(["ATP", "DHL", "DPD", "GLS", "UPS"], weights=[40, 25, 15, 10, 10])[0]
            s = (sid(), tracking(carrier), carrier, recipient())
            shipments.append(s)
            lines.append(f"{ts()} INFO  http POST /shipments 201 {rng.randint(9, 41)}ms shipment={s[0]} tracking={s[1]} carrier={carrier}")
        elif roll < 0.40:
            s = rng.choice(shipments)
            lines.append(f"{ts()} INFO  http GET /shipments/{s[0]} 200 {rng.randint(2, 15)}ms")
        elif roll < 0.62:
            s = rng.choice(shipments)
            typ = rng.choice(["picked_up", "in_transit", "out_for_delivery"])
            lines.append(f"{ts()} INFO  http POST /shipments/{s[0]}/events 201 {rng.randint(5, 30)}ms")
            lines.append(f"{ts()} INFO  event shipment={s[0]} type={typ} location=\"{rng.choice(LOCATIONS)}\"")
        elif roll < (0.93 if peak else 0.84):
            s = rng.choice(shipments)
            e = eid()
            lines.append(f"{ts()} INFO  http POST /shipments/{s[0]}/events 201 {rng.randint(5, 30)}ms")
            lines.append(f"{ts()} INFO  event shipment={s[0]} type=delivered location=\"{rng.choice(LOCATIONS)}\"")
            if rng.random() < 0.12:
                lines.append(f"{ts()} WARN  erp notify failed event_id={e} err=\"Error: ERP responded 503\"")
            else:
                lines.append(f"{ts()} INFO  erp notified event_id={e} shipment_id={s[0]} type=delivered")
        elif roll < 0.90 or peak:
            s = rng.choice(shipments)
            e = eid()
            r = s[3]
            lines.append(f"{ts()} INFO  http POST /shipments/{s[0]}/events 201 {rng.randint(5, 30)}ms")
            lines.append(
                f"{ts()} INFO  event shipment={s[0]} type=exception tracking={s[1]} "
                f"note=\"{rng.choice(EXCEPTION_NOTES)}\" recipient=\"{r['name']}, {r['street']}, {r['zip']} {r['city']}\""
            )
            lines.append(f"{ts()} INFO  erp notified event_id={e} shipment_id={s[0]} type=exception")
        elif roll < 0.95:
            lines.append(f"{ts()} INFO  http GET /shipments?limit=50 200 {rng.randint(40, 380)}ms")
        else:
            lines.append(f"{ts()} INFO  http GET /health 200 1ms")
    out = ROOT / "logs" / "staging-2026-11-12.log"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    write_fixture()
    write_log()
    for p in [ROOT / "data/fixtures/shipments.sample.json", ROOT / "logs/staging-2026-11-12.log"]:
        text = p.read_text(encoding="utf-8")
        print(f"{p.relative_to(ROOT)}: {len(text.splitlines())} lines, {len(text)} chars")
