"""
make_worldmap.py  -  Natural Earth 1:110m countries (public domain) -> motion/src/library/worldmap.json

    bin/python tools/make_worldmap.py <ne_110m_admin_0_countries.geojson>

Equirectangular projection into a 1000 x 460 box (longitude -180..180, latitude 84..-58; Antarctica left out),
rounded to 0.1 px and thinned, so the whole map is one small JSON the map component draws. Each country keeps
its name, ISO code and Natural Earth's own label point (where a pin or label goes).
Source: https://www.naturalearthdata.com (public domain, no credit required).
"""

import json
import sys
from pathlib import Path

W, H, LAT_TOP, LAT_BOT = 1000, 460, 84.0, -58.0
OUT = Path(__file__).resolve().parent.parent / "motion" / "src" / "library" / "worldmap.json"


def xy(lon, lat):
    x = (lon + 180) / 360 * W
    y = (LAT_TOP - max(LAT_BOT, min(LAT_TOP, lat))) / (LAT_TOP - LAT_BOT) * H
    return round(x, 1), round(y, 1)


def ring(coords):
    pts, last = [], None
    for lon, lat in coords:
        p = xy(lon, lat)
        if last is None or abs(p[0] - last[0]) + abs(p[1] - last[1]) >= 0.6:
            pts.append(p)
            last = p
    if len(pts) < 3:
        return ""
    return "M" + "L".join(f"{x:g},{y:g}" for x, y in pts) + "Z"


def main():
    src = Path(sys.argv[1])
    data = json.loads(src.read_text(encoding="utf-8"))
    out = []
    for f in data["features"]:
        pr = f["properties"]
        iso = pr.get("ISO_A3") if pr.get("ISO_A3") not in (None, "-99") else pr.get("ADM0_A3")
        if iso == "ATA":
            continue
        g = f["geometry"]
        polys = g["coordinates"] if g["type"] == "MultiPolygon" else [g["coordinates"]]
        d = "".join(ring(poly[0]) for poly in polys)
        if not d:
            continue
        lx, ly = xy(pr.get("LABEL_X", 0), pr.get("LABEL_Y", 0))
        out.append({"name": pr.get("NAME"), "iso": iso, "d": d, "x": lx, "y": ly})
    OUT.write_text(json.dumps({"width": W, "height": H, "latTop": LAT_TOP, "latBottom": LAT_BOT,
                               "source": "Natural Earth 1:110m admin 0 countries (public domain)",
                               "countries": out}, separators=(",", ":")), encoding="utf-8")
    print(f"{len(out)} countries -> {OUT} ({OUT.stat().st_size / 1e3:.0f} KB)")


if __name__ == "__main__":
    main()
