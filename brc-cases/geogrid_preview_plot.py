#!/usr/bin/env python3
"""Render a geogrid-only domain preview PNG and terrain summary from geo_em files.

Gate-B deliverable for a WPS domain review: it reads the ``geo_em.d0*.nc`` written
by ``geogrid.exe`` and produces

  * ``domain_preview.png`` -- terrain-filled context map with every nested-domain
    footprint and the finest nest (d05) emphasized, plus a zoom panel on the
    finest nest showing its terrain and nest-edge relaxation buffer;
  * ``geogrid_geo_em_summary.tsv`` -- per-domain grid size, lat/lon extent, and
    HGT_M min/mean/max (the terrain-reality check);
  * stdout lines with the finest-nest HGT_M sanity check and the edge-distance of
    review targets, to inform ``i_parent_start`` / ``j_parent_start`` placement.

It reads WPS geography only. It never downloads GRIB, runs ungrib/metgrid/real/
wrf, or inspects WRF-output archives.

Usage:
    geogrid_preview_plot.py --wps-run DIR --out-png PATH --summary-tsv PATH \
        [--title STR] [--target NAME LAT LON ...]
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Polygon
from netCDF4 import Dataset

# Orientation markers for the Ashley Valley review: the nocturnal cold-air
# drainage path Dry Fork Canyon -> Maeser (canyon mouth) -> Vernal valley floor.
# Coordinates are display annotations for the preview only (Vernal is brc-tools
# waypoints.vernal; the canyon/mouth points are approximate).
DEFAULT_TARGETS = [
    ("Dry Fork canyon", 40.55, -109.65),
    ("Maeser (mouth)", 40.48, -109.57),
    ("Vernal", 40.455, -109.53),
]


def read_domain(nc_path: Path) -> dict:
    with Dataset(nc_path) as ds:
        lat = np.array(ds.variables["XLAT_M"][0])
        lon = np.array(ds.variables["XLONG_M"][0])
        hgt = np.array(ds.variables["HGT_M"][0])
        landmask = None
        if "LANDMASK" in ds.variables:
            landmask = np.array(ds.variables["LANDMASK"][0])
        title = getattr(ds, "TITLE", "")
    return {
        "path": nc_path,
        "lat": lat,
        "lon": lon,
        "hgt": hgt,
        "landmask": landmask,
        "title": title,
        "ny": hgt.shape[0],
        "nx": hgt.shape[1],
    }


def perimeter(lon: np.ndarray, lat: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    xs = np.concatenate([lon[0, :], lon[:, -1], lon[-1, ::-1], lon[::-1, 0]])
    ys = np.concatenate([lat[0, :], lat[:, -1], lat[-1, ::-1], lat[::-1, 0]])
    return xs, ys


def nearest_cell(dom: dict, tlat: float, tlon: float) -> tuple[int, int, float]:
    coslat = np.cos(np.deg2rad(tlat))
    dx = (dom["lon"] - tlon) * coslat
    dy = dom["lat"] - tlat
    d2 = dx * dx + dy * dy
    j, i = np.unravel_index(int(np.argmin(d2)), d2.shape)
    # approximate great-circle distance to that cell centre, in km
    dist_km = float(np.sqrt(d2[j, i])) * 111.195
    return int(i), int(j), dist_km


def dx_metres(dom: dict) -> float:
    # Grid spacing in the i (west-east) direction, from the SAME i+1 step for
    # both lon and lat components. Using the j+1 step for the latitude part would
    # return the cell diagonal (~sqrt(2)*dx), not the spacing.
    j = dom["ny"] // 2
    i = dom["nx"] // 2
    dlon = (dom["lon"][j, i + 1] - dom["lon"][j, i]) * np.cos(np.deg2rad(dom["lat"][j, i]))
    dlat = dom["lat"][j, i + 1] - dom["lat"][j, i]
    return float(np.hypot(dlon, dlat) * 111195.0)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--wps-run", type=Path, required=True)
    ap.add_argument("--out-png", type=Path, required=True)
    ap.add_argument("--summary-tsv", type=Path, required=True)
    ap.add_argument("--title", default="WRF domain preview")
    ap.add_argument("--relax-cells", type=int, default=5,
                    help="nest-edge relaxation/boundary cells to shade on the finest nest")
    ap.add_argument("--target", nargs=3, action="append", metavar=("NAME", "LAT", "LON"),
                    help="review target NAME LAT LON; repeatable (defaults to Vernal + canyon mouth)")
    args = ap.parse_args(argv)

    targets = ([(n, float(la), float(lo)) for n, la, lo in args.target]
               if args.target else DEFAULT_TARGETS)

    doms = []
    d = 1
    while True:
        p = args.wps_run / f"geo_em.d{d:02d}.nc"
        if not p.exists():
            break
        doms.append(read_domain(p))
        d += 1
    if not doms:
        print(f"ERROR: no geo_em.d0*.nc found under {args.wps_run}", file=sys.stderr)
        return 2
    ndom = len(doms)
    fine = doms[-1]

    # ---- summary TSV + HGT sanity ---------------------------------------
    lines = ["\t".join([
        "domain", "west_east", "south_north", "lat_min", "lat_mean", "lat_max",
        "lon_min", "lon_mean", "lon_max", "hgt_min_m", "hgt_mean_m", "hgt_max_m",
        "dx_m", "land_frac"])]
    for k, dom in enumerate(doms, start=1):
        lf = float(np.mean(dom["landmask"])) if dom["landmask"] is not None else float("nan")
        lines.append("\t".join(str(v) for v in [
            f"d{k:02d}", dom["nx"], dom["ny"],
            round(float(dom["lat"].min()), 5), round(float(dom["lat"].mean()), 5),
            round(float(dom["lat"].max()), 5),
            round(float(dom["lon"].min()), 5), round(float(dom["lon"].mean()), 5),
            round(float(dom["lon"].max()), 5),
            round(float(dom["hgt"].min()), 3), round(float(dom["hgt"].mean()), 3),
            round(float(dom["hgt"].max()), 3),
            round(dx_metres(dom), 3), round(lf, 3)]))
    args.summary_tsv.parent.mkdir(parents=True, exist_ok=True)
    args.summary_tsv.write_text("\n".join(lines) + "\n", encoding="utf-8")

    # finest-nest terrain reality check + gradient (slope) proxy
    fdx = dx_metres(fine)
    gy, gx = np.gradient(fine["hgt"], fdx, fdx)
    slope_deg = np.degrees(np.arctan(np.hypot(gx, gy)))
    print(f"finest nest d{ndom:02d}: {fine['nx']}x{fine['ny']} dx={fdx:.3f} m")
    print(f"  HGT_M min/mean/max = {fine['hgt'].min():.1f} / {fine['hgt'].mean():.1f} "
          f"/ {fine['hgt'].max():.1f} m  (nonzero={bool(np.any(fine['hgt'] != 0))})")
    print(f"  slope deg  mean/95pct/max = {slope_deg.mean():.2f} / "
          f"{np.percentile(slope_deg, 95):.2f} / {slope_deg.max():.2f}")
    print(f"  lat[{fine['lat'].min():.4f},{fine['lat'].max():.4f}] "
          f"lon[{fine['lon'].min():.4f},{fine['lon'].max():.4f}]")
    for name, tlat, tlon in targets:
        i, j, dist = nearest_cell(fine, tlat, tlon)
        edge = min(i, fine["nx"] - 1 - i, j, fine["ny"] - 1 - j)
        inside = (0 <= i < fine["nx"]) and (0 <= j < fine["ny"]) and dist < 1.0
        print(f"  target {name:24s} nearest d{ndom:02d} cell (i={i},j={j}) "
              f"edge={edge} cells ({edge * fdx:.0f} m) match_dist={dist:.2f} km "
              f"{'INSIDE' if edge > args.relax_cells and inside else 'CHECK'}")

    # ---- figure ----------------------------------------------------------
    fig, (axc, axz) = plt.subplots(1, 2, figsize=(16, 7.2))
    box_colors = ["#111111", "#1f77b4", "#2ca02c", "#ff7f0e", "#d62728"]

    # context panel: coarse-domain terrain + all footprints
    c = doms[0]
    tv = c["hgt"]
    pcm = axc.pcolormesh(c["lon"], c["lat"], tv, cmap="terrain",
                         vmin=np.percentile(tv, 2), vmax=np.percentile(tv, 99),
                         shading="auto")
    fig.colorbar(pcm, ax=axc, shrink=0.85, label="HGT_M (m)")
    for k, dom in enumerate(doms):
        xs, ys = perimeter(dom["lon"], dom["lat"])
        lw = 3.0 if k == ndom - 1 else 1.6
        axc.plot(xs, ys, color=box_colors[k % len(box_colors)], lw=lw,
                 label=f"d{k+1:02d} ({dom['nx']}x{dom['ny']})")
    for name, tlat, tlon in targets:
        axc.plot(tlon, tlat, "k*", ms=11, mec="white", mew=0.6)
    axc.set_title(f"{args.title}\ncontext: d01 terrain, {ndom} domains "
                  f"(d{ndom:02d} emphasized)")
    axc.set_xlabel("longitude"); axc.set_ylabel("latitude")
    axc.legend(loc="upper right", fontsize=8, framealpha=0.9)
    axc.set_aspect(1.0 / np.cos(np.deg2rad(float(c["lat"].mean()))))

    # zoom panel: finest nest terrain, its box, parent box, relaxation buffer
    tvz = fine["hgt"]
    pcz = axz.pcolormesh(fine["lon"], fine["lat"], tvz, cmap="terrain",
                         vmin=np.percentile(tvz, 1), vmax=np.percentile(tvz, 99),
                         shading="auto")
    fig.colorbar(pcz, ax=axz, shrink=0.85, label="HGT_M (m)")
    xs, ys = perimeter(fine["lon"], fine["lat"])
    axz.plot(xs, ys, color=box_colors[(ndom - 1) % len(box_colors)], lw=3.0,
             label=f"d{ndom:02d} edge")
    if ndom >= 2:
        pxs, pys = perimeter(doms[-2]["lon"], doms[-2]["lat"])
        axz.plot(pxs, pys, color=box_colors[(ndom - 2) % len(box_colors)], lw=1.4,
                 ls="--", label=f"d{ndom-1:02d} edge (parent)")
    rb = args.relax_cells
    if fine["ny"] > 2 * rb and fine["nx"] > 2 * rb:
        rxs, rys = perimeter(fine["lon"][rb:-rb, rb:-rb], fine["lat"][rb:-rb, rb:-rb])
        axz.plot(rxs, rys, color="magenta", lw=1.1, ls=":",
                 label=f"{rb}-cell nest-edge buffer")
    for name, tlat, tlon in targets:
        axz.plot(tlon, tlat, "k*", ms=13, mec="white", mew=0.7)
        axz.annotate(name, (tlon, tlat), textcoords="offset points", xytext=(6, 5),
                     fontsize=8, color="black",
                     bbox=dict(boxstyle="round,pad=0.15", fc="white", ec="none", alpha=0.7))
    axz.set_title(f"finest nest d{ndom:02d}: {fine['nx']}x{fine['ny']} @ {fdx:.1f} m\n"
                  f"HGT_M {tvz.min():.0f}-{tvz.max():.0f} m")
    axz.set_xlabel("longitude"); axz.set_ylabel("latitude")
    axz.legend(loc="upper right", fontsize=8, framealpha=0.9)
    axz.set_aspect(1.0 / np.cos(np.deg2rad(float(fine["lat"].mean()))))

    fig.tight_layout()
    args.out_png.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(args.out_png, dpi=130)
    print(f"wrote {args.out_png}")
    print(f"wrote {args.summary_tsv}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
