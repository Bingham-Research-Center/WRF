#!/usr/bin/env python3
"""Render no-run quicklooks from existing BRC WRF proof artifacts.

This consumes a ``brc-cases/*.case.yaml`` manifest, the existing ``brc-tools``
input manifest, WPS ``met_em`` files, and archived WRF output. It never runs
WPS, real.exe, wrf.exe, Slurm, or download/staging commands.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import wrf_case


REPO_ROOT = Path(__file__).resolve().parents[1]


def _path_under(path: Path, parent: Path) -> bool:
    try:
        path.resolve(strict=False).relative_to(parent.resolve(strict=False))
        return True
    except ValueError:
        return False


def _default_output_dir(ctx: "QuicklookContext") -> Path:
    """Put review PNGs beside the durable archive run, never inside the repo."""
    return ctx.archive_run / "quicklooks"


def _validate_output_dir(path: Path) -> Path:
    if _path_under(path, REPO_ROOT):
        raise ValueError(
            "quicklook output inside the brc-wrf checkout is not allowed; "
            "write to a durable lawson-group archive path instead"
        )
    return path


@dataclass
class QuicklookContext:
    case_file: Path
    data: dict[str, Any]
    case_name: str
    case_start: str
    manifest_path: Path
    wps_run: Path
    archive_run: Path
    met_d01: Path
    met_d02: Path
    wrf_d02: Path


def _as_path(value: Any) -> Path:
    return wrf_case.as_path(value)


def _ensure_mpl_config() -> Path:
    """Keep Matplotlib cache writes out of unwritable home config paths."""
    current = os.environ.get("MPLCONFIGDIR")
    if current:
        path = Path(current)
    else:
        user = os.environ.get("USER", "user")
        path = Path("/tmp") / f"brc-wrf-matplotlib-{user}"
        os.environ["MPLCONFIGDIR"] = str(path)
    path.mkdir(parents=True, exist_ok=True)
    return path


def _find_first(paths: list[Path], label: str) -> Path:
    for path in paths:
        if path.exists():
            return path
    raise FileNotFoundError(f"could not find {label}; tried: {', '.join(str(p) for p in paths)}")


def _latest_archive_run(archive_root: Path) -> Path:
    runs = sorted(p for p in archive_root.glob("run_*") if p.is_dir())
    if not runs:
        raise FileNotFoundError(f"no run_* archive directories under {archive_root}")
    return runs[-1]


def _load_context(args: argparse.Namespace) -> QuicklookContext:
    case_file = Path(args.case_file)
    data = wrf_case.load_case(case_file)
    findings = wrf_case.validate_case(data, strict_files=False)
    wrf_case.print_findings(findings)
    errors = [f for f in findings if f.severity == "ERROR"]
    if errors:
        raise RuntimeError("case validation has errors")

    case = data["case"]
    forcing = data["forcing"]
    paths = data["paths"]
    case_name = str(case["name"])
    case_start = str(case["start"])
    manifest_path = _as_path(forcing["manifest_path"])
    wps_run = _as_path(paths["wps_run"])
    archive_root = _as_path(paths["archive_root"])
    archive_run = Path(args.archive_run) if args.archive_run else _latest_archive_run(archive_root)

    met_d01 = _find_first(
        [
            wps_run / f"met_em.d01.{case_start}.nc",
            *sorted(wps_run.glob("met_em.d01.*.nc")),
        ],
        "d01 met_em",
    )
    met_d02 = _find_first(
        [
            wps_run / f"met_em.d02.{case_start}.nc",
            *sorted(wps_run.glob("met_em.d02.*.nc")),
        ],
        "d02 met_em",
    )
    wrf_d02 = _find_first(
        [
            archive_run / f"wrfout_d02_{case_start}",
            *sorted(archive_run.glob("wrfout_d02_*")),
        ],
        "d02 wrfout",
    )

    return QuicklookContext(
        case_file=case_file,
        data=data,
        case_name=case_name,
        case_start=case_start,
        manifest_path=manifest_path,
        wps_run=wps_run,
        archive_run=archive_run,
        met_d01=met_d01,
        met_d02=met_d02,
        wrf_d02=wrf_d02,
    )


def _verify_brc_tools_manifest(manifest_path: Path, *, verbose: bool) -> None:
    brc_tools = (REPO_ROOT / "../brc-tools").resolve()
    script = brc_tools / "scripts" / "stage_wrf_inputs.py"
    if not script.exists():
        raise FileNotFoundError(f"brc-tools verifier not found: {script}")
    if not manifest_path.exists():
        raise FileNotFoundError(f"brc-tools manifest not found: {manifest_path}")

    env = os.environ.copy()
    env["PYTHONPATH"] = f"{brc_tools}{os.pathsep}{env.get('PYTHONPATH', '')}"
    env["MPLCONFIGDIR"] = str(_ensure_mpl_config())
    result = subprocess.run(
        [sys.executable, str(script), "--verify-manifest", str(manifest_path)],
        cwd=brc_tools,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    if verbose or result.returncode != 0:
        print(result.stdout, end="")
    if result.returncode != 0:
        raise RuntimeError(f"brc-tools manifest verification failed: {manifest_path}")
    if not verbose:
        last_line = result.stdout.strip().splitlines()[-1] if result.stdout.strip() else "OK"
        print(f"brc-tools manifest: {last_line}")


def _open_dataset(path: Path):
    import xarray as xr

    return xr.open_dataset(path, decode_times=False)


def _require_vars(path: Path, names: list[str]) -> None:
    with _open_dataset(path) as ds:
        missing = [name for name in names if name not in ds.variables]
    if missing:
        raise RuntimeError(f"{path} is missing variables: {', '.join(missing)}")


def _first_available(path: Path, names: list[str]) -> str:
    with _open_dataset(path) as ds:
        for name in names:
            if name in ds.variables:
                return name
    raise RuntimeError(f"{path} has none of: {', '.join(names)}")


def _as_2d(ds: Any, name: str) -> Any:
    arr = ds[name]
    selectors = {dim: 0 for dim in arr.dims[:-2]}
    if selectors:
        arr = arr.isel(selectors)
    return arr.squeeze(drop=True)


def _coords(ds: Any, lon_name: str, lat_name: str, field: Any) -> tuple[Any, Any]:
    import numpy as np

    if lon_name in ds.variables and lat_name in ds.variables:
        lon = _as_2d(ds, lon_name).values
        lat = _as_2d(ds, lat_name).values
        return lon, lat
    ny, nx = field.shape
    x = np.arange(nx)
    y = np.arange(ny)
    return np.meshgrid(x, y)


def _converted_values(arr: Any, units: str | None) -> tuple[Any, str]:
    values = arr.values
    label = units or ""
    if units == "K":
        values = values - 273.15
        label = "deg C"
    if units == "Pa":
        values = values / 100.0
        label = "hPa"
    return values, label


def _plot_field(
    path: Path,
    field_name: str,
    out_path: Path,
    *,
    lon_name: str,
    lat_name: str,
    title: str,
    cmap: str,
    contour_name: str | None = None,
    wind_names: tuple[str, str] | None = None,
) -> Path:
    _ensure_mpl_config()
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np

    with _open_dataset(path) as ds:
        field = _as_2d(ds, field_name)
        lon, lat = _coords(ds, lon_name, lat_name, field)
        values, units = _converted_values(field, field.attrs.get("units"))

        fig, ax = plt.subplots(figsize=(8.5, 6.5), constrained_layout=True)
        mesh = ax.pcolormesh(lon, lat, values, shading="auto", cmap=cmap)
        fig.colorbar(mesh, ax=ax, shrink=0.8, label=f"{field_name} {units}".strip())

        if contour_name:
            contour = _as_2d(ds, contour_name)
            contour_values, _ = _converted_values(contour, contour.attrs.get("units"))
            finite = contour_values[np.isfinite(contour_values)]
            if finite.size:
                levels = np.linspace(float(np.nanmin(finite)), float(np.nanmax(finite)), 8)
                ax.contour(lon, lat, contour_values, levels=levels, colors="black", linewidths=0.35, alpha=0.55)

        if wind_names:
            u = _as_2d(ds, wind_names[0]).values
            v = _as_2d(ds, wind_names[1]).values
            stride_y = max(1, u.shape[0] // 24)
            stride_x = max(1, u.shape[1] // 24)
            ax.quiver(
                lon[::stride_y, ::stride_x],
                lat[::stride_y, ::stride_x],
                u[::stride_y, ::stride_x],
                v[::stride_y, ::stride_x],
                color="black",
                scale=450,
                width=0.0022,
                alpha=0.75,
            )

        ax.set_title(title)
        ax.set_xlabel("longitude")
        ax.set_ylabel("latitude")
        ax.text(
            0.99,
            0.01,
            f"BRC WRF NAM-only proof | {path.name}",
            transform=ax.transAxes,
            ha="right",
            va="bottom",
            fontsize=6,
            alpha=0.65,
            bbox={"facecolor": "white", "edgecolor": "none", "alpha": 0.55, "pad": 1.5},
        )
        out_path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(out_path, dpi=150)
        plt.close(fig)
    return out_path


def _plot_domain_terrain(ctx: QuicklookContext, out_path: Path) -> Path:
    _ensure_mpl_config()
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    with _open_dataset(ctx.met_d01) as d01, _open_dataset(ctx.met_d02) as d02:
        terrain = _as_2d(d01, "HGT_M")
        lon1, lat1 = _coords(d01, "XLONG_M", "XLAT_M", terrain)
        hgt = terrain.values
        lon2 = _as_2d(d02, "XLONG_M").values
        lat2 = _as_2d(d02, "XLAT_M").values

        fig, ax = plt.subplots(figsize=(8.5, 6.5), constrained_layout=True)
        mesh = ax.pcolormesh(lon1, lat1, hgt, shading="auto", cmap="terrain")
        fig.colorbar(mesh, ax=ax, shrink=0.8, label="HGT_M m")
        ax.plot(
            [lon2.min(), lon2.max(), lon2.max(), lon2.min(), lon2.min()],
            [lat2.min(), lat2.min(), lat2.max(), lat2.max(), lat2.min()],
            color="red",
            linewidth=1.8,
            label="d02 extent",
        )
        ax.set_title("WPS terrain and nested-domain footprint")
        ax.set_xlabel("longitude")
        ax.set_ylabel("latitude")
        ax.legend(loc="upper right")
        ax.text(
            0.99,
            0.01,
            f"BRC WRF NAM-only proof | {ctx.met_d01.name} + {ctx.met_d02.name}",
            transform=ax.transAxes,
            ha="right",
            va="bottom",
            fontsize=6,
            alpha=0.65,
            bbox={"facecolor": "white", "edgecolor": "none", "alpha": 0.55, "pad": 1.5},
        )
        out_path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(out_path, dpi=150)
        plt.close(fig)
    return out_path


def _render(ctx: QuicklookContext, output_dir: Path) -> list[Path]:
    snow_var = _first_available(ctx.met_d02, ["SNOWH", "SNOW"])
    land_var = _first_available(ctx.met_d02, ["LANDSEA", "LANDMASK"])

    outputs = [
        _plot_domain_terrain(ctx, output_dir / "wps_domain_terrain.png"),
        _plot_field(
            ctx.met_d02,
            land_var,
            output_dir / "wps_d02_landmask.png",
            lon_name="XLONG_M",
            lat_name="XLAT_M",
            title=f"WPS d02 {land_var} at {ctx.case_start}",
            cmap="Greys",
            contour_name="HGT_M",
        ),
        _plot_field(
            ctx.met_d02,
            "SKINTEMP",
            output_dir / "wps_d02_skintemp_snow.png",
            lon_name="XLONG_M",
            lat_name="XLAT_M",
            title=f"WPS d02 skin temperature, snow-contoured, {ctx.case_start}",
            cmap="RdYlBu_r",
            contour_name=snow_var,
        ),
        _plot_field(
            ctx.wrf_d02,
            "T2",
            output_dir / "wrf_d02_t2_10m_wind.png",
            lon_name="XLONG",
            lat_name="XLAT",
            title=f"WRF d02 2 m temperature and 10 m wind, {ctx.case_start}",
            cmap="RdYlBu_r",
            contour_name="HGT",
            wind_names=("U10", "V10"),
        ),
        _plot_field(
            ctx.wrf_d02,
            "SNOWH",
            output_dir / "wrf_d02_snow_depth.png",
            lon_name="XLONG",
            lat_name="XLAT",
            title=f"WRF d02 snow depth, terrain-contoured, {ctx.case_start}",
            cmap="Blues",
            contour_name="HGT",
        ),
    ]
    return outputs


def _check_inputs(ctx: QuicklookContext, *, verbose_manifest: bool) -> None:
    _verify_brc_tools_manifest(ctx.manifest_path, verbose=verbose_manifest)
    _require_vars(ctx.met_d01, ["HGT_M", "XLONG_M", "XLAT_M"])
    _require_vars(ctx.met_d02, ["HGT_M", "XLONG_M", "XLAT_M", "SKINTEMP"])
    _first_available(ctx.met_d02, ["LANDSEA", "LANDMASK"])
    _first_available(ctx.met_d02, ["SNOWH", "SNOW"])
    _require_vars(ctx.wrf_d02, ["XLONG", "XLAT", "T2", "U10", "V10", "SNOWH", "HGT"])
    print(f"WPS d01: {ctx.met_d01}")
    print(f"WPS d02: {ctx.met_d02}")
    print(f"WRF d02: {ctx.wrf_d02}")
    print(f"archive run: {ctx.archive_run}")


def cmd_check(args: argparse.Namespace) -> int:
    try:
        ctx = _load_context(args)
        _check_inputs(ctx, verbose_manifest=args.verbose_manifest)
    except Exception as exc:  # noqa: BLE001 - CLI boundary
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    return 0


def cmd_render(args: argparse.Namespace) -> int:
    try:
        ctx = _load_context(args)
        _check_inputs(ctx, verbose_manifest=args.verbose_manifest)
        output_dir = _validate_output_dir(
            Path(args.output_dir) if args.output_dir else _default_output_dir(ctx)
        )
        outputs = _render(ctx, output_dir)
    except Exception as exc:  # noqa: BLE001 - CLI boundary
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    for path in outputs:
        print(f"wrote {path}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Check and render BRC WRF quicklooks from existing proof artifacts."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    for name in ("check", "render"):
        cmd = subparsers.add_parser(name)
        cmd.add_argument("case_file")
        cmd.add_argument(
            "--archive-run",
            help="specific archive run directory; defaults to the latest run_* under paths.archive_root",
        )
        cmd.add_argument(
            "--verbose-manifest",
            action="store_true",
            help="print every brc-tools manifest verification row",
        )
        cmd.set_defaults(func=cmd_check if name == "check" else cmd_render)
        if name == "render":
            cmd.add_argument(
                "--output-dir",
                help="directory for PNG output; default is <archive-run>/quicklooks; repo-local paths are refused",
            )

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
