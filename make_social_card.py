"""Editorial social card for the EFFIS wildfire post.

The analytical chart lives in make_chart.py and stays dependency-free. This one
is the LinkedIn card, and it uses NASA's VIIRS night image of the Pedrógão
Grande fire — the same fire that is the 2017 peak in the data.

  python3 make_social_card.py inset    (default) ember ground + framed inset
  python3 make_social_card.py ground             satellite image full-bleed

Composition, both modes:
  - burnt area is the hero, its baseline reading as a horizon
  - number of fires is demoted to a small ash sparkline, which is the argument:
    the metric everyone quotes is the one with no colour in it

Image credit: NASA Earth Observatory image by Jesse Allen, using VIIRS
day-night band data from the Suomi National Polar-orbiting Partnership.
"""

from __future__ import annotations

import base64
import csv
import mimetypes
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).parent
DATA = HERE / "data"
BUILD = HERE / ".build"
ASSETS = HERE / "assets"
COUNTRY = "PRT"

W, H = 1200, 675
PAD = 72
BASELINE = 548          # the plot floor, which reads as a horizon
PLOT_TOP = 214

# The inset lives in the empty upper-left of the plot: burnt area stays low
# until 2003, so nothing is covered. X clears the y-axis labels at PAD.
INSET_X, INSET_Y, INSET_S = 156, 230, 158

# Sampled from the photograph: a near-black with a red bias, an ember ramp, and
# a warm grey for the series that is deliberately colourless.
GROUND = "#0a0605"
EMBER_TIP = "#ffc043"
EMBER = "#f2551c"
EMBER_DEEP = "#8c1d0e"
ASH = "#9a9089"
INK = "#fdf6f0"
INK_2 = "#bda99e"

DISPLAY = "Charter, 'Iowan Old Style', Georgia, serif"
SANS = "system-ui, -apple-system, 'Helvetica Neue', sans-serif"

CHROME_CANDIDATES = [
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
    "google-chrome",
    "chromium",
]


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


def asset(name: str) -> Path | None:
    p = ASSETS / name
    return p if p.exists() else None


def embed(path: Path) -> str:
    mime = mimetypes.guess_type(path.name)[0] or "image/jpeg"
    return f"data:{mime};base64,{base64.b64encode(path.read_bytes()).decode()}"


def photo_layer(photo: Path | None) -> str:
    """Full-bleed ground. The satellite image when we have one, an ember wash when not."""
    if photo:
        return (
            f'<image href="{embed(photo)}" x="0" y="0" width="{W}" height="{H}" '
            f'preserveAspectRatio="xMidYMid slice" filter="url(#emberDuotone)" '
            f'opacity="0.85"/>'
        )
    return (
        f'<rect width="{W}" height="{H}" fill="url(#emberGround)"/>'
        f'<ellipse cx="{W * 0.46:.0f}" cy="{H - 10}" rx="{W * 0.55:.0f}" ry="215" '
        f'fill="url(#emberBloom)"/>'
        f'<ellipse cx="{W * 0.74:.0f}" cy="{H + 18}" rx="{W * 0.34:.0f}" ry="170" '
        f'fill="url(#emberBloom)"/>'
    )


def defs(has_photo: bool) -> str:
    # A photographic ground needs a lighter scrim or the image disappears; the
    # procedural ground can take a heavy one because there is nothing to lose.
    sc = (
        (0.90, 0.74, 0.55, 0.30, 0.12) if has_photo else (0.98, 0.94, 0.78, 0.30, 0.05)
    )
    return f"""<defs>
  <linearGradient id="scrim" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0%" stop-color="{GROUND}" stop-opacity="{sc[0]}"/>
    <stop offset="46%" stop-color="{GROUND}" stop-opacity="{sc[1]}"/>
    <stop offset="72%" stop-color="{GROUND}" stop-opacity="{sc[2]}"/>
    <stop offset="86%" stop-color="{GROUND}" stop-opacity="{sc[3]}"/>
    <stop offset="100%" stop-color="{GROUND}" stop-opacity="{sc[4]}"/>
  </linearGradient>
  <linearGradient id="footerVeil" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0%" stop-color="{GROUND}" stop-opacity="0"/>
    <stop offset="70%" stop-color="{GROUND}" stop-opacity="0.30"/>
    <stop offset="100%" stop-color="{GROUND}" stop-opacity="0.62"/>
  </linearGradient>
  <filter id="textShadow" x="-10%" y="-40%" width="120%" height="180%">
    <feDropShadow dx="0" dy="1" stdDeviation="3" flood-color="{GROUND}" flood-opacity="0.95"/>
  </filter>
  <linearGradient id="areaFill" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0%" stop-color="{EMBER_TIP}" stop-opacity="0.85"/>
    <stop offset="38%" stop-color="{EMBER}" stop-opacity="0.55"/>
    <stop offset="100%" stop-color="{EMBER_DEEP}" stop-opacity="0.06"/>
  </linearGradient>
  <linearGradient id="emberGround" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0%" stop-color="#050303"/>
    <stop offset="62%" stop-color="#160806"/>
    <stop offset="100%" stop-color="#3d1008"/>
  </linearGradient>
  <radialGradient id="emberBloom">
    <stop offset="0%" stop-color="{EMBER}" stop-opacity="0.55"/>
    <stop offset="55%" stop-color="{EMBER_DEEP}" stop-opacity="0.28"/>
    <stop offset="100%" stop-color="{EMBER_DEEP}" stop-opacity="0"/>
  </radialGradient>
  <filter id="glow" x="-30%" y="-30%" width="160%" height="160%">
    <feGaussianBlur stdDeviation="6" result="b"/>
    <feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
  </filter>
  <!-- The VIIRS night band is monochrome. Mapping its luminance onto the ember
       ramp is an explicit design treatment, not a claim about the measurement. -->
  <filter id="emberDuotone" color-interpolation-filters="sRGB">
    <feColorMatrix type="saturate" values="0"/>
    <feComponentTransfer>
      <feFuncR type="table" tableValues="0.03 0.62 0.95 1"/>
      <feFuncG type="table" tableValues="0.02 0.20 0.60 0.88"/>
      <feFuncB type="table" tableValues="0.03 0.06 0.14 0.62"/>
    </feComponentTransfer>
  </filter>
  <clipPath id="insetClip">
    <rect x="{INSET_X}" y="{INSET_Y}" width="{INSET_S}" height="{INSET_S}" rx="4"/>
  </clipPath>
</defs>"""


def inset_layer(inset: Path) -> str:
    """Pedrógão Grande from orbit, framed as a figure rather than wallpaper."""
    cx = INSET_X + INSET_S / 2
    return (
        f'<image href="{embed(inset)}" x="{INSET_X}" y="{INSET_Y}" width="{INSET_S}" '
        f'height="{INSET_S}" preserveAspectRatio="xMidYMid slice" '
        f'clip-path="url(#insetClip)" filter="url(#emberDuotone)"/>'
        f'<rect x="{INSET_X}" y="{INSET_Y}" width="{INSET_S}" height="{INSET_S}" rx="4" '
        f'fill="none" stroke="{EMBER}" stroke-opacity="0.45" stroke-width="1"/>'
        f'<text x="{INSET_X}" y="{INSET_Y - 14}" fill="{EMBER_TIP}" font-family="{SANS}" '
        f'font-size="11" font-weight="600" letter-spacing="0.13em">THE 2017 PEAK</text>'
        f'<text x="{INSET_X}" y="{INSET_Y + INSET_S + 20}" fill="{INK_2}" '
        f'font-family="{SANS}" font-size="12.5" fill-opacity="0.92" '
        f'filter="url(#textShadow)">Pedrógão Grande, 19 June 2017:</text>'
        f'<text x="{INSET_X}" y="{INSET_Y + INSET_S + 38}" fill="{INK_2}" '
        f'font-family="{SANS}" font-size="12.5" fill-opacity="0.92" '
        f'filter="url(#textShadow)">bright enough to see from orbit.</text>'
    )


def build(area, fires, years, ground, inset):
    x0, x1 = PAD, W - PAD
    span = years[-1] - years[0]
    fx = lambda y: x0 + (y - years[0]) / span * (x1 - x0)
    a_max = 560_000
    fy = lambda v: BASELINE - (v / a_max) * (BASELINE - PLOT_TOP)

    s = [defs(bool(ground)), photo_layer(ground)]
    add = s.append
    add(f'<rect width="{W}" height="{H}" fill="url(#scrim)"/>')
    add(f'<rect x="0" y="{H - 150}" width="{W}" height="150" fill="url(#footerVeil)"/>')

    # ---- headline ------------------------------------------------------
    add(
        f'<text x="{PAD}" y="106" fill="{INK}" font-family="{DISPLAY}" font-size="46" '
        f'font-weight="700">Fewer fires. Four times the land.</text>'
    )
    add(
        f'<text x="{PAD}" y="146" fill="{INK_2}" font-family="{SANS}" font-size="18">'
        f'Portugal, 1980–2024. Counting wildfires is not measuring damage.</text>'
    )

    # ---- the demoted metric, top right ---------------------------------
    sx0, sx1, sy0, sy1 = W - PAD - 210, W - PAD, 96, 132
    f_max = max(fires.values())
    pts = [
        (sx0 + (y - years[0]) / span * (sx1 - sx0), sy1 - (fires[y] / f_max) * (sy1 - sy0))
        for y in years
    ]
    add(
        f'<text x="{sx1}" y="72" fill="{ASH}" font-family="{SANS}" font-size="11.5" '
        f'font-weight="600" letter-spacing="0.13em" text-anchor="end">'
        f'NUMBER OF FIRES</text>'
    )
    add(
        f'<path d="M{" L".join(f"{x:.1f},{y:.1f}" for x, y in pts)}" fill="none" '
        f'stroke="{ASH}" stroke-width="1.5" stroke-opacity="0.85"/>'
    )
    add(
        f'<text x="{sx1}" y="158" fill="{ASH}" font-family="{SANS}" font-size="15" '
        f'text-anchor="end">2023 → 2024: <tspan font-weight="700">−17%</tspan></text>'
    )

    # ---- y gridlines, ticks inside the plot ----------------------------
    for v in (200_000, 400_000):
        y = fy(v)
        add(
            f'<line x1="{x0}" y1="{y:.1f}" x2="{x1}" y2="{y:.1f}" stroke="{INK}" '
            f'stroke-opacity="0.11" stroke-width="1"/>'
        )
        add(
            f'<text x="{x0}" y="{y - 8:.1f}" fill="{INK_2}" font-family="{SANS}" '
            f'font-size="12" fill-opacity="0.75" '
            f'style="font-variant-numeric:tabular-nums">{v // 1000}k ha</text>'
        )

    # ---- the hero series -----------------------------------------------
    line = [(fx(y), fy(area[y])) for y in years]
    path = "M" + " L".join(f"{x:.1f},{y:.1f}" for x, y in line)
    add(f'<path d="{path} L{x1},{BASELINE} L{x0},{BASELINE} Z" fill="url(#areaFill)"/>')
    add(
        f'<path d="{path}" fill="none" stroke="{EMBER_TIP}" stroke-width="2" '
        f'stroke-linejoin="round" filter="url(#glow)"/>'
    )
    add(f'<line x1="{x0}" y1="{BASELINE}" x2="{x1}" y2="{BASELINE}" stroke="{EMBER_TIP}" '
        f'stroke-opacity="0.5" stroke-width="1"/>')

    # ---- x ticks, kept above the flames --------------------------------
    for yr in range(1980, 2025, 10):
        add(
            f'<text x="{fx(yr):.1f}" y="{BASELINE - 12:.1f}" fill="{INK_2}" '
            f'font-family="{SANS}" font-size="12" text-anchor="middle" fill-opacity="0.7" '
            f'style="font-variant-numeric:tabular-nums">{yr}</text>'
        )

    if inset:
        add(inset_layer(inset))

    # ---- the two labelled moments --------------------------------------
    px, py = fx(2017), fy(area[2017])
    add(f'<circle cx="{px:.1f}" cy="{py:.1f}" r="3.5" fill="{EMBER_TIP}"/>')
    add(
        f'<text x="{px:.1f}" y="{py - 14:.1f}" fill="{INK}" font-family="{SANS}" '
        f'font-size="13" text-anchor="middle" fill-opacity="0.9">2017 · 539,921 ha</text>'
    )

    ax, ay = fx(2024), fy(area[2024])
    add(
        f'<circle cx="{ax:.1f}" cy="{ay:.1f}" r="5" fill="{EMBER_TIP}" '
        f'filter="url(#glow)"/>'
    )
    add(
        f'<text x="{ax - 14:.1f}" y="{ay - 16:.1f}" fill="{EMBER_TIP}" '
        f'font-family="{SANS}" font-size="17" font-weight="700" text-anchor="end">'
        f'+299% burnt area</text>'
    )

    # ---- footer (shadowed: it may sit over the photograph's flames) ------
    add(
        f'<text x="{PAD}" y="{H - 38}" fill="{INK_2}" font-family="{SANS}" font-size="13.5" '
        f'fill-opacity="0.92" filter="url(#textShadow)">'
        f'Across 45 years the two series correlate at r = 0.42.</text>'
    )
    add(
        f'<text x="{W - PAD}" y="{H - 48}" fill="{INK_2}" font-family="{SANS}" '
        f'font-size="11.5" text-anchor="end" fill-opacity="0.72" filter="url(#textShadow)">'
        f'Data: EFFIS · Copernicus EMS / European Commission JRC (CC BY 4.0)</text>'
    )
    add(
        f'<text x="{W - PAD}" y="{H - 30}" fill="{INK_2}" font-family="{SANS}" '
        f'font-size="11.5" text-anchor="end" fill-opacity="0.62" filter="url(#textShadow)">'
        f'Image: NASA Earth Observatory (Jesse Allen) · VIIRS day-night band, Suomi NPP</text>'
    )

    return (
        f'<svg viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg" '
        f'xmlns:xlink="http://www.w3.org/1999/xlink">{"".join(s)}</svg>'
    )


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "inset"
    if mode not in {"inset", "ground", "both"}:
        raise SystemExit(f"unknown mode {mode!r} - use 'inset', 'ground' or 'both'")

    area, fires = load("effis_burnt_area_ha.csv"), load("effis_number_of_fires.csv")
    years = sorted(set(area) & set(fires))

    ground = asset("nasa_ground.jpg") if mode in ("ground", "both") else None
    inset = asset("nasa_fire_tight.jpg") if mode in ("inset", "both") else None
    print(f"mode: {mode}")
    if mode in ("ground", "both") and not ground:
        print("  assets/nasa_ground.jpg missing - falling back to procedural ember")
    if mode in ("inset", "both") and not inset:
        print("  assets/nasa_fire_tight.jpg missing - rendering without the inset")

    BUILD.mkdir(exist_ok=True)
    svg = build(area, fires, years, ground, inset)
    card = BUILD / f"social-card-{mode}.html"
    card.write_text(
        f'<!doctype html><html data-theme="dark"><meta charset=utf-8><title>card</title>'
        f"<style>body{{margin:0;background:{GROUND}}}svg{{display:block;width:1200px}}</style>"
        f"{svg}</html>"
    )

    chrome = next((c for c in CHROME_CANDIDATES if Path(c).exists() or shutil.which(c)), None)
    if not chrome:
        print(f"no Chrome found - open {card} and screenshot at 1200x675")
        return
    out = HERE / f"card-{mode}.png"
    subprocess.run(
        [chrome, "--headless", "--disable-gpu", "--hide-scrollbars",
         "--force-color-profile=srgb", f"--screenshot={out}",
         f"--window-size={W},{H}", card.as_uri()],
        check=True, capture_output=True,
    )
    print(f"{out.name}: {out.stat().st_size:,} bytes")


if __name__ == "__main__":
    main()
