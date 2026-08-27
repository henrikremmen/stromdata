import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import requests
from dotenv import load_dotenv


ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT / ".env")

TOKEN = os.getenv("AGVA_TOKEN")
CUSTOMER_ID = os.getenv("CUSTOMER_ID")
DELIVERY_POINT_ID = os.getenv("DELIVERY_POINT_ID")

if not TOKEN:
    raise RuntimeError("AGVA_TOKEN mangler i .env")
if not CUSTOMER_ID:
    raise RuntimeError("CUSTOMER_ID mangler i .env")
if not DELIVERY_POINT_ID:
    raise RuntimeError("DELIVERY_POINT_ID mangler i .env")


API_ROOT = "https://minside2.agva.no/api/v1/Retail"
HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Accept": "application/json",
}


def _get(url, params):
    response = requests.get(
        url,
        params=params,
        headers=HEADERS,
        timeout=20,
    )

    if not response.ok:
        print(f"API-feil: {response.status_code}")
        print(response.text)

    response.raise_for_status()
    return response.json()


def get_consumption(start, end, resolution="Hour"):
    """Hent forbruksmålinger fra Agva."""
    url = (
        f"{API_ROOT}/customers/{CUSTOMER_ID}/"
        f"delivery-points/{DELIVERY_POINT_ID}/"
        "metering-values/Consumption"
    )
    params = {
        "fromDateTime": start.astimezone(timezone.utc).isoformat(),
        "toDateTime": end.astimezone(timezone.utc).isoformat(),
        "resolution": resolution,
        "unit": "WattHours",
        "contractType": "Power",
    }
    return _get(url, params)


def get_spot_prices(start, end, resolution="Hour", price_area="NO3"):
    """Hent spotpriser for et norsk prisområde fra Agva."""
    # Spotpris-endepunktet returnerer ingen punkter når grensene inneholder
    # minutter/sekunder. Utvid derfor intervallet til hele klokketimer.
    start = start.replace(minute=0, second=0, microsecond=0)
    if end.minute or end.second or end.microsecond:
        end = end.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)

    url = f"{API_ROOT}/spot-prices/{price_area}"
    params = {
        "fromDateTime": start.astimezone(timezone.utc).isoformat(),
        "toDateTime": end.astimezone(timezone.utc).isoformat(),
        "resolution": resolution,
    }
    return _get(url, params)


def to_kwh(value, data):
    """Konverter en måleverdi fra API-responsens enhet til kWh."""
    multipliers = {
        "None": 1,
        "Deca": 10,
        "Hecto": 100,
        "Kilo": 1_000,
        "Mega": 1_000_000,
        "Giga": 1_000_000_000,
    }

    unit = data.get("unit")
    multiplier = data.get("multiplier")

    if unit != "WattHours":
        raise ValueError(f"Uventet enhet: {unit}")

    factor = multipliers.get(multiplier)
    if factor is None:
        raise ValueError(f"Ukjent multiplier: {multiplier}")

    return float(value) * factor / 1000


def format_time(reading):
    """Konverter UTC-tidsstempler til norsk lokal tid."""
    norway = ZoneInfo("Europe/Oslo")
    start_time = datetime.fromisoformat(
        reading["fromDateTime"]
    ).astimezone(norway)
    end_time = datetime.fromisoformat(
        reading["toDateTime"]
    ).astimezone(norway)
    return f"{start_time:%d.%m.%Y %H:%M}–{end_time:%H:%M}"


def main():
    now = datetime.now(timezone.utc)
    start = now - timedelta(days=3)
    data = get_consumption(start, now)
    readings = data.get("intervalReadings", [])

    if not readings:
        raise RuntimeError("Ingen målinger funnet.")

    latest = max(readings, key=lambda reading: reading["toDateTime"])

    print()
    print("Nyeste tilgjengelige måling")
    print("---------------------------")
    print(f"Forbruk:  {to_kwh(latest['value'], data):.3f} kWh")
    print(f"Tid:      {format_time(latest)}")
    print(f"Kvalitet: {latest.get('quality', 'Ukjent')}")

    actual_readings = [
        reading
        for reading in readings
        if reading.get("quality") != "Estimated"
    ]
    if actual_readings:
        latest_actual = max(
            actual_readings,
            key=lambda reading: reading["toDateTime"],
        )
        if latest_actual != latest:
            print()
            print("Nyeste ikke-estimerte måling")
            print("----------------------------")
            print(
                f"Forbruk:  "
                f"{to_kwh(latest_actual['value'], data):.3f} kWh"
            )
            print(f"Tid:      {format_time(latest_actual)}")
            print(
                f"Kvalitet: "
                f"{latest_actual.get('quality', 'Ukjent')}"
            )


if __name__ == "__main__":
    main()
