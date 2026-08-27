import os
import argparse
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import matplotlib

matplotlib.use("Agg")
import matplotlib.dates as mdates
import matplotlib.pyplot as plt

from getdata import get_consumption, get_spot_prices, to_kwh


NORWAY = ZoneInfo("Europe/Oslo")
PRICE_AREA = os.getenv("PRICE_AREA", "NO3")
VAT_FACTOR = 1.25
ROOT = Path(__file__).resolve().parent


def main(output_file):
    end = datetime.now(NORWAY)
    start = end - timedelta(days=7)

    consumption_data = get_consumption(
        start,
        end,
        resolution="Hour",
    )
    price_data = get_spot_prices(
        start,
        end,
        resolution="Hour",
        price_area=PRICE_AREA,
    )

    readings = consumption_data.get("intervalReadings", [])
    prices = price_data.get("prices", [])

    if not readings:
        raise RuntimeError("Ingen forbruksmålinger funnet.")
    if not prices:
        raise RuntimeError("Ingen spotpriser funnet.")

    # Agva-prisene er oppgitt i NOK/kWh ekskl. mva.
    # Vi bruker pris inkl. 25 % mva. for NO3.
    price_by_time = {
        datetime.fromisoformat(price["fromDate"]).astimezone(NORWAY):
        float(price["price"]) * VAT_FACTOR
        for price in prices
    }

    consumption_by_time = {
        datetime.fromisoformat(reading["fromDateTime"]).astimezone(NORWAY):
        to_kwh(reading["value"], consumption_data)
        for reading in readings
    }

    price_rows = sorted(price_by_time.items())
    consumption_rows = sorted(consumption_by_time.items())

    # Bare timer som har både forbruk og spotpris kan få en kostnad.
    common_times = sorted(price_by_time.keys() & consumption_by_time.keys())
    if not common_times:
        raise RuntimeError(
            "Fant ingen klokketimer med både forbruk og spotpris."
        )

    cost_values = [
        consumption_by_time[time] * price_by_time[time]
        for time in common_times
    ]

    figure, axes = plt.subplots(
        3,
        1,
        figsize=(13, 10),
        sharex=True,
    )

    price_times, price_values = zip(*price_rows)
    axes[0].step(
        price_times,
        [price * 100 for price in price_values],
        where="post",
        color="tab:orange",
    )
    axes[0].set_title(f"Spotpris siste 7 dager ({PRICE_AREA})")
    axes[0].set_ylabel("øre/kWh inkl. mva.")

    consumption_times, consumption_values = zip(*consumption_rows)
    axes[1].bar(
        consumption_times,
        consumption_values,
        width=1 / 24 * 0.85,
        color="tab:blue",
    )
    axes[1].set_title("Forbruk siste 7 dager")
    axes[1].set_ylabel("kWh per time")

    axes[2].bar(
        common_times,
        cost_values,
        width=1 / 24 * 0.85,
        color="tab:green",
    )
    axes[2].set_title("Spotkostnad siste 7 dager")
    axes[2].set_ylabel("kr per time")
    axes[2].set_xlabel("Dato og klokkeslett")

    for axis in axes:
        axis.grid(axis="y", alpha=0.3)

    axes[2].xaxis.set_major_locator(mdates.DayLocator())
    axes[2].xaxis.set_major_formatter(mdates.DateFormatter("%d.%m", tz=NORWAY))
    axes[2].xaxis.set_minor_locator(mdates.HourLocator(byhour=[6, 12, 18]))
    axes[2].xaxis.set_minor_formatter(mdates.DateFormatter("%H", tz=NORWAY))
    axes[2].tick_params(axis="x", which="minor", labelsize=8)

    total_kwh = sum(consumption_by_time[time] for time in common_times)
    total_cost = sum(cost_values)
    figure.patch.set_facecolor("#000000")
    for axis in axes:
        axis.set_facecolor("#000000")
        axis.tick_params(colors="#dddddd")
        axis.xaxis.label.set_color("#dddddd")
        axis.yaxis.label.set_color("#dddddd")
        axis.title.set_color("#ffffff")
        for spine in axis.spines.values():
            spine.set_color("#555555")

    figure.suptitle(
        f"{total_kwh:.1f} kWh · {total_cost:.2f} kr i spotkostnad",
        color="#ffffff",
        fontsize=14,
    )
    figure.tight_layout()

    output_file.parent.mkdir(parents=True, exist_ok=True)
    temporary_file = output_file.with_name(f"{output_file.stem}.tmp.png")
    figure.savefig(
        temporary_file,
        dpi=150,
        bbox_inches="tight",
        facecolor=figure.get_facecolor(),
    )
    plt.close(figure)
    temporary_file.replace(output_file)
    print(f"Lagret graf: {output_file}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "public" / "stromdata.png",
    )
    arguments = parser.parse_args()
    main(arguments.output.resolve())
