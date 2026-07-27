#!/usr/bin/env python3
"""Lightweight watcher for a running wrf.exe: is it advancing, and is it healthy?

    python brc-cases/wrf_watch.py <wrf_run_dir> [--expect-wall-h-per-sim-h 1.83] [--watch]

Read-only. Parses `rsl.out.0000` / `rsl.error.0000` text only -- no NetCDF, no Slurm
calls, no writes. Safe to run on a login node against a job on a compute node.

Designed around the failure this project actually hit. ashley2026_seiche gate E lost
**eight wall-hours producing one model-second**: 1-arc-second terrain with 56-degree
grid-scale slopes put w-damping on all 56 ranks, and nothing in the job output said
"this is hopeless" -- it looked like a slow run until the wall clock ran out.

So the headline number here is not a count of warnings, it is the **projection**:
given how far the model has advanced and how long that took, when will it finish?
A run that will overshoot its wall clock by 10x is visible within minutes. Kill it
then, not at the timeout.
"""

from __future__ import annotations

import argparse
import re
import time
from pathlib import Path

# "Timing for main: time 2025-01-28_21:00:12 on domain   3:    0.62310 elapsed seconds"
TIMING = re.compile(
    r"Timing for main: time\s+(\S+)\s+on domain\s+(\d+):\s+([\d.]+)\s+elapsed"
)
DOM_TIME = re.compile(r"(\d{4})-(\d\d)-(\d\d)_(\d\d):(\d\d):([\d.]+)")


def parse_stamp(text: str) -> float | None:
    m = DOM_TIME.match(text)
    if not m:
        return None
    y, mo, d, h, mi, s = m.groups()
    return ((int(d) * 24 + int(h)) * 60 + int(mi)) * 60 + float(s)


def scan(run: Path) -> dict:
    out = run / "rsl.out.0000"
    err = run / "rsl.error.0000"
    info: dict = {"exists": out.is_file(), "cfl": 0, "wdamp": 0, "d1_steps": 0,
                  "first": None, "last": None, "elapsed_sum": 0.0, "recent": [],
                  "done": False, "errors": []}
    if not info["exists"]:
        return info

    text = out.read_text(errors="replace")
    for m in TIMING.finditer(text):
        stamp, dom, elapsed = m.group(1), int(m.group(2)), float(m.group(3))
        if dom != 1:
            continue
        t = parse_stamp(stamp)
        if t is None:
            continue
        info["d1_steps"] += 1
        info["elapsed_sum"] += elapsed
        if info["first"] is None:
            info["first"] = t
        info["last"] = t
        info["recent"].append(elapsed)
    info["recent"] = info["recent"][-20:]

    # Health markers. w-damping alone is not fatal -- it is a safety net -- but a
    # rising count on every step means the net is carrying the run.
    low = text.lower()
    info["cfl"] = low.count("cfl")
    info["wdamp"] = low.count("w-damping") + low.count("w damping")
    info["done"] = "wrf: SUCCESS COMPLETE WRF" in text

    if err.is_file():
        etext = err.read_text(errors="replace")
        info["errors"] = [ln.strip() for ln in etext.splitlines()
                          if "error" in ln.lower() or "fatal" in ln.lower()][-5:]
    return info


def report(run: Path, expect: float, run_hours: float) -> tuple[str, bool]:
    """Return (text, healthy)."""
    i = scan(run)
    lines = [f"wrf_watch  {run}"]
    if not i["exists"]:
        return "\n".join(lines + ["  rsl.out.0000 not present yet "
                                  "(real.exe may still be running)"]), True
    if i["first"] is None or i["d1_steps"] == 0:
        return "\n".join(lines + ["  no completed d01 steps yet"]), True

    sim_s = i["last"] - i["first"]
    wall_s = i["elapsed_sum"]
    lines.append(f"  d01 steps completed : {i['d1_steps']}")
    lines.append(f"  model time advanced : {sim_s/60:.1f} min of {run_hours*60:.0f} min "
                 f"({100*sim_s/(run_hours*3600):.1f}%)")
    lines.append(f"  wall time in steps  : {wall_s/60:.1f} min")

    healthy = True
    if sim_s > 0:
        rate = (wall_s / 3600) / (sim_s / 3600)  # wall-h per sim-h
        projected = rate * run_hours
        lines.append(f"  rate                : {rate:.2f} wall-h per sim-h "
                     f"(expected {expect:.2f})")
        lines.append(f"  PROJECTED TOTAL     : {projected:.1f} wall-hours")
        if rate > 3 * expect:
            healthy = False
            lines.append(f"  >> STOP: {rate/expect:.0f}x slower than expected. This is the "
                         "gate E failure signature -- do not wait for the timeout.")
        elif rate > 1.5 * expect:
            lines.append(f"  >> WATCH: {rate/expect:.1f}x slower than expected.")
    if i["recent"]:
        lines.append(f"  last {len(i['recent'])} step times : "
                     f"{min(i['recent']):.2f}-{max(i['recent']):.2f} s")

    lines.append(f"  cfl mentions        : {i['cfl']}")
    lines.append(f"  w-damping mentions  : {i['wdamp']}")
    if i["wdamp"] > i["d1_steps"] and i["d1_steps"] > 5:
        healthy = False
        lines.append("  >> w-damping is firing more often than once per step: the safety "
                     "net is carrying the run, not protecting it.")
    for e in i["errors"]:
        healthy = False
        lines.append(f"  >> rsl.error: {e[:110]}")
    if i["done"]:
        lines.append("  SUCCESS COMPLETE WRF")
    return "\n".join(lines), healthy


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("run_dir", type=Path)
    ap.add_argument("--expect-wall-h-per-sim-h", type=float, default=1.83,
                    help="projected rate from domain_calc.py (default: this case)")
    ap.add_argument("--run-hours", type=float, default=7.0)
    ap.add_argument("--watch", action="store_true", help="re-report every --every seconds")
    ap.add_argument("--every", type=int, default=300)
    args = ap.parse_args(argv)

    while True:
        text, healthy = report(args.run_dir, args.expect_wall_h_per_sim_h, args.run_hours)
        print(text, flush=True)
        if not args.watch:
            return 0 if healthy else 1
        print("-" * 60, flush=True)
        time.sleep(args.every)


if __name__ == "__main__":
    raise SystemExit(main())
