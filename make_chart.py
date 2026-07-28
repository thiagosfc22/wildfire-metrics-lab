"""Render the Portugal burnt-area vs fire-count chart.

Two measures of different scale never share a y-axis, so they get two stacked
panels on a common x-axis instead.

Outputs:
  chart.html       - interactive version (hover, light/dark, table view)
  chart-light.png  - static 1200x675 card for sharing
  chart-dark.png   - same card, dark mode

PNG export shells out to headless Chrome; if Chrome isn't installed the HTML is
still written and you can screenshot it yourself.
"""

import csv
import shutil
import subprocess
from pathlib import Path

HERE = Path(__file__).parent
DATA = HERE / "data"
BUILD = HERE / ".build"
COUNTRY = "PRT"

CHROME_CANDIDATES = [
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
    "google-chrome",
    "chromium",
]

W, PAD_L, PAD_R = 1200, 92, 44
TOP_Y, TOP_H = 168, 214          # panel A: burnt area
BOT_Y, BOT_H = 452, 116          # panel B: number of fires

INK = {
    "surface": ("#fcfcfb", "#1a1a19"),
    "primary": ("#0b0b0b", "#ffffff"),
    "secondary": ("#52514e", "#c3c2b7"),
    "muted": ("#898781", "#898781"),
    "grid": ("#e1e0d9", "#2c2c2a"),
    "axis": ("#c3c2b7", "#383835"),
    "series": ("#2a78d6", "#3987e5"),
    "accent": ("#d03b3b", "#d03b3b"),
}


def load(name):
    rows = list(csv.reader((DATA / name).open()))
    idx = rows[0].index(COUNTRY)
    out = {}
    for row in rows[1:]:
        if row and row[0] and len(row) > idx and row[idx]:
            try:
                out[int(row[0])] = float(row[idx])
            except ValueError:
                pass
    return out


def nice_top(v):
    """Round an axis maximum up to a readable step."""
    step = 10 ** (len(str(int(v))) - 1) // 2 or 1
    return ((int(v) // step) + 1) * step


def build_svg(area, fires, years, *, static):
    x0, x1 = PAD_L, W - PAD_R
    span = years[-1] - years[0]
    fx = lambda y: x0 + (y - years[0]) / span * (x1 - x0)

    a_max, f_max = nice_top(max(area.values())), nice_top(max(fires.values()))
    fy_a = lambda v: TOP_Y + TOP_H - (v / a_max) * TOP_H
    fy_f = lambda v: BOT_Y + BOT_H - (v / f_max) * BOT_H

    s = []
    add = s.append
    if static:
        add(f'<rect width="{W}" height="675" fill="var(--surface)"/>')

    # ---- headline -------------------------------------------------------
    add(
        f'<text x="{PAD_L}" y="62" fill="var(--primary)" font-size="34" '
        f'font-weight="650">Portugal had fewer wildfires in 2024 — and burnt '
        f'4× more land</text>'
    )
    add(
        f'<text x="{PAD_L}" y="98" fill="var(--secondary)" font-size="17">'
        f'Counting fires does not measure damage. Portugal, 1980–2024.</text>'
    )

    for label, y in (("Burnt area (hectares)", TOP_Y - 18), ("Number of fires", BOT_Y - 18)):
        add(
            f'<text x="{PAD_L}" y="{y}" fill="var(--secondary)" font-size="14" '
            f'font-weight="600" letter-spacing="0.04em">{label.upper()}</text>'
        )

    # ---- grid + y ticks (hairline, solid, recessive) --------------------
    for frac in (0, 0.5, 1):
        for top, height, mx, fy, fmt in (
            (TOP_Y, TOP_H, a_max, fy_a, lambda v: f"{v / 1000:,.0f}k"),
            (BOT_Y, BOT_H, f_max, fy_f, lambda v: f"{v / 1000:,.0f}k"),
        ):
            v = mx * frac
            y = fy(v)
            add(
                f'<line x1="{x0}" y1="{y:.1f}" x2="{x1}" y2="{y:.1f}" '
                f'stroke="var({"--axis" if frac == 0 else "--grid"})" stroke-width="1"/>'
            )
            add(
                f'<text x="{x0 - 12}" y="{y + 4:.1f}" fill="var(--muted)" font-size="13" '
                f'text-anchor="end" style="font-variant-numeric:tabular-nums">'
                f'{"0" if frac == 0 else fmt(v)}</text>'
            )

    # ---- x ticks --------------------------------------------------------
    for yr in range(1980, 2025, 5):
        add(
            f'<text x="{fx(yr):.1f}" y="{BOT_Y + BOT_H + 26}" fill="var(--muted)" '
            f'font-size="13" text-anchor="middle" '
            f'style="font-variant-numeric:tabular-nums">{yr}</text>'
        )

    # ---- series ---------------------------------------------------------
    for series, fy, top, height in ((area, fy_a, TOP_Y, TOP_H), (fires, fy_f, BOT_Y, BOT_H)):
        pts = [(fx(y), fy(series[y])) for y in years]
        line = "M" + " L".join(f"{x:.1f},{y:.1f}" for x, y in pts)
        add(f'<path d="{line} L{pts[-1][0]:.1f},{top + height} L{pts[0][0]:.1f},'
            f'{top + height} Z" fill="var(--series)" fill-opacity="0.10"/>')
        add(f'<path d="{line}" fill="none" stroke="var(--series)" stroke-width="2" '
            f'stroke-linejoin="round" stroke-linecap="round"/>')

    # ---- emphasis: the 2023 -> 2024 divergence --------------------------
    for series, fy, dy, label in (
        (area, fy_a, -18, "+299% area"),
        (fires, fy_f, -16, "−17% fires"),
    ):
        p, c = (fx(2023), fy(series[2023])), (fx(2024), fy(series[2024]))
        add(f'<path d="M{p[0]:.1f},{p[1]:.1f} L{c[0]:.1f},{c[1]:.1f}" fill="none" '
            f'stroke="var(--accent)" stroke-width="3" stroke-linecap="round"/>')
        for cx, cy in (p, c):
            add(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="4.5" fill="var(--accent)" '
                f'stroke="var(--surface)" stroke-width="2"/>')
        add(f'<text x="{c[0] - 8:.1f}" y="{min(p[1], c[1]) + dy:.1f}" fill="var(--accent)" '
            f'font-size="15" font-weight="650" text-anchor="end">{label}</text>')

    # ---- direct label on the record season ------------------------------
    px, py = fx(2017), fy_a(area[2017])
    add(f'<circle cx="{px:.1f}" cy="{py:.1f}" r="4" fill="var(--series)" '
        f'stroke="var(--surface)" stroke-width="2"/>')
    add(f'<text x="{px:.1f}" y="{py - 14:.1f}" fill="var(--secondary)" font-size="14" '
        f'text-anchor="middle">2017 · 539,921 ha</text>')

    # ---- footer ---------------------------------------------------------
    add(f'<line x1="{PAD_L}" y1="612" x2="{x1}" y2="612" stroke="var(--grid)" stroke-width="1"/>')
    add(f'<text x="{PAD_L}" y="639" fill="var(--secondary)" font-size="14">'
        f'Over 45 years the two series correlate at just r = 0.42.</text>')
    add(f'<text x="{x1}" y="639" fill="var(--muted)" font-size="13" text-anchor="end">'
        f'Source: EFFIS · Copernicus EMS / European Commission JRC</text>')

    box = f'0 0 {W} 675'
    return f'<svg viewBox="{box}" xmlns="http://www.w3.org/2000/svg" font-family="system-ui, -apple-system, sans-serif">{"".join(s)}</svg>'


def css():
    light = "".join(f"  --{k}: {v[0]};\n" for k, v in INK.items())
    dark = "".join(f"    --{k}: {v[1]};\n" for k, v in INK.items())
    return f""":root {{ color-scheme: light dark; }}
.viz {{
  color-scheme: light;
{light}  background: var(--surface);
}}
@media (prefers-color-scheme: dark) {{
  :root:where(:not([data-theme="light"])) .viz {{
    color-scheme: dark;
{dark}  }}
}}
:root[data-theme="dark"] .viz {{
  color-scheme: dark;
{dark}}}
body {{ margin: 0; font-family: system-ui, -apple-system, sans-serif; }}
.viz {{ max-width: 1200px; margin: 0 auto; }}
.viz svg {{ display: block; width: 100%; height: auto; }}
table {{ border-collapse: collapse; width: 100%; font-size: 13px;
  font-variant-numeric: tabular-nums; color: var(--primary); }}
th, td {{ text-align: right; padding: 5px 10px; border-bottom: 1px solid var(--grid); }}
th:first-child, td:first-child {{ text-align: left; }}
summary {{ cursor: pointer; color: var(--secondary); font-size: 14px;
  padding: 16px 0 8px; }}
"""


def main():
    area, fires = load("effis_burnt_area_ha.csv"), load("effis_number_of_fires.csv")
    years = sorted(set(area) & set(fires))

    rows = "".join(
        f"<tr><td>{y}</td><td>{area[y]:,.0f}</td><td>{fires[y]:,.0f}</td></tr>"
        for y in reversed(years)
    )
    table = (
        "<details><summary>Table view — every value in the chart</summary>"
        "<table><thead><tr><th>Year</th><th>Burnt area (ha)</th>"
        f"<th>Fires</th></tr></thead><tbody>{rows}</tbody></table></details>"
    )

    svg = build_svg(area, fires, years, static=False)
    (HERE / "chart.html").write_text(
        f"<!doctype html><meta charset=utf-8><title>Portugal wildfires 1980–2024</title>"
        f"<style>{css()}body{{padding:24px;background:var(--surface)}}</style>"
        f'<div class="viz">{svg}{table}</div>'
    )

    # Static cards. The theme is stamped on <html> so headless Chrome renders the
    # chosen mode instead of inheriting the OS preference.
    BUILD.mkdir(exist_ok=True)
    card = build_svg(area, fires, years, static=True)
    for theme in ("light", "dark"):
        (BUILD / f"card-{theme}.html").write_text(
            f'<!doctype html><html data-theme="{theme}"><meta charset=utf-8>'
            f"<title>card</title>"
            f"<style>{css()}body{{margin:0}}.viz{{max-width:none}}</style>"
            f'<div class="viz" style="width:1200px">{card}</div></html>'
        )
    print(f"chart.html written ({len(years)} years)")
    export_pngs()


def export_pngs() -> None:
    chrome = next(
        (c for c in CHROME_CANDIDATES if Path(c).exists() or shutil.which(c)), None
    )
    if not chrome:
        print("no Chrome/Chromium found - skipping PNG export, open chart.html instead")
        return
    for theme in ("light", "dark"):
        out = HERE / f"chart-{theme}.png"
        subprocess.run(
            [
                chrome, "--headless", "--disable-gpu", "--hide-scrollbars",
                "--force-color-profile=srgb", f"--screenshot={out}",
                "--window-size=1200,675", (BUILD / f"card-{theme}.html").as_uri(),
            ],
            check=True, capture_output=True,
        )
        print(f"{out.name}: {out.stat().st_size:,} bytes")


if __name__ == "__main__":
    main()
