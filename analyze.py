"""Does 'number of wildfires' tell you how much land burnt?

Correlates the two EFFIS series (1980-2024) per country and lists the years
where the two metrics moved in opposite directions. Run fetch_effis.py first.
"""

import csv
import math
from pathlib import Path

DATA = Path(__file__).parent / "data"
FOCUS = ["PRT", "ESP", "FRA", "ITA", "GRC"]


def load(name: str) -> dict[str, dict[int, float]]:
    rows = list(csv.reader((DATA / name).open()))
    header, out = rows[0], {}
    for row in rows[1:]:
        if not row or not row[0]:
            continue
        year = int(row[0])
        for i, country in enumerate(header[1:], start=1):
            cell = row[i] if i < len(row) else ""
            if cell:
                try:
                    out.setdefault(country, {})[year] = float(cell)
                except ValueError:
                    pass  # footnote rows
    return out


def pearson(xs: list[float], ys: list[float]) -> float:
    n = len(xs)
    mx, my = sum(xs) / n, sum(ys) / n
    num = sum((a - mx) * (b - my) for a, b in zip(xs, ys))
    den = math.sqrt(sum((a - mx) ** 2 for a in xs) * sum((b - my) ** 2 for b in ys))
    return num / den if den else float("nan")


def main() -> None:
    area, fires = load("effis_burnt_area_ha.csv"), load("effis_number_of_fires.csv")

    print("Correlation between number of fires and burnt area, 1980-2024\n")
    print(f"{'country':<9}{'years':>6}{'r':>8}   interpretation")
    for c in FOCUS:
        years = sorted(set(area.get(c, {})) & set(fires.get(c, {})))
        r = pearson([fires[c][y] for y in years], [area[c][y] for y in years])
        note = "none" if abs(r) < 0.3 else "weak" if abs(r) < 0.5 else "moderate"
        print(f"{c:<9}{len(years):>6}{r:>8.2f}   {note}")

    print("\nYears where fires FELL but burnt area ROSE (>5% / >30%, since 2005)\n")
    for c in FOCUS:
        years = sorted(set(area.get(c, {})) & set(fires.get(c, {})))
        for prev, cur in zip(years, years[1:]):
            if cur < 2005:
                continue
            d_fires = (fires[c][cur] - fires[c][prev]) / fires[c][prev]
            d_area = (area[c][cur] - area[c][prev]) / area[c][prev]
            if d_fires < -0.05 and d_area > 0.30:
                print(
                    f"  {c} {prev}->{cur}:  fires {d_fires * 100:+6.1f}%   "
                    f"area {d_area * 100:+8.1f}%   "
                    f"({area[c][prev]:,.0f} -> {area[c][cur]:,.0f} ha)"
                )

    print("\nLargest single-country seasons on record\n")
    worst = sorted(
        ((v, c, y) for c, series in area.items() for y, v in series.items()), reverse=True
    )
    for v, c, y in worst[:8]:
        n = fires.get(c, {}).get(y)
        tail = f" in {n:,.0f} fires" if n else ""
        print(f"  {c} {y}: {v:>9,.0f} ha{tail}")


if __name__ == "__main__":
    main()
