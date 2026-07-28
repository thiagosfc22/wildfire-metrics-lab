"""Download and parse the official EFFIS annual wildfire statistics workbook.

Source: European Forest Fire Information System (EFFIS), Copernicus Emergency
Management Service / European Commission Joint Research Centre (JRC).
https://forest-fire.emergency.copernicus.eu/applications/data-and-services

The workbook has two sheets covering 1980-2024 for 31 countries:
  sheet1 - burnt area in hectares
  sheet2 - number of forest fires

Stdlib only: an .xlsx is a zip of XML, so no pandas/openpyxl needed.
Data use requires acknowledging the EFFIS licence:
https://forest-fire.emergency.copernicus.eu/about-effis/data-license
"""

import csv
import re
import urllib.request
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

URL = (
    "https://forest-fire.emergency.copernicus.eu/effis"
    "/applications/data-and-services/report_2024.xlsx"
)
NS = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
TAG = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
HERE = Path(__file__).parent
DATA = HERE / "data"
SHEETS = {
    "xl/worksheets/sheet1.xml": "effis_burnt_area_ha.csv",
    "xl/worksheets/sheet2.xml": "effis_number_of_fires.csv",
}


def col_index(ref: str) -> int:
    """'A' -> 1, 'AB' -> 28. Cell refs skip empty columns, so we can't enumerate."""
    n = 0
    for ch in ref:
        n = n * 26 + (ord(ch) - 64)
    return n


def shared_strings(z: zipfile.ZipFile) -> list[str]:
    root = ET.fromstring(z.read("xl/sharedStrings.xml"))
    return ["".join(t.text or "" for t in si.iter(TAG + "t")) for si in root.findall("m:si", NS)]


def read_sheet(z: zipfile.ZipFile, path: str, strings: list[str]) -> list[list[str]]:
    sheet = ET.fromstring(z.read(path))
    rows = []
    for row in sheet.iter(TAG + "row"):
        cells = {}
        for c in row.findall("m:c", NS):
            value = c.find("m:v", NS)
            if value is None:
                continue
            ref = re.match(r"([A-Z]+)", c.get("r")).group(1)
            # t="s" means the value is an index into the shared string table
            raw = strings[int(value.text)] if c.get("t") == "s" else value.text
            # EFFIS writes thousands separators as non-breaking spaces
            cells[col_index(ref)] = raw.replace("\xa0", "").replace(" ", "").strip()
        if cells:
            width = max(cells)
            rows.append([cells.get(i, "") for i in range(1, width + 1)])
    return rows


def main() -> None:
    DATA.mkdir(exist_ok=True)
    xlsx = DATA / "report_2024.xlsx"

    if not xlsx.exists():
        print(f"downloading {URL}")
        urllib.request.urlretrieve(URL, xlsx)
    print(f"{xlsx.name}: {xlsx.stat().st_size:,} bytes")

    with zipfile.ZipFile(xlsx) as z:
        strings = shared_strings(z)
        for path, out_name in SHEETS.items():
            rows = read_sheet(z, path, strings)
            out = DATA / out_name
            with out.open("w", newline="") as f:
                csv.writer(f).writerows(rows)
            years = [r[0] for r in rows[1:] if r and r[0]]
            print(
                f"{out_name}: {len(rows) - 1} years "
                f"({years[0]}-{years[-1]}), {len(rows[0]) - 1} countries"
            )


if __name__ == "__main__":
    main()
