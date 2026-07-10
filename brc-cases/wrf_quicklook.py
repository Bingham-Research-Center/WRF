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
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import wrf_case


REPO_ROOT = Path(__file__).resolve().parents[1]
BRC_TOOLS_ROOT = (REPO_ROOT / "../brc-tools").resolve()
if str(BRC_TOOLS_ROOT) not in sys.path:
    sys.path.insert(0, str(BRC_TOOLS_ROOT))

STANDARD_SURFACE_PRODUCTS = (
    "t2_10m_wind",
    "t2_anomaly",
    "theta2_10m_wind",
    "10m_wind_speed",
    "pbl_height",
    "snow_depth",
    "skin_temperature",
    "surface_pressure",
)
SUPPLEMENTAL_SURFACE_PRODUCTS_4H = (
    "t2_10m_wind",
    "10m_wind_speed",
    "snow_depth",
)
SURFACE_ENERGY_PRODUCTS = (
    ("SWDOWN", "01_swdown.png", "downward shortwave radiation", "W m-2", "magma"),
    ("GLW", "02_glw.png", "downward longwave radiation", "W m-2", "viridis"),
    ("HFX", "03_hfx.png", "sensible heat flux", "W m-2", "RdBu_r"),
    ("LH", "04_lh.png", "latent heat flux", "W m-2", "RdBu_r"),
)


def _path_under(path: Path, parent: Path) -> bool:
    try:
        path.resolve(strict=False).relative_to(parent.resolve(strict=False))
        return True
    except ValueError:
        return False


def _default_output_dir(ctx: "QuicklookContext") -> Path:
    """Put review PNGs in the archive quicklooks directory, never in the repo."""
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


def _valid_time_for_lead(case_start: str, lead_hours: int) -> str:
    start = datetime.strptime(case_start, "%Y-%m-%d_%H:%M:%S")
    return (start + timedelta(hours=lead_hours)).strftime("%Y-%m-%d_%H:%M:%S")


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
    return f"BRC WRF quicklook | {path.name}"


def _theta_from_t_p(t_k: Any, p_pa: Any) -> Any:
    return t_k * (100000.0 / p_pa) ** 0.2854


def _symmetrical_limit(values: Any) -> float | None:
    import numpy as np

    finite = values[np.isfinite(values)]
    if finite.size == 0:
        return None
    limit = float(np.nanmax(np.abs(finite)))
    return limit if limit > 0.0 else None


def _interp_to_pressure(values: Any, pressure_pa: Any, target_pa: float) -> Any:
    import numpy as np

    field = np.asarray(values, dtype=float)
    pressure = np.asarray(pressure_pa, dtype=float)
    if field.shape != pressure.shape:
        raise ValueError(f"pressure interpolation shape mismatch: {field.shape} vs {pressure.shape}")

    p_inc = pressure[::-1, :, :]
    v_inc = field[::-1, :, :]
    nlev = p_inc.shape[0]
    idx_hi = np.sum(p_inc < target_pa, axis=0)
    inside = (idx_hi > 0) & (idx_hi < nlev)
    idx_hi = np.clip(idx_hi, 1, nlev - 1)
    idx_lo = idx_hi - 1

    p0 = np.take_along_axis(p_inc, idx_lo[np.newaxis, :, :], axis=0)[0]
    p1 = np.take_along_axis(p_inc, idx_hi[np.newaxis, :, :], axis=0)[0]
    v0 = np.take_along_axis(v_inc, idx_lo[np.newaxis, :, :], axis=0)[0]
    v1 = np.take_along_axis(v_inc, idx_hi[np.newaxis, :, :], axis=0)[0]

    denom = p1 - p0
    with np.errstate(invalid="ignore", divide="ignore"):
        weight = (target_pa - p0) / denom
        out = v0 + weight * (v1 - v0)
    out[~inside | ~np.isfinite(out) | (denom == 0.0)] = np.nan
    return out


def _relative_humidity_pct(pressure_pa: Any, temperature_k: Any, qvapor: Any) -> Any:
    import numpy as np

    pressure = np.asarray(pressure_pa, dtype=float)
    temp_c = np.asarray(temperature_k, dtype=float) - 273.15
    qv = np.maximum(np.asarray(qvapor, dtype=float), 0.0)
    vapor_pressure_hpa = (qv * pressure / (0.622 + qv)) / 100.0
    saturation_hpa = 6.112 * np.exp((17.67 * temp_c) / (temp_c + 243.5))
    with np.errstate(invalid="ignore", divide="ignore"):
        rh = 100.0 * vapor_pressure_hpa / saturation_hpa
    return np.clip(rh, 0.0, 150.0)


def _destagger_u_to_mass(u: Any, mass_shape: tuple[int, int, int]) -> Any:
    if u.shape == mass_shape:
        return u
    if u.shape[:2] == mass_shape[:2] and u.shape[2] == mass_shape[2] + 1:
        return 0.5 * (u[:, :, :-1] + u[:, :, 1:])
    raise ValueError(f"U wind shape {u.shape} is not compatible with mass grid {mass_shape}")


def _destagger_v_to_mass(v: Any, mass_shape: tuple[int, int, int]) -> Any:
    if v.shape == mass_shape:
        return v
    if v.shape[0] == mass_shape[0] and v.shape[1] == mass_shape[1] + 1 and v.shape[2] == mass_shape[2]:
        return 0.5 * (v[:, :-1, :] + v[:, 1:, :])
    raise ValueError(f"V wind shape {v.shape} is not compatible with mass grid {mass_shape}")


def _height_contour_levels(values: Any) -> Any:
    import numpy as np

    finite = np.asarray(values)[np.isfinite(values)]
    if finite.size == 0:
        return None
    low = float(np.nanmin(finite))
    high = float(np.nanmax(finite))
    if low == high:
        return None
    for interval in (30.0, 60.0, 90.0, 120.0, 180.0):
        start = np.floor(low / interval) * interval
        stop = np.ceil(high / interval) * interval
        levels = np.arange(start, stop + interval, interval)
        if 5 <= levels.size <= 24:
            return levels
    return np.linspace(low, high, 14)


def _wrfout_for_valid_time(ctx: QuicklookContext, domain: int, valid_time: str) -> Path:
    tag = _domain_tag(domain)
    return _find_first([ctx.archive_run / f"wrfout_{tag}_{valid_time}"], f"{tag} wrfout at {valid_time}")


def _plot_pressure_level_product(
    lon: Any,
    lat: Any,
    height_m: Any,
    rh_pct: Any,
    wind_u_ms: Any,
    wind_v_ms: Any,
    out_path: Path,
    *,
    domain_tag: str,
    valid_time: str,
    level_hpa: int,
    annotation: str | None = None,
    wind_max_barbs: int = 24,
) -> Path:
    import matplotlib
    import numpy as np

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    lon = np.asarray(lon)
    lat = np.asarray(lat)
    height = np.asarray(height_m)
    rh = np.asarray(rh_pct)
    u_kt = np.asarray(wind_u_ms) * 1.94384
    v_kt = np.asarray(wind_v_ms) * 1.94384

    fig, ax = plt.subplots(figsize=(8.5, 6.5), constrained_layout=True)
    mesh = ax.pcolormesh(
        lon,
        lat,
        rh,
        shading="nearest",
        cmap="YlGnBu",
        vmin=0.0,
        vmax=100.0,
        alpha=0.9,
    )
    fig.colorbar(mesh, ax=ax, shrink=0.8, label="RH %")

    height_levels = _height_contour_levels(height)
    if height_levels is not None:
        height_lines = ax.contour(
            lon,
            lat,
            height,
            levels=height_levels,
            colors="black",
            linewidths=0.45,
            alpha=0.7,
        )
        ax.clabel(height_lines, fontsize=5, fmt="%.0f m")

    rh_levels = np.arange(10.0, 101.0, 10.0)
    rh_lines = ax.contour(
        lon,
        lat,
        rh,
        levels=rh_levels,
        colors="#0f766e",
        linewidths=0.35,
        alpha=0.55,
    )
    ax.clabel(rh_lines, fontsize=4.5, fmt="%.0f%%")

    stride_y = max(1, u_kt.shape[0] // wind_max_barbs)
    stride_x = max(1, u_kt.shape[1] // wind_max_barbs)
    ax.barbs(
        lon[::stride_y, ::stride_x],
        lat[::stride_y, ::stride_x],
        u_kt[::stride_y, ::stride_x],
        v_kt[::stride_y, ::stride_x],
        length=5.0,
        linewidth=0.45,
        color="black",
        alpha=0.75,
    )

    ax.set_title(f"WRF {domain_tag} {level_hpa} hPa height, RH, and wind barbs, {valid_time}")
    ax.set_xlabel("longitude")
    ax.set_ylabel("latitude")
    if annotation:
        ax.text(
            0.99,
            0.01,
            annotation,
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


def _plot_domain_surface_products(
    path: Path,
    domain_dir: Path,
    *,
    domain_tag: str,
    valid_time: str,
    product_ids: tuple[str, ...],
) -> list[Path]:
    from brc_tools.visualize.grid import plot_grid_field, terrain_contour_levels

    import numpy as np

    outputs: list[Path] = []
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

        for product_id in product_ids:
            if product_id == "t2_10m_wind":
                outputs.append(
                    plot_grid_field(
                        lon,
                        lat,
                        t2_c,
                        domain_dir / "01_t2_10m_wind.png",
                        title=f"WRF {domain_tag} 2 m temperature and 10 m wind, {valid_time}",
                        colorbar_label="T2 deg C",
                        cmap="RdYlBu_r",
                        contour=hgt,
                        contour_levels=terrain_levels,
                        contour_label=True,
                        wind_u=u10,
                        wind_v=v10,
                        annotation=annotation,
                    )
                )
            elif product_id == "t2_anomaly":
                outputs.append(
                    plot_grid_field(
                        lon,
                        lat,
                        t2_anomaly,
                        domain_dir / "02_t2_anomaly.png",
                        title=f"WRF {domain_tag} 2 m temperature anomaly from domain median, {valid_time}",
                        colorbar_label="T2 anomaly deg C",
                        cmap="RdBu_r",
                        vmin=-anomaly_limit if anomaly_limit is not None else None,
                        vmax=anomaly_limit,
                        contour=hgt,
                        contour_levels=terrain_levels,
                        contour_label=True,
                        annotation=annotation,
                    )
                )
            elif product_id == "theta2_10m_wind":
                outputs.append(
                    plot_grid_field(
                        lon,
                        lat,
                        theta2,
                        domain_dir / "03_theta2_10m_wind.png",
                        title=f"WRF {domain_tag} 2 m potential temperature and 10 m wind, {valid_time}",
                        colorbar_label="theta2 K",
                        cmap="RdYlBu_r",
                        contour=hgt,
                        contour_levels=terrain_levels,
                        contour_label=True,
                        wind_u=u10,
                        wind_v=v10,
                        annotation=annotation,
                    )
                )
            elif product_id == "10m_wind_speed":
                outputs.append(
                    plot_grid_field(
                        lon,
                        lat,
                        wspd10,
                        domain_dir / "04_10m_wind_speed.png",
                        title=f"WRF {domain_tag} 10 m wind speed and vectors, {valid_time}",
                        colorbar_label="10 m wind speed m s-1",
                        cmap="viridis",
                        contour=hgt,
                        contour_levels=terrain_levels,
                        contour_label=True,
                        wind_u=u10,
                        wind_v=v10,
                        annotation=annotation,
                    )
                )
            elif product_id == "pbl_height":
                outputs.append(
                    plot_grid_field(
                        lon,
                        lat,
                        pblh,
                        domain_dir / "05_pbl_height.png",
                        title=f"WRF {domain_tag} PBL height, {valid_time}",
                        colorbar_label="PBLH m",
                        cmap="YlOrRd",
                        contour=hgt,
                        contour_levels=terrain_levels,
                        contour_label=True,
                        annotation=annotation,
                    )
                )
            elif product_id == "snow_depth":
                outputs.append(
                    plot_grid_field(
                        lon,
                        lat,
                        snowh,
                        domain_dir / "06_snow_depth.png",
                        title=f"WRF {domain_tag} snow depth, {valid_time}",
                        colorbar_label="SNOWH m",
                        cmap="Blues",
                        contour=hgt,
                        contour_levels=terrain_levels,
                        contour_label=True,
                        annotation=annotation,
                    )
                )
            elif product_id == "skin_temperature":
                outputs.append(
                    plot_grid_field(
                        lon,
                        lat,
                        tsk_c,
                        domain_dir / "07_skin_temperature.png",
                        title=f"WRF {domain_tag} skin temperature, {valid_time}",
                        colorbar_label="TSK deg C",
                        cmap="RdYlBu_r",
                        contour=hgt,
                        contour_levels=terrain_levels,
                        contour_label=True,
                        annotation=annotation,
                    )
                )
            elif product_id == "surface_pressure":
                outputs.append(
                    plot_grid_field(
                        lon,
                        lat,
                        psfc_hpa,
                        domain_dir / "08_surface_pressure.png",
                        title=f"WRF {domain_tag} surface pressure, {valid_time}",
                        colorbar_label="PSFC hPa",
                        cmap="viridis",
                        contour=hgt,
                        contour_levels=terrain_levels,
                        contour_label=True,
                        annotation=annotation,
                    )
                )
            else:
                raise ValueError(f"unknown surface quicklook product: {product_id}")
    return outputs


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
    tag = _domain_tag(domain)
    path = ctx.wrf_by_domain[domain]
    domain_dir = output_dir / tag
    outputs = _plot_domain_surface_products(
        path,
        domain_dir,
        domain_tag=tag,
        valid_time=ctx.case_start,
        product_ids=STANDARD_SURFACE_PRODUCTS,
    )

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


def _plot_domain_pressure_supplement(
    ctx: QuicklookContext,
    domain: int,
    output_dir: Path,
    *,
    level_hpa: int,
    lead_hours: int,
) -> list[Path]:
    import numpy as np

    tag = _domain_tag(domain)
    valid_time = _valid_time_for_lead(ctx.case_start, lead_hours)
    path = _wrfout_for_valid_time(ctx, domain, valid_time)
    target_pa = float(level_hpa) * 100.0

    with _open_dataset(path) as ds:
        pressure_pa = _as_3d(ds, "P").values + _as_3d(ds, "PB").values
        theta_k = _as_3d(ds, "T").values + 300.0
        temperature_k = theta_k * (pressure_pa / 100000.0) ** 0.2854
        qvapor = _as_3d(ds, "QVAPOR").values
        rh_pct = _relative_humidity_pct(pressure_pa, temperature_k, qvapor)

        z_w = (_as_3d(ds, "PH").values + _as_3d(ds, "PHB").values) / 9.80665
        height_m = 0.5 * (z_w[:-1, :, :] + z_w[1:, :, :])
        mass_shape = pressure_pa.shape
        u_ms = _destagger_u_to_mass(_as_3d(ds, "U").values, mass_shape)
        v_ms = _destagger_v_to_mass(_as_3d(ds, "V").values, mass_shape)

        sample_field = _as_2d(ds, "HGT")
        lon, lat = _coords(ds, "XLONG", "XLAT", sample_field)
        height_level = _interp_to_pressure(height_m, pressure_pa, target_pa)
        rh_level = _interp_to_pressure(rh_pct, pressure_pa, target_pa)
        u_level = _interp_to_pressure(u_ms, pressure_pa, target_pa)
        v_level = _interp_to_pressure(v_ms, pressure_pa, target_pa)

    if not np.isfinite(height_level).any():
        raise RuntimeError(f"{path} has no finite {level_hpa} hPa height values for {tag}")

    out_path = output_dir / tag / f"_{level_hpa}hPa" / f"01_{level_hpa}hPa_height_rh_wind_barbs.png"
    return [
        _plot_pressure_level_product(
            lon,
            lat,
            height_level,
            rh_level,
            u_level,
            v_level,
            out_path,
            domain_tag=tag,
            valid_time=valid_time,
            level_hpa=level_hpa,
            annotation=_annotation(path),
        )
    ]


def _plot_domain_4h_supplement(
    ctx: QuicklookContext,
    domain: int,
    output_dir: Path,
    *,
    lead_hours: int,
) -> list[Path]:
    tag = _domain_tag(domain)
    valid_time = _valid_time_for_lead(ctx.case_start, lead_hours)
    path = _wrfout_for_valid_time(ctx, domain, valid_time)
    return _plot_domain_surface_products(
        path,
        output_dir / tag / f"_{lead_hours}h",
        domain_tag=tag,
        valid_time=valid_time,
        product_ids=SUPPLEMENTAL_SURFACE_PRODUCTS_4H,
    )


def _plot_domain_surface_energy(
    ctx: QuicklookContext,
    domain: int,
    output_dir: Path,
    *,
    lead_hours: int,
) -> list[Path]:
    from brc_tools.visualize.grid import plot_grid_field, terrain_contour_levels

    tag = _domain_tag(domain)
    valid_time = _valid_time_for_lead(ctx.case_start, lead_hours)
    path = _wrfout_for_valid_time(ctx, domain, valid_time)
    outputs: list[Path] = []
    with _open_dataset(path) as ds:
        terrain = _as_2d(ds, "HGT")
        hgt = terrain.values
        lon, lat = _coords(ds, "XLONG", "XLAT", terrain)
        terrain_levels = terrain_contour_levels(hgt)
        annotation = _annotation(path)
        for variable, filename, label, units, cmap in SURFACE_ENERGY_PRODUCTS:
            values = _as_2d(ds, variable).values
            symmetric = variable in {"HFX", "LH"}
            limit = _symmetrical_limit(values) if symmetric else None
            outputs.append(
                plot_grid_field(
                    lon,
                    lat,
                    values,
                    output_dir / tag / f"_{lead_hours}h_energy" / filename,
                    title=f"WRF {tag} {label}, {valid_time}",
                    colorbar_label=f"{variable} {units}",
                    cmap=cmap,
                    vmin=-limit if limit is not None else None,
                    vmax=limit,
                    contour=hgt,
                    contour_levels=terrain_levels,
                    contour_label=True,
                    annotation=annotation,
                )
            )
    return outputs


def _render(ctx: QuicklookContext, output_dir: Path) -> list[Path]:
    outputs: list[Path] = []
    for domain in ctx.domains:
        outputs.extend(_plot_domain_products(ctx, domain, output_dir))
    return outputs


def _render_supplemental(
    ctx: QuicklookContext,
    output_dir: Path,
    *,
    pressure_level_hpa: int,
    pressure_lead_hours: int,
    surface_lead_hours: int,
) -> list[Path]:
    outputs: list[Path] = []
    for domain in ctx.domains:
        outputs.extend(
            _plot_domain_pressure_supplement(
                ctx,
                domain,
                output_dir,
                level_hpa=pressure_level_hpa,
                lead_hours=pressure_lead_hours,
            )
        )
        outputs.extend(
            _plot_domain_4h_supplement(
                ctx,
                domain,
                output_dir,
                lead_hours=surface_lead_hours,
            )
        )
    return outputs


def _check_surface_energy_inputs(
    ctx: QuicklookContext,
    *,
    verbose_manifest: bool,
    lead_hours: int,
) -> None:
    _verify_brc_tools_manifest(ctx.manifest_path, verbose=verbose_manifest)
    valid_time = _valid_time_for_lead(ctx.case_start, lead_hours)
    required = ["XLONG", "XLAT", "HGT", *[item[0] for item in SURFACE_ENERGY_PRODUCTS]]
    for domain in ctx.domains:
        path = _wrfout_for_valid_time(ctx, domain, valid_time)
        _require_vars(path, required)
        print(f"WRF {_domain_tag(domain)} {lead_hours}h surface-energy source: {path}")
        print(f"surface-energy {_domain_tag(domain)} products: {len(SURFACE_ENERGY_PRODUCTS)}")
    print(f"archive run: {ctx.archive_run}")


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


def _check_supplemental_inputs(
    ctx: QuicklookContext,
    *,
    verbose_manifest: bool,
    pressure_level_hpa: int,
    pressure_lead_hours: int,
    surface_lead_hours: int,
) -> None:
    _verify_brc_tools_manifest(ctx.manifest_path, verbose=verbose_manifest)
    pressure_valid_time = _valid_time_for_lead(ctx.case_start, pressure_lead_hours)
    surface_valid_time = _valid_time_for_lead(ctx.case_start, surface_lead_hours)
    pressure_vars = [
        "XLONG",
        "XLAT",
        "HGT",
        "P",
        "PB",
        "PH",
        "PHB",
        "T",
        "QVAPOR",
        "U",
        "V",
    ]
    surface_vars = ["XLONG", "XLAT", "HGT", "T2", "U10", "V10", "SNOWH", "PSFC", "PBLH", "TSK"]
    for domain in ctx.domains:
        pressure_path = _wrfout_for_valid_time(ctx, domain, pressure_valid_time)
        surface_path = _wrfout_for_valid_time(ctx, domain, surface_valid_time)
        _require_vars(pressure_path, pressure_vars)
        _require_vars(surface_path, surface_vars)
    for domain in ctx.domains:
        tag = _domain_tag(domain)
        print(
            f"WRF {tag} {pressure_level_hpa} hPa source: "
            f"{_wrfout_for_valid_time(ctx, domain, pressure_valid_time)}"
        )
        print(
            f"WRF {tag} {surface_lead_hours}h source: "
            f"{_wrfout_for_valid_time(ctx, domain, surface_valid_time)}"
        )
        print(f"supplemental {tag} products: 4")
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


def cmd_render_supplemental(args: argparse.Namespace) -> int:
    try:
        ctx = _load_context(args)
        _check_supplemental_inputs(
            ctx,
            verbose_manifest=args.verbose_manifest,
            pressure_level_hpa=args.pressure_level_hpa,
            pressure_lead_hours=args.pressure_lead_hours,
            surface_lead_hours=args.surface_lead_hours,
        )
        output_dir = _validate_output_dir(
            Path(args.output_dir) if args.output_dir else _default_output_dir(ctx)
        )
        outputs = _render_supplemental(
            ctx,
            output_dir,
            pressure_level_hpa=args.pressure_level_hpa,
            pressure_lead_hours=args.pressure_lead_hours,
            surface_lead_hours=args.surface_lead_hours,
        )
    except Exception as exc:  # noqa: BLE001 - CLI boundary
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    for path in outputs:
        print(f"wrote {path}")
    return 0


def cmd_render_surface_energy(args: argparse.Namespace) -> int:
    try:
        ctx = _load_context(args)
        _check_surface_energy_inputs(
            ctx,
            verbose_manifest=args.verbose_manifest,
            lead_hours=args.lead_hours,
        )
        output_dir = _validate_output_dir(
            Path(args.output_dir) if args.output_dir else _default_output_dir(ctx)
        )
        outputs: list[Path] = []
        for domain in ctx.domains:
            outputs.extend(
                _plot_domain_surface_energy(
                    ctx,
                    domain,
                    output_dir,
                    lead_hours=args.lead_hours,
                )
            )
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
                    "directory for PNG output; default is <archive-run>/quicklooks; "
                    "repo-local paths are refused"
                ),
            )

    cmd = subparsers.add_parser(
        "render-supplemental",
        help="render additive Pelican review products under each domain directory",
    )
    cmd.add_argument("case_file")
    cmd.add_argument(
        "--archive-run",
        help="specific archive run directory; defaults to the latest run_* under paths.archive_root",
    )
    cmd.add_argument(
        "--output-dir",
        help=(
            "domain-root directory for PNG output; default is <archive-run>/quicklooks; "
            "repo-local paths are refused"
        ),
    )
    cmd.add_argument(
        "--pressure-level-hpa",
        type=int,
        default=600,
        help="pressure level for the upper-air proof product; default: 600",
    )
    cmd.add_argument(
        "--pressure-lead-hours",
        type=int,
        default=1,
        help="forecast lead hour for the pressure-level product; default: 1",
    )
    cmd.add_argument(
        "--surface-lead-hours",
        type=int,
        default=4,
        help="forecast lead hour for the copied surface products; default: 4",
    )
    cmd.add_argument(
        "--verbose-manifest",
        action="store_true",
        help="print every brc-tools manifest verification row",
    )
    cmd.set_defaults(func=cmd_render_supplemental)

    cmd = subparsers.add_parser(
        "render-surface-energy",
        help="render additive SWDOWN, GLW, HFX, and LH treatment diagnostics",
    )
    cmd.add_argument("case_file")
    cmd.add_argument(
        "--archive-run",
        help="specific archive run directory; defaults to the latest run_* under paths.archive_root",
    )
    cmd.add_argument(
        "--output-dir",
        help=(
            "domain-root directory for PNG output; default is <archive-run>/quicklooks; "
            "repo-local paths are refused"
        ),
    )
    cmd.add_argument(
        "--lead-hours",
        type=int,
        default=4,
        help="forecast lead hour for surface-energy products; default: 4",
    )
    cmd.add_argument(
        "--verbose-manifest",
        action="store_true",
        help="print every brc-tools manifest verification row",
    )
    cmd.set_defaults(func=cmd_render_surface_energy)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
