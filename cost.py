from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from getdata import (
    get_consumption,
    get_spot_prices,
    to_kwh,
)


NORWAY = ZoneInfo("Europe/Oslo")

now = datetime.now(NORWAY)
start = now - timedelta(days=7)


# --------------------------------------------------
# Hent forbruk
# --------------------------------------------------

consumption_data = get_consumption(
    start,
    now,
    resolution="Hour",
)

consumption = consumption_data.get(
    "intervalReadings",
    [],
)


# --------------------------------------------------
# Hent spotpriser
# --------------------------------------------------

price_data = get_spot_prices(
    start,
    now,
    resolution="Hour",
    price_area="NO3",
)

prices = price_data.get("prices", [])


print("Currency:", price_data.get("currencyCode"))
print("Antall forbrukspunkter:", len(consumption))
print("Antall prispunkter:", len(prices))

if prices:
    print("Eksempel spotpris:")
    print(prices[-1])


# --------------------------------------------------
# Lag dictionary over priser per tidspunkt
# --------------------------------------------------

price_by_time = {}

for price in prices:
    dt = datetime.fromisoformat(
        price["fromDate"]
    ).astimezone(NORWAY)

    # Agva spotpris ser ut til å være eks. mva.
    # For NO3 legges 25 % mva på.
    price_nok_kwh = float(price["price"]) * 1.25

    price_by_time[dt] = price_nok_kwh


# --------------------------------------------------
# Match forbruk og spotpris
# --------------------------------------------------

rows = []

for reading in consumption:
    dt = datetime.fromisoformat(
        reading["fromDateTime"]
    ).astimezone(NORWAY)

    price = price_by_time.get(dt)

    if price is None:
        continue

    kwh = to_kwh(
        reading["value"],
        consumption_data,
    )

    cost = kwh * price

    rows.append({
        "time": dt,
        "kwh": kwh,
        "price": price,
        "cost": cost,
        "quality": reading.get("quality"),
    })


# --------------------------------------------------
# Resultat
# --------------------------------------------------

total_kwh = sum(
    row["kwh"]
    for row in rows
)

total_cost = sum(
    row["cost"]
    for row in rows
)


print()
print("Siste 7 dager")
print("-------------")
print(f"Forbruk:      {total_kwh:.2f} kWh")
print(f"Spotkostnad:  {total_cost:.2f} kr")

if total_kwh:
    avg_price = total_cost / total_kwh

    print(
        f"Snittpris:    "
        f"{avg_price * 100:.1f} øre/kWh"
    )


print()
print("Siste timer")
print("------------")

for row in rows[-10:]:
    print(
        f"{row['time']:%d.%m %H:%M}  "
        f"{row['kwh']:.3f} kWh  "
        f"{row['price'] * 100:6.1f} øre/kWh  "
        f"{row['cost']:.3f} kr"
    )