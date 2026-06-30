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
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import wrf_case


REPO_ROOT = Path(__file__).resolve().parents[1]
BRC_TOOLS_ROOT = (REPO_ROOT / "../brc-tools").resolve()
if str(BRC_TOOLS_ROOT) not in sys.path:
    sys.path.insert(0, str(BRC_TOOLS_ROOT))


def _path_under(path: Path, parent: Path) -> bool:
    try:
        path.resolve(strict=False).relative_to(parent.resolve(strict=False))
        return True
    except ValueError:
        return False


def _default_output_dir(ctx: "QuicklookContext") -> Path:
    """Put review PNGs in a stamped archive subdirectory, never inside the repo."""
    return ctx.archive_run / "quicklooks" / _quicklook_stamp()


def _validate_output_dir(path: Path) -> Path:
    if _path_under(path, REPO_ROOT):
        raise ValueError(
            "quicklook output inside the brc-wrf checkout is not allowed; "
            "write to a durable lawson-group archive path instead"
        )
    return path


def _quicklook_stamp() -> str:
    stamp = os.environ.get("BRC_WRF_QUICKLOOK_STAMP")
    if stamp:
        if "/" in stamp or stamp in {".", ".."}:
            raise ValueError(f"invalid BRC_WRF_QUICKLOOK_STAMP: {stamp!r}")
        return stamp
    return datetime.now(timezone.utc).strftime("standardized_%Y%m%dT%H%M%SZ")


@dataclass
class QuicklookContext:
    case_file: Path
    data: dict[str, Any]
    case_name: str
    case_start: str
    domains: tuple[int, ...]
    manifest_path: Path
    wps_run: Path
    archive_run: Path
    met_by_domain: dict[int, Path]
    wrf_by_domain: dict[int, Path]


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


def _domain_tag(domain: int) -> str:
    return f"d{domain:02d}"


def _latest_archive_run(archive_root: Path) -> Path:
    runs = sorted(p for p in archive_root.glob("run_*") if p.is_dir())
    if not runs:
        raise FileNotFoundError(f"no run_* archive directories under {archive_root}")
    return runs[-1]


def _resolve_archive_run(archive_root: Path, archive_run_arg: str | None) -> Path:
    if archive_run_arg:
        return Path(archive_run_arg)
    return _latest_archive_run(archive_root)


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
    domain_count = int(case.get("domains", 1))
    domains = tuple(range(1, domain_count + 1))
    manifest_path = _as_path(forcing["manifest_path"])
    wps_run = _as_path(paths["wps_run"])
    archive_root = _as_path(paths["archive_root"])
    archive_run = _resolve_archive_run(archive_root, args.archive_run)

    met_by_domain: dict[int, Path] = {}
    wrf_by_domain: dict[int, Path] = {}
    for domain in domains:
        tag = _domain_tag(domain)
        met_by_domain[domain] = _find_first(
            [
                wps_run / f"met_em.{tag}.{case_start}.nc",
                *sorted(wps_run.glob(f"met_em.{tag}.*.nc")),
            ],
            f"{tag} met_em",
        )
        wrf_by_domain[domain] = _find_first(
            [
                archive_run / f"wrfout_{tag}_{case_start}",
                *sorted(archive_run.glob(f"wrfout_{tag}_*")),
            ],
            f"{tag} wrfout",
        )

    return QuicklookContext(
        case_file=case_file,
        data=data,
        case_name=case_name,
        case_start=case_start,
        domains=domains,
        manifest_path=manifest_path,
        wps_run=wps_run,
        archive_run=archive_run,
        met_by_domain=met_by_domain,
        wrf_by_domain=wrf_by_domain,
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


def _as_2d(ds: Any, name: str) -> Any:
    arr = ds[name]
    selectors = {dim: 0 for dim in arr.dims[:-2]}
    if selectors:
        arr = arr.isel(selectors)
    return arr.squeeze(drop=True)


def _as_3d(ds: Any, name: str) -> Any:
    arr = ds[name]
    selectors = {dim: 0 for dim in arr.dims[:-3]}
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


def _distance_km(lon: Any, lat: Any) -> Any:
    import numpy as np

    lon_r = np.radians(lon.astype(float))
    lat_r = np.radians(lat.astype(float))
    dlon = np.diff(lon_r)
    dlat = np.diff(lat_r)
    a = np.sin(dlat / 2.0) ** 2 + np.cos(lat_r[:-1]) * np.cos(lat_r[1:]) * np.sin(dlon / 2.0) ** 2
    segment = 2.0 * 6371.0 * np.arcsin(np.sqrt(a))
    return np.concatenate(([0.0], np.cumsum(segment)))


def _annotation(path: Path) -> str:
    return f"BRC WRF NAM-only proof | {path.name}"


def _theta_from_t_p(t_k: Any, p_pa: Any) -> Any:
    return t_k * (100000.0 / p_pa) ** 0.2854


def _symmetrical_limit(values: Any) -> float | None:
    import numpy as np

    finite = values[np.isfinite(values)]
    if finite.size == 0:
        return None
    limit = float(np.nanmax(np.abs(finite)))
    return limit if limit > 0.0 else None


def _plot_domain_cross_section(
    path: Path,
    out_path: Path,
    *,
    domain_tag: str,
    case_start: str,
    orientation: str,
) -> Path:
    from brc_tools.visualize.grid import plot_vertical_section

    import numpy as np

    with _open_dataset(path) as ds:
        theta = _as_3d(ds, "T").values + 300.0
        z_w = (_as_3d(ds, "PH").values + _as_3d(ds, "PHB").values) / 9.80665
        z_mass = 0.5 * (z_w[:-1, :, :] + z_w[1:, :, :])
        terrain = _as_2d(ds, "HGT")
        hgt = terrain.values
        z_agl = z_mass - hgt[np.newaxis, :, :]
        lon, lat = _coords(ds, "XLONG", "XLAT", terrain)

        if orientation == "we":
            index = hgt.shape[0] // 2
            theta_sec = theta[:, index, :]
            z_sec = z_agl[:, index, :]
            lon_line = lon[index, :]
            lat_line = lat[index, :]
            xlabel = "west-east distance (km)"
            section_label = f"row {index}"
            pblh = _as_2d(ds, "PBLH").values[index, :] if "PBLH" in ds.variables else None
        elif orientation == "sn":
            index = hgt.shape[1] // 2
            theta_sec = theta[:, :, index]
            z_sec = z_agl[:, :, index]
            lon_line = lon[:, index]
            lat_line = lat[:, index]
            xlabel = "south-north distance (km)"
            section_label = f"column {index}"
            pblh = _as_2d(ds, "PBLH").values[:, index] if "PBLH" in ds.variables else None
        else:
            raise ValueError(f"unknown cross-section orientation: {orientation}")

        distance = _distance_km(lon_line, lat_line)

        return plot_vertical_section(
            distance,
            z_sec,
            theta_sec,
            out_path,
            title=f"WRF {domain_tag} potential-temperature cross-section, {case_start} | {section_label}",
            colorbar_label="potential temperature K",
            xlabel=xlabel,
            line_y=pblh,
            line_label="PBLH" if pblh is not None else None,
            annotation=_annotation(path),
        )


def _plot_domain_products(ctx: QuicklookContext, domain: int, output_dir: Path) -> list[Path]:
    from brc_tools.visualize.grid import plot_grid_field, terrain_contour_levels

    import numpy as np

    tag = _domain_tag(domain)
    path = ctx.wrf_by_domain[domain]
    domain_dir = output_dir / tag

    with _open_dataset(path) as ds:
        terrain = _as_2d(ds, "HGT")
        hgt = terrain.values
        lon, lat = _coords(ds, "XLONG", "XLAT", terrain)
        terrain_levels = terrain_contour_levels(hgt)
        annotation = _annotation(path)

        t2_k = _as_2d(ds, "T2").values
        t2_c = t2_k - 273.15
        u10 = _as_2d(ds, "U10").values
        v10 = _as_2d(ds, "V10").values
        wspd10 = np.hypot(u10, v10)
        psfc_pa = _as_2d(ds, "PSFC").values
        psfc_hpa = psfc_pa / 100.0
        theta2 = _theta_from_t_p(t2_k, psfc_pa)
        t2_anomaly = t2_c - float(np.nanmedian(t2_c))
        anomaly_limit = _symmetrical_limit(t2_anomaly)
        tsk_c = _as_2d(ds, "TSK").values - 273.15
        pblh = _as_2d(ds, "PBLH").values
        snowh = _as_2d(ds, "SNOWH").values

        outputs = [
            plot_grid_field(
                lon,
                lat,
                t2_c,
                domain_dir / "01_t2_10m_wind.png",
                title=f"WRF {tag} 2 m temperature and 10 m wind, {ctx.case_start}",
                colorbar_label="T2 deg C",
                cmap="RdYlBu_r",
                contour=hgt,
                contour_levels=terrain_levels,
                contour_label=True,
                wind_u=u10,
                wind_v=v10,
                annotation=annotation,
            ),
            plot_grid_field(
                lon,
                lat,
                t2_anomaly,
                domain_dir / "02_t2_anomaly.png",
                title=f"WRF {tag} 2 m temperature anomaly from domain median, {ctx.case_start}",
                colorbar_label="T2 anomaly deg C",
                cmap="RdBu_r",
                vmin=-anomaly_limit if anomaly_limit is not None else None,
                vmax=anomaly_limit,
                contour=hgt,
                contour_levels=terrain_levels,
                contour_label=True,
                annotation=annotation,
            ),
            plot_grid_field(
                lon,
                lat,
                theta2,
                domain_dir / "03_theta2_10m_wind.png",
                title=f"WRF {tag} 2 m potential temperature and 10 m wind, {ctx.case_start}",
                colorbar_label="theta2 K",
                cmap="RdYlBu_r",
                contour=hgt,
                contour_levels=terrain_levels,
                contour_label=True,
                wind_u=u10,
                wind_v=v10,
                annotation=annotation,
            ),
            plot_grid_field(
                lon,
                lat,
                wspd10,
                domain_dir / "04_10m_wind_speed.png",
                title=f"WRF {tag} 10 m wind speed and vectors, {ctx.case_start}",
                colorbar_label="10 m wind speed m s-1",
                cmap="viridis",
                contour=hgt,
                contour_levels=terrain_levels,
                contour_label=True,
                wind_u=u10,
                wind_v=v10,
                annotation=annotation,
            ),
            plot_grid_field(
                lon,
                lat,
                pblh,
                domain_dir / "05_pbl_height.png",
                title=f"WRF {tag} PBL height, {ctx.case_start}",
                colorbar_label="PBLH m",
                cmap="YlOrRd",
                contour=hgt,
                contour_levels=terrain_levels,
                contour_label=True,
                annotation=annotation,
            ),
            plot_grid_field(
                lon,
                lat,
                snowh,
                domain_dir / "06_snow_depth.png",
                title=f"WRF {tag} snow depth, {ctx.case_start}",
                colorbar_label="SNOWH m",
                cmap="Blues",
                contour=hgt,
                contour_levels=terrain_levels,
                contour_label=True,
                annotation=annotation,
            ),
            plot_grid_field(
                lon,
                lat,
                tsk_c,
                domain_dir / "07_skin_temperature.png",
                title=f"WRF {tag} skin temperature, {ctx.case_start}",
                colorbar_label="TSK deg C",
                cmap="RdYlBu_r",
                contour=hgt,
                contour_levels=terrain_levels,
                contour_label=True,
                annotation=annotation,
            ),
            plot_grid_field(
                lon,
                lat,
                psfc_hpa,
                domain_dir / "08_surface_pressure.png",
                title=f"WRF {tag} surface pressure, {ctx.case_start}",
                colorbar_label="PSFC hPa",
                cmap="viridis",
                contour=hgt,
                contour_levels=terrain_levels,
                contour_label=True,
                annotation=annotation,
            ),
        ]

    outputs.extend(
        [
            _plot_domain_cross_section(
                path,
                domain_dir / "09_theta_xsection_we.png",
                domain_tag=tag,
                case_start=ctx.case_start,
                orientation="we",
            ),
            _plot_domain_cross_section(
                path,
                domain_dir / "10_theta_xsection_sn.png",
                domain_tag=tag,
                case_start=ctx.case_start,
                orientation="sn",
            ),
        ]
    )
    return outputs


def _render(ctx: QuicklookContext, output_dir: Path) -> list[Path]:
    outputs: list[Path] = []
    for domain in ctx.domains:
        outputs.extend(_plot_domain_products(ctx, domain, output_dir))
    return outputs


def _check_inputs(ctx: QuicklookContext, *, verbose_manifest: bool) -> None:
    _verify_brc_tools_manifest(ctx.manifest_path, verbose=verbose_manifest)
    required_wrf_vars = [
        "XLONG",
        "XLAT",
        "HGT",
        "T2",
        "U10",
        "V10",
        "PBLH",
        "SNOWH",
        "TSK",
        "PSFC",
        "T",
        "PH",
        "PHB",
    ]
    for domain in ctx.domains:
        _require_vars(ctx.met_by_domain[domain], ["HGT_M", "XLONG_M", "XLAT_M"])
        _require_vars(ctx.wrf_by_domain[domain], required_wrf_vars)
    for domain in ctx.domains:
        print(f"WPS {_domain_tag(domain)}: {ctx.met_by_domain[domain]}")
    for domain in ctx.domains:
        print(f"WRF {_domain_tag(domain)}: {ctx.wrf_by_domain[domain]}")
    for domain in ctx.domains:
        print(f"quicklook {_domain_tag(domain)} products: 10")
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
                help=(
                    "directory for PNG output; default is "
                    "<archive-run>/quicklooks/standardized_<UTC>; repo-local paths are refused"
                ),
            )

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
