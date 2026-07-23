#!/usr/bin/env python3
"""Prepare custom WPS static HGT_M terrain datasets.

This helper builds a WPS geogrid-compatible continuous topography directory
from DEM rasters and can render/cache an approval-gated Slurm acquisition
packet. It does not submit Slurm, run geogrid, or inspect WRF NetCDF output.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
import re
import shutil
import shlex
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import quote, urlencode, urlparse
from urllib.request import Request, urlopen


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_TOKEN = "brc_custom_3s"
DEFAULT_REL_PATH = "topo_brc_custom_3s"
DEFAULT_DX_DEG = 3.0 / 3600.0
DEFAULT_TILE_SIZE = 1200
DEFAULT_TILE_BORDER = 3
DEFAULT_PELICAN_BOUNDS = (-114.0, 37.0, -105.0, 44.0)
DEFAULT_INTERP = "average_gcell(4.0)+four_pt+average_4pt"
DEFAULT_USGS_DATASET = "National Elevation Dataset (NED) 1 arc-second"
DEFAULT_TNM_ENDPOINT = "https://tnmaccess.nationalmap.gov/api/v1/products"
DEFAULT_LOG_ROOT = Path("/uufs/chpc.utah.edu/common/home/lawson-group6/jrlawson/wrf_build_logs/brc-wrf")


@dataclass(frozen=True)
class Tile:
    x_start: int
    x_end: int
    y_start: int
    y_end: int

    @property
    def name(self) -> str:
        return f"{self.x_start:05d}-{self.x_end:05d}.{self.y_start:05d}-{self.y_end:05d}"


@dataclass(frozen=True)
class ManifestRow:
    url: str
    filename: str
    bytes_expected: int | None = None
    sha256_expected: str = ""
    title: str = ""


def shell_quote(value: object) -> str:
    return shlex.quote(str(value))


def _utc_id() -> str:
    return time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())


def _path_under(path: Path, parent: Path) -> bool:
    try:
        path.resolve(strict=False).relative_to(parent.resolve(strict=False))
        return True
    except ValueError:
        return False


def _require_outside_repo(path: Path, label: str) -> None:
    if _path_under(path, REPO_ROOT):
        raise ValueError(f"{label} must not be inside the brc-wrf checkout: {path}")


def _safe_filename(value: str, fallback: str) -> str:
    basename = Path(urlparse(value).path).name or fallback
    basename = re.sub(r"[^A-Za-z0-9._+-]+", "_", basename).strip("._")
    return basename or fallback


def _clean_int(value: object) -> int | None:
    if value in (None, ""):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _format_bounds(bounds: tuple[float, float, float, float]) -> str:
    return ",".join(f"{v:g}" for v in bounds)


def read_manifest(path: Path) -> list[ManifestRow]:
    with path.open("r", encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh, delimiter="\t")
        required = {"url", "filename"}
        missing = required.difference(reader.fieldnames or [])
        if missing:
            raise ValueError(f"{path} missing required columns: {', '.join(sorted(missing))}")
        rows = []
        for raw in reader:
            url = (raw.get("url") or "").strip()
            filename = (raw.get("filename") or "").strip()
            if not url or not filename:
                continue
            rows.append(
                ManifestRow(
                    url=url,
                    filename=_safe_filename(filename, "dem.dat"),
                    bytes_expected=_clean_int(raw.get("bytes")),
                    sha256_expected=(raw.get("sha256") or "").strip().lower(),
                    title=(raw.get("title") or "").strip(),
                )
            )
    if not rows:
        raise ValueError(f"{path} did not contain any downloadable rows")
    return rows


def write_manifest(path: Path, rows: list[ManifestRow]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(
            fh,
            fieldnames=["url", "filename", "bytes", "sha256", "title"],
            delimiter="\t",
            lineterminator="\n",
        )
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    "url": row.url,
                    "filename": row.filename,
                    "bytes": "" if row.bytes_expected is None else row.bytes_expected,
                    "sha256": row.sha256_expected,
                    "title": row.title,
                }
            )


def _extract_download_url(item: dict[str, object]) -> str:
    for key in ("downloadURL", "downloadUrl", "download_url", "url"):
        value = item.get(key)
        if isinstance(value, str) and value.startswith(("http://", "https://")):
            return value
    urls = item.get("urls")
    if isinstance(urls, dict):
        for value in urls.values():
            if isinstance(value, str) and value.startswith(("http://", "https://")):
                return value
    raise ValueError(f"could not find download URL in TNM item keys: {sorted(item)}")


def _source_tile_key(*values: str) -> str:
    for value in values:
        match = re.search(r"\b[ns]\d{2}[ew]\d{3}\b", value, flags=re.IGNORECASE)
        if match:
            return match.group(0).lower()
    return ""


def _source_version_key(item: dict[str, object], url: str, title: str) -> tuple[int, str]:
    date = 0
    for value in (title, url, str(item.get("publicationDate") or ""), str(item.get("lastUpdated") or "")):
        match = re.search(r"(20\d{6})", value)
        if match:
            date = max(date, int(match.group(1)))
    current_bonus = 1 if "/current/" in url else 0
    return current_bonus, f"{date:08d}:{title}:{url}"


def query_usgs_manifest(
    *,
    bounds: tuple[float, float, float, float],
    dataset: str = DEFAULT_USGS_DATASET,
    prod_format: str = "GeoTIFF",
    endpoint: str = DEFAULT_TNM_ENDPOINT,
    max_products: int = 500,
    timeout: int = 60,
) -> list[ManifestRow]:
    params = {
        "datasets": dataset,
        "bbox": _format_bounds(bounds),
        "prodFormats": prod_format,
        "max": str(max_products),
    }
    request_url = f"{endpoint}?{urlencode(params, quote_via=quote)}"
    req = Request(request_url, headers={"User-Agent": "brc-wrf-wps-hgt-static/1"})
    with urlopen(req, timeout=timeout) as response:
        payload = json.loads(response.read().decode("utf-8"))
    items = payload.get("items")
    if not isinstance(items, list):
        raise ValueError(f"TNM response lacks an items list: {request_url}")
    by_tile: dict[str, tuple[tuple[int, str], ManifestRow]] = {}
    untiled: list[ManifestRow] = []
    for idx, item in enumerate(items, start=1):
        if not isinstance(item, dict):
            continue
        url = _extract_download_url(item)
        title = str(item.get("title") or item.get("name") or "")
        filename = _safe_filename(url, f"usgs_3dep_{idx:03d}.tif")
        row = ManifestRow(
            url=url,
            filename=filename,
            bytes_expected=_clean_int(item.get("sizeInBytes") or item.get("size")),
            title=title,
        )
        tile_key = _source_tile_key(filename, title, url)
        if tile_key:
            version_key = _source_version_key(item, url, title)
            if tile_key not in by_tile or version_key > by_tile[tile_key][0]:
                by_tile[tile_key] = (version_key, row)
        else:
            untiled.append(row)
    rows = [value[1] for value in by_tile.values()] + untiled
    if not rows:
        raise ValueError(f"TNM query returned no products: {request_url}")
    return sorted(rows, key=lambda row: row.filename)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _verify_cached(path: Path, row: ManifestRow, *, compute_hash: bool, strict_bytes: bool) -> tuple[bool, str]:
    if not path.exists() or path.stat().st_size == 0:
        return False, ""
    if strict_bytes and row.bytes_expected is not None and path.stat().st_size != row.bytes_expected:
        return False, ""
    if row.sha256_expected:
        actual = _sha256(path)
        return actual == row.sha256_expected, actual
    if compute_hash:
        return True, _sha256(path)
    return True, ""


def download_manifest(
    *,
    manifest: Path,
    output_dir: Path,
    inventory: Path,
    timeout: int = 120,
    retries: int = 3,
    compute_hash: bool = True,
    force: bool = False,
    strict_bytes: bool = False,
    min_free_gb: float = 5.0,
) -> list[dict[str, object]]:
    output_dir = output_dir.resolve()
    _require_outside_repo(output_dir, "DEM download cache")
    output_dir.mkdir(parents=True, exist_ok=True)
    free_gb = shutil.disk_usage(output_dir).free / (1024**3)
    if free_gb < min_free_gb:
        raise RuntimeError(f"{output_dir} has only {free_gb:.1f} GiB free; require {min_free_gb:.1f} GiB")
    rows = read_manifest(manifest)
    results: list[dict[str, object]] = []
    for row in rows:
        dest = output_dir / row.filename
        ok, digest = _verify_cached(dest, row, compute_hash=compute_hash, strict_bytes=strict_bytes)
        if ok and not force:
            note = ""
            if row.bytes_expected is not None and dest.stat().st_size != row.bytes_expected:
                note = f"metadata_bytes={row.bytes_expected}"
            results.append(
                {
                    "status": "cached",
                    "path": dest,
                    "bytes": dest.stat().st_size,
                    "sha256": digest,
                    "url": row.url,
                    "error": note,
                }
            )
            continue
        part = dest.with_name(f"{dest.name}.part")
        last_error = ""
        for attempt in range(1, retries + 1):
            try:
                req = Request(row.url, headers={"User-Agent": "brc-wrf-wps-hgt-static/1"})
                digest_obj = hashlib.sha256()
                byte_count = 0
                with urlopen(req, timeout=timeout) as response, part.open("wb") as out:
                    for chunk in iter(lambda: response.read(1024 * 1024), b""):
                        if not chunk:
                            break
                        out.write(chunk)
                        byte_count += len(chunk)
                        digest_obj.update(chunk)
                if strict_bytes and row.bytes_expected is not None and byte_count != row.bytes_expected:
                    raise RuntimeError(f"downloaded {byte_count} bytes, expected {row.bytes_expected}")
                digest = digest_obj.hexdigest()
                if row.sha256_expected and digest != row.sha256_expected:
                    raise RuntimeError(f"sha256 mismatch: {digest} != {row.sha256_expected}")
                part.replace(dest)
                note = ""
                if row.bytes_expected is not None and byte_count != row.bytes_expected:
                    note = f"metadata_bytes={row.bytes_expected}"
                results.append(
                    {
                        "status": "downloaded",
                        "path": dest,
                        "bytes": byte_count,
                        "sha256": digest,
                        "url": row.url,
                        "error": note,
                    }
                )
                break
            except Exception as exc:  # noqa: BLE001 - preserve source error in inventory.
                last_error = str(exc)
                if attempt == retries:
                    results.append({"status": "ERROR", "path": dest, "bytes": 0, "sha256": "", "url": row.url, "error": last_error})
                else:
                    time.sleep(min(30, attempt * 5))
        if results[-1]["status"] == "ERROR":
            break
    inventory.parent.mkdir(parents=True, exist_ok=True)
    with inventory.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(
            fh,
            fieldnames=["status", "path", "bytes", "sha256", "url", "error"],
            delimiter="\t",
            lineterminator="\n",
        )
        writer.writeheader()
        for result in results:
            writer.writerow(
                {
                    "status": result.get("status", ""),
                    "path": result.get("path", ""),
                    "bytes": result.get("bytes", ""),
                    "sha256": result.get("sha256", ""),
                    "url": result.get("url", ""),
                    "error": result.get("error", ""),
                }
            )
    errors = [result for result in results if result["status"] == "ERROR"]
    if errors:
        raise RuntimeError(f"{len(errors)} download(s) failed; see {inventory}")
    return results


def paths_from_inventory(path: Path) -> list[Path]:
    with path.open("r", encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh, delimiter="\t")
        paths = [Path(row["path"]) for row in reader if row.get("status") in {"cached", "downloaded"} and row.get("path")]
    if not paths:
        raise ValueError(f"{path} contains no cached/downloaded DEM paths")
    return paths


def _lon_0360(lon: float) -> float:
    value = lon % 360.0
    if math.isclose(value, 360.0):
        return 0.0
    return value


def normalize_bounds(bounds: tuple[float, float, float, float]) -> tuple[float, float, float, float]:
    min_lon, min_lat, max_lon, max_lat = bounds
    if min_lat >= max_lat:
        raise ValueError("bounds require min_lat < max_lat")
    left = _lon_0360(min_lon)
    right = _lon_0360(max_lon)
    if right <= left:
        raise ValueError("bounds crossing the dateline are not supported by this helper")
    return left, min_lat, right, max_lat


def tiles_for_bounds(
    bounds: tuple[float, float, float, float],
    *,
    dx_deg: float = DEFAULT_DX_DEG,
    tile_size: int = DEFAULT_TILE_SIZE,
) -> list[Tile]:
    left, min_lat, right, max_lat = normalize_bounds(bounds)
    nx = int(round(360.0 / dx_deg))
    ny = int(round(180.0 / dx_deg))
    x_min = max(1, int(math.floor(left / dx_deg)) + 1)
    x_max = min(nx, int(math.ceil(right / dx_deg)))
    y_min = max(1, int(math.floor((min_lat + 90.0) / dx_deg)) + 1)
    y_max = min(ny, int(math.ceil((max_lat + 90.0) / dx_deg)))
    if x_min > x_max or y_min > y_max:
        raise ValueError("bounds do not intersect the regular lat/lon grid")

    x0 = ((x_min - 1) // tile_size) * tile_size + 1
    y0 = ((y_min - 1) // tile_size) * tile_size + 1
    tiles: list[Tile] = []
    for xs in range(x0, x_max + 1, tile_size):
        xe = min(xs + tile_size - 1, nx)
        for ys in range(y0, y_max + 1, tile_size):
            ye = min(ys + tile_size - 1, ny)
            tiles.append(Tile(xs, xe, ys, ye))
    return tiles


def source_bounds_for_tiles(
    bounds: tuple[float, float, float, float],
    *,
    dx_deg: float = DEFAULT_DX_DEG,
    tile_size: int = DEFAULT_TILE_SIZE,
    tile_border: int = DEFAULT_TILE_BORDER,
) -> tuple[float, float, float, float]:
    windows = [
        tile_projwin(tile, dx_deg=dx_deg, tile_border=tile_border)
        for tile in tiles_for_bounds(bounds, dx_deg=dx_deg, tile_size=tile_size)
    ]
    left = min(window[0] for window in windows)
    north = max(window[1] for window in windows)
    right = max(window[2] for window in windows)
    south = min(window[3] for window in windows)
    return left, south, right, north


def _lon_from_0360(lon: float) -> float:
    if lon > 180.0:
        return lon - 360.0
    return lon


def tile_projwin(
    tile: Tile,
    *,
    dx_deg: float = DEFAULT_DX_DEG,
    tile_border: int = DEFAULT_TILE_BORDER,
) -> tuple[float, float, float, float]:
    left_0360 = (tile.x_start - 1 - tile_border) * dx_deg
    right_0360 = (tile.x_end + tile_border) * dx_deg
    if left_0360 < 0.0 or right_0360 > 360.0:
        raise ValueError(f"tile {tile.name} crosses global longitude boundary")
    left = _lon_from_0360(left_0360)
    right = _lon_from_0360(right_0360)
    if right <= left:
        raise ValueError(f"tile {tile.name} crosses the dateline")
    south = -90.0 + (tile.y_start - 1 - tile_border) * dx_deg
    north = -90.0 + (tile.y_end + tile_border) * dx_deg
    return left, north, right, south


def filename_digits_for_grid(dx_deg: float, *, tile_size: int = DEFAULT_TILE_SIZE) -> int:
    max_index = max(int(round(360.0 / dx_deg)), int(round(180.0 / dx_deg)))
    if max_index <= 99999:
        return 5
    if max_index <= 999999:
        return 6
    raise ValueError("WPS geogrid supports only 5- or 6-digit static tile filenames")


def filename_digits_for_tiles(tiles: list[Tile]) -> int:
    """Digit width (5 or 6) needed to name the tiles that actually occur in-region.

    ``filename_digits_for_grid`` sizes from the *global* grid width and refuses
    anything past 6 digits, so a true 1-arc-second build is rejected because the
    global 1s grid reaches 1_296_000 (7 digits). A *regional* build only spans a
    handful of tiles, whose indices are far smaller: a 1s box over Utah tops out
    near 903_600 (6 digits) and is perfectly representable. Sizing from the
    in-region tiles is therefore what unlocks a regional 1s build while leaving
    the existing 3s (max index ~432_000 -> 6) and 30s (~43_200 -> 5) builds byte
    identical, since their regional maxima land in the same 5/6-digit bucket.
    """
    if not tiles:
        raise ValueError("cannot size filename digits from an empty tile list")
    max_index = max(max(tile.x_end, tile.y_end) for tile in tiles)
    if max_index <= 99999:
        return 5
    if max_index <= 999999:
        return 6
    raise ValueError(
        "WPS geogrid static tiles support at most 6-digit filenames; in-region "
        f"tile index {max_index} needs {len(str(max_index))} digits -- shrink the region"
    )


def resolve_filename_digits(tiles: list[Tile], override: int | None) -> int:
    """Pick the static-tile filename digit width for a regional build.

    Without an override the width is derived from the in-region tiles (see
    ``filename_digits_for_tiles``). An explicit ``--filename-digits`` override is
    honored only when it is a legal WPS width (5 or 6) and wide enough to name
    every in-region tile, so it can never silently truncate a tile index.
    """
    region_digits = filename_digits_for_tiles(tiles)
    if override is None:
        return region_digits
    if override not in (5, 6):
        raise ValueError("--filename-digits must be 5 or 6")
    if override < region_digits:
        raise ValueError(
            f"--filename-digits {override} is too narrow for this region; it needs "
            f"at least {region_digits} to name the in-region tiles"
        )
    return override


def tile_name(tile: Tile, *, filename_digits: int) -> str:
    if filename_digits not in {5, 6}:
        raise ValueError("filename_digits must be 5 or 6")
    return (
        f"{tile.x_start:0{filename_digits}d}-{tile.x_end:0{filename_digits}d}."
        f"{tile.y_start:0{filename_digits}d}-{tile.y_end:0{filename_digits}d}"
    )


def index_text(
    *,
    dx_deg: float = DEFAULT_DX_DEG,
    tile_size: int = DEFAULT_TILE_SIZE,
    tile_border: int = DEFAULT_TILE_BORDER,
    filename_digits: int | None = None,
    description: str = "Custom 3-arc-second topography height for BRC WRF",
) -> str:
    known = dx_deg / 2.0
    if filename_digits is None:
        filename_digits = filename_digits_for_grid(dx_deg, tile_size=tile_size)
    return "\n".join(
        [
            "type = continuous",
            "signed = yes",
            "projection = regular_ll",
            f"dx = {dx_deg:.15g}",
            f"dy = {dx_deg:.15g}",
            "known_x = 1.0",
            "known_y = 1.0",
            f"known_lat = {-90.0 + known:.15g}",
            f"known_lon = {known:.15g}",
            "wordsize = 2",
            f"tile_x = {tile_size}",
            f"tile_y = {tile_size}",
            "tile_z = 1",
            f"filename_digits = {filename_digits}",
            f"tile_bdr={tile_border}",
            'units="meters MSL"',
            f'description="{description}"',
            "",
        ]
    )


def patch_geogrid_table_text(
    text: str,
    *,
    token: str = DEFAULT_TOKEN,
    rel_path: str = DEFAULT_REL_PATH,
    interp: str = DEFAULT_INTERP,
) -> str:
    if f"{token}:" in text:
        return text
    lines = text.splitlines()
    out: list[str] = []
    in_hgt = False
    inserted_interp = False
    inserted_rel = False
    for line in lines:
        stripped = line.strip()
        if re.match(r"^name\s*=", stripped):
            in_hgt = re.match(r"^name\s*=\s*HGT_M\s*$", stripped) is not None
        if in_hgt and not inserted_interp and stripped.startswith("interp_option"):
            prefix = line[: len(line) - len(line.lstrip())]
            out.append(f"{prefix}interp_option = {token}:{interp}")
            inserted_interp = True
        if in_hgt and not inserted_rel and stripped.startswith("rel_path"):
            prefix = line[: len(line) - len(line.lstrip())]
            out.append(f"{prefix}rel_path = {token}:{rel_path}/")
            inserted_rel = True
        out.append(line)
    if not inserted_interp or not inserted_rel:
        raise ValueError("could not find HGT_M interp_option and rel_path entries in GEOGRID.TBL")
    return "\n".join(out) + "\n"


def _count_geog_res_entries(line: str) -> int:
    return line.count("'") // 2


def render_namelist_text(
    text: str,
    *,
    token: str = DEFAULT_TOKEN,
    geog_data_path: Path,
) -> str:
    lines = text.splitlines()
    out: list[str] = []
    replaced_res = False
    replaced_path = False
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("geog_data_res"):
            count = max(1, _count_geog_res_entries(line))
            value = ",".join([f"'{token}+default'"] * count)
            prefix = line[: len(line) - len(line.lstrip())]
            out.append(f"{prefix}geog_data_res     = {value},")
            replaced_res = True
        elif stripped.startswith("geog_data_path"):
            prefix = line[: len(line) - len(line.lstrip())]
            path = str(geog_data_path)
            if not path.endswith("/"):
                path += "/"
            out.append(f"{prefix}geog_data_path = '{path}'")
            replaced_path = True
        else:
            out.append(line)
    if not replaced_res or not replaced_path:
        raise ValueError("could not replace geog_data_res and geog_data_path in namelist.wps")
    return "\n".join(out) + "\n"


def _run(cmd: list[str]) -> None:
    subprocess.run(cmd, check=True)


def _need_tool(name: str) -> str:
    found = shutil.which(name)
    if not found:
        raise RuntimeError(f"required GDAL tool not found on PATH: {name}")
    return found


def _parse_envi_byte_order(header: Path) -> int:
    for line in header.read_text(encoding="utf-8", errors="replace").splitlines():
        key, sep, value = line.partition("=")
        if sep and key.strip().lower() == "byte order":
            return int(value.strip())
    raise ValueError(f"could not determine ENVI byte order from {header}")


def _write_wps_tile_from_envi(raw_path: Path, header_path: Path, dest: Path, width: int, height: int) -> None:
    byte_order = _parse_envi_byte_order(header_path)
    row_bytes = width * 2
    data = raw_path.read_bytes()
    expected = row_bytes * height
    if len(data) != expected:
        raise ValueError(f"{raw_path} has {len(data)} bytes, expected {expected}")
    rows = [data[i : i + row_bytes] for i in range(0, len(data), row_bytes)]
    dest.parent.mkdir(parents=True, exist_ok=True)
    with dest.open("wb") as fh:
        for row in reversed(rows):
            if byte_order == 0:
                swapped = bytearray(len(row))
                swapped[0::2] = row[1::2]
                swapped[1::2] = row[0::2]
                fh.write(swapped)
            elif byte_order == 1:
                fh.write(row)
            else:
                raise ValueError(f"unsupported ENVI byte order {byte_order}")


def build_tiles(args: argparse.Namespace) -> None:
    output_dir = args.output_dir.resolve()
    _require_outside_repo(output_dir, "static-data output")
    output_dir.mkdir(parents=True, exist_ok=True)
    build_dir = output_dir / "_build"
    build_dir.mkdir(parents=True, exist_ok=True)
    tile_width = args.tile_size + 2 * args.tile_border
    tile_height = args.tile_size + 2 * args.tile_border
    bounds = tuple(args.bounds)
    tiles = tiles_for_bounds(bounds, dx_deg=args.dx_deg, tile_size=args.tile_size)
    filename_digits = resolve_filename_digits(tiles, getattr(args, "filename_digits", None))

    gdalbuildvrt = _need_tool("gdalbuildvrt")
    gdalwarp = _need_tool("gdalwarp")
    gdal_translate = _need_tool("gdal_translate")
    source_vrt = build_dir / "source.vrt"
    warped_vrt = build_dir / "source_epsg4326.vrt"
    _run([gdalbuildvrt, "-overwrite", str(source_vrt), *[str(p) for p in args.source_dem]])
    _run(
        [
            gdalwarp,
            "-overwrite",
            "-of",
            "VRT",
            "-t_srs",
            "EPSG:4326",
            "-r",
            args.resampling,
            "-tr",
            f"{args.dx_deg:.15g}",
            f"{args.dx_deg:.15g}",
            str(source_vrt),
            str(warped_vrt),
        ]
    )

    output_dir.joinpath("index").write_text(
        index_text(
            dx_deg=args.dx_deg,
            tile_size=args.tile_size,
            tile_border=args.tile_border,
            filename_digits=filename_digits,
            description=args.description,
        ),
        encoding="utf-8",
    )

    for tile in tiles:
        left, north, right, south = tile_projwin(tile, dx_deg=args.dx_deg, tile_border=args.tile_border)
        name = tile_name(tile, filename_digits=filename_digits)
        raw = build_dir / f"{name}.envi"
        header = Path(f"{raw}.hdr")
        _run(
            [
                gdal_translate,
                "-q",
                "-of",
                "ENVI",
                "-ot",
                "Int16",
                "-r",
                args.resampling,
                "-projwin_srs",
                "EPSG:4326",
                "-projwin",
                f"{left:.12f}",
                f"{north:.12f}",
                f"{right:.12f}",
                f"{south:.12f}",
                "-outsize",
                str(tile_width),
                str(tile_height),
                "-epo",
                "-co",
                "INTERLEAVE=BSQ",
                "-co",
                "SUFFIX=ADD",
                str(warped_vrt),
                str(raw),
            ]
        )
        _write_wps_tile_from_envi(raw, header, output_dir / name, tile_width, tile_height)


def cmd_plan(args: argparse.Namespace) -> int:
    bounds = tuple(args.bounds)
    tiles = tiles_for_bounds(bounds, dx_deg=args.dx_deg, tile_size=args.tile_size)
    filename_digits = resolve_filename_digits(tiles, getattr(args, "filename_digits", None))
    print("tile\tleft\tright\tsouth\tnorth")
    for tile in tiles:
        left, north, right, south = tile_projwin(tile, dx_deg=args.dx_deg, tile_border=args.tile_border)
        print(f"{tile_name(tile, filename_digits=filename_digits)}\t{left:.6f}\t{right:.6f}\t{south:.6f}\t{north:.6f}")
    print()
    print(
        index_text(
            dx_deg=args.dx_deg,
            tile_size=args.tile_size,
            tile_border=args.tile_border,
            filename_digits=filename_digits,
        ),
        end="",
    )
    return 0


def cmd_build(args: argparse.Namespace) -> int:
    for source in args.source_dem:
        if not source.exists():
            raise FileNotFoundError(source)
    build_tiles(args)
    return 0


def cmd_patch_geogrid(args: argparse.Namespace) -> int:
    text = args.base.read_text(encoding="utf-8")
    patched = patch_geogrid_table_text(text, token=args.token, rel_path=args.rel_path, interp=args.interp)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(patched, encoding="utf-8")
    return 0


def cmd_render_namelist(args: argparse.Namespace) -> int:
    text = args.template.read_text(encoding="utf-8")
    rendered = render_namelist_text(text, token=args.token, geog_data_path=args.geog_data_path)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(rendered, encoding="utf-8")
    return 0


def cmd_query_usgs(args: argparse.Namespace) -> int:
    bounds = tuple(args.bounds)
    if args.expand_for_wps:
        bounds = source_bounds_for_tiles(
            bounds,
            dx_deg=args.dx_deg,
            tile_size=args.tile_size,
            tile_border=args.tile_border,
        )
    rows = query_usgs_manifest(
        bounds=bounds,
        dataset=args.dataset,
        prod_format=args.prod_format,
        endpoint=args.endpoint,
        max_products=args.max_products,
        timeout=args.timeout,
    )
    write_manifest(args.output, rows)
    print(f"wrote {len(rows)} USGS product row(s) to {args.output}")
    return 0


def cmd_download_manifest(args: argparse.Namespace) -> int:
    results = download_manifest(
        manifest=args.manifest,
        output_dir=args.output_dir,
        inventory=args.inventory,
        timeout=args.timeout,
        retries=args.retries,
        compute_hash=not args.skip_hash,
        force=args.force,
        strict_bytes=args.strict_bytes,
        min_free_gb=args.min_free_gb,
    )
    cached = sum(1 for result in results if result["status"] == "cached")
    downloaded = sum(1 for result in results if result["status"] == "downloaded")
    total_bytes = sum(int(result.get("bytes") or 0) for result in results)
    print(f"cached={cached} downloaded={downloaded} bytes={total_bytes} inventory={args.inventory}")
    return 0


def cmd_build_from_inventory(args: argparse.Namespace) -> int:
    args.source_dem = paths_from_inventory(args.inventory)
    build_tiles(args)
    return 0


def _slurm_line(name: str, value: object | None) -> str | None:
    if value in (None, ""):
        return None
    return f"#SBATCH --{name}={value}"


def render_slurm_packet(args: argparse.Namespace) -> None:
    packet_dir = args.packet_dir.resolve()
    _require_outside_repo(packet_dir, "Slurm packet output")
    packet_dir.mkdir(parents=True, exist_ok=True)

    user = os.environ.get("USER", "u0737349")
    run_id = args.run_id or f"terrain_{_utc_id()}"
    safe_case = re.sub(r"[^A-Za-z0-9._+-]+", "_", args.case_name).strip("_")
    geog_data_path = args.geog_data_path or Path(f"/scratch/general/vast/{user}/wps_geog_static/{safe_case}")
    static_output_dir = args.static_output_dir or geog_data_path / args.rel_path
    download_dir = args.download_dir or Path(f"/scratch/general/vast/{user}/wrf_inputs/{safe_case}/terrain_dem_cache")
    manifest = packet_dir / "terrain_urls.tsv"
    inventory = packet_dir / "terrain_download_inventory.tsv"
    log_root = args.log_root
    helper = REPO_ROOT / "brc-cases" / "wps_hgt_static.py"
    bounds = " ".join(f"{v:g}" for v in args.bounds)
    source_bounds = source_bounds_for_tiles(tuple(args.bounds))
    source_bounds_arg = " ".join(f"{v:g}" for v in source_bounds)

    headers_download = [
        "#!/bin/bash",
        "# Rendered by brc-cases/wps_hgt_static.py; static terrain acquisition only.",
        f"#SBATCH --job-name=terrain-dl-{safe_case[:20]}",
        _slurm_line("account", args.download_account),
        _slurm_line("partition", args.download_partition),
        _slurm_line("qos", args.download_qos),
        "#SBATCH --nodes=1",
        "#SBATCH --ntasks=1",
        f"#SBATCH --mem={args.download_mem}",
        f"#SBATCH --time={args.download_time}",
        _slurm_line("chdir", packet_dir),
        _slurm_line("output", log_root / f"terrain_download_{safe_case}_%j.out"),
        _slurm_line("error", log_root / f"terrain_download_{safe_case}_%j.err"),
    ]
    download_lines = [line for line in headers_download if line]
    download_lines.extend(
        [
            "",
            "set -euo pipefail",
            'PYTHON_BIN="${PYTHON_BIN:-python3}"',
            f"mkdir -p {shell_quote(download_dir)} {shell_quote(log_root)}",
            f"echo \"terrain download start $(date -u +%Y-%m-%dT%H:%M:%SZ) host=$(hostname)\"",
        ]
    )
    if args.source_manifest:
        download_lines.append(f"cp {shell_quote(args.source_manifest)} {shell_quote(manifest)}")
    else:
        download_lines.extend(
            [
                '"${PYTHON_BIN}" '
                f"{shell_quote(helper)} query-usgs --bounds {source_bounds_arg} "
                f"--dataset {shell_quote(args.usgs_dataset)} --prod-format {shell_quote(args.usgs_format)} "
                f"--max-products {args.max_products} --output {shell_quote(manifest)}",
            ]
        )
    download_lines.extend(
        [
            '"${PYTHON_BIN}" '
            f"{shell_quote(helper)} download-manifest --manifest {shell_quote(manifest)} "
            f"--output-dir {shell_quote(download_dir)} --inventory {shell_quote(inventory)} "
            f"--timeout {args.timeout} --retries {args.retries} --min-free-gb {args.min_free_gb}",
            f"du -sh {shell_quote(download_dir)} | tee {shell_quote(packet_dir / 'terrain_download_du.txt')}",
            f"echo \"terrain download stop $(date -u +%Y-%m-%dT%H:%M:%SZ)\"",
            "",
        ]
    )

    headers_build = [
        "#!/bin/bash",
        "# Rendered by brc-cases/wps_hgt_static.py; static terrain build only.",
        f"#SBATCH --job-name=terrain-bld-{safe_case[:19]}",
        _slurm_line("account", args.build_account),
        _slurm_line("partition", args.build_partition),
        _slurm_line("qos", args.build_qos),
        "#SBATCH --nodes=1",
        "#SBATCH --ntasks=1",
        f"#SBATCH --mem={args.build_mem}",
        f"#SBATCH --time={args.build_time}",
        _slurm_line("chdir", packet_dir),
        _slurm_line("output", log_root / f"terrain_build_{safe_case}_%j.out"),
        _slurm_line("error", log_root / f"terrain_build_{safe_case}_%j.err"),
    ]
    build_lines = [line for line in headers_build if line]
    build_lines.extend(
        [
            "",
            "set -euo pipefail",
            'PYTHON_BIN="${PYTHON_BIN:-python3}"',
            f"mkdir -p {shell_quote(static_output_dir)} {shell_quote(log_root)}",
            f"echo \"terrain build start $(date -u +%Y-%m-%dT%H:%M:%SZ) host=$(hostname)\"",
            '"${PYTHON_BIN}" '
            f"{shell_quote(helper)} build-from-inventory --inventory {shell_quote(inventory)} "
            f"--output-dir {shell_quote(static_output_dir)} --bounds {bounds} "
            f"--description {shell_quote(args.description)}",
            f"du -sh {shell_quote(static_output_dir)} | tee {shell_quote(packet_dir / 'terrain_static_du.txt')}",
            f"test -f {shell_quote(static_output_dir / 'index')}",
            f"echo \"terrain build stop $(date -u +%Y-%m-%dT%H:%M:%SZ)\"",
            "",
        ]
    )

    packet_dir.joinpath("terrain_download.slurm").write_text("\n".join(download_lines), encoding="utf-8")
    packet_dir.joinpath("terrain_build.slurm").write_text("\n".join(build_lines), encoding="utf-8")
    packet_dir.joinpath("submit_terrain_static.sh").write_text(
        "\n".join(
            [
                "#!/bin/bash",
                "set -euo pipefail",
                f"cd {shell_quote(packet_dir)}",
                'download_job=$(sbatch --parsable terrain_download.slurm)',
                'printf "download_job=%s\\n" "$download_job"',
                'build_job=$(sbatch --parsable --dependency=afterok:${download_job} terrain_build.slurm)',
                'printf "build_job=%s\\n" "$build_job"',
                "",
            ]
        ),
        encoding="utf-8",
    )
    packet_dir.joinpath("README.md").write_text(
        "\n".join(
            [
                f"# Terrain Static Packet: {args.case_name}",
                "",
                f"- run_id: `{run_id}`",
                f"- bounds: `{_format_bounds(tuple(args.bounds))}`",
                f"- DEM query bounds with WPS tile borders: `{_format_bounds(source_bounds)}`",
                f"- token: `{args.token}`",
                f"- WPS relative path: `{args.rel_path}/`",
                f"- DEM cache: `{download_dir}`",
                f"- static output: `{static_output_dir}`",
                f"- WPS `geog_data_path`: `{geog_data_path}`",
                "",
                "Submit from a login shell only after confirming the Slurm target:",
                "",
                "```bash",
                f"bash {packet_dir / 'submit_terrain_static.sh'}",
                "```",
                "",
                "The download job is intended for the DTN/transfer partition. The build job is",
                "separate and can use a normal compute partition. Neither job runs WPS/geogrid.",
                "",
                "Expected size warning: 1 arc-second regional DEM caches can be several GiB.",
                "The WPS 3s static output for the Pelican broad box is much smaller, roughly",
                "hundreds of MiB plus temporary GDAL build files.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    os.chmod(packet_dir / "submit_terrain_static.sh", 0o755)
    print(f"wrote terrain Slurm packet to {packet_dir}")


def cmd_render_slurm_packet(args: argparse.Namespace) -> int:
    render_slurm_packet(args)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    plan = sub.add_parser("plan", help="print the WPS tiles needed for a lon/lat box")
    plan.add_argument("--bounds", nargs=4, type=float, default=DEFAULT_PELICAN_BOUNDS)
    plan.add_argument("--dx-deg", type=float, default=DEFAULT_DX_DEG)
    plan.add_argument("--tile-size", type=int, default=DEFAULT_TILE_SIZE)
    plan.add_argument("--tile-border", type=int, default=DEFAULT_TILE_BORDER)
    plan.add_argument(
        "--filename-digits",
        type=int,
        default=None,
        help="override static-tile filename digit width (5 or 6); default derives it from the in-region tiles",
    )
    plan.set_defaults(func=cmd_plan)

    build = sub.add_parser("build", help="build WPS HGT_M tiles from existing DEM rasters")
    build.add_argument("--source-dem", nargs="+", type=Path, required=True)
    build.add_argument("--output-dir", type=Path, required=True)
    build.add_argument("--bounds", nargs=4, type=float, default=DEFAULT_PELICAN_BOUNDS)
    build.add_argument("--dx-deg", type=float, default=DEFAULT_DX_DEG)
    build.add_argument("--tile-size", type=int, default=DEFAULT_TILE_SIZE)
    build.add_argument("--tile-border", type=int, default=DEFAULT_TILE_BORDER)
    build.add_argument("--resampling", default="bilinear")
    build.add_argument("--description", default="Custom 3-arc-second topography height for BRC WRF")
    build.add_argument(
        "--filename-digits",
        type=int,
        default=None,
        help="override static-tile filename digit width (5 or 6); default derives it from the in-region tiles",
    )
    build.set_defaults(func=cmd_build)

    build_inv = sub.add_parser("build-from-inventory", help="build WPS HGT_M tiles from a download inventory")
    build_inv.add_argument("--inventory", type=Path, required=True)
    build_inv.add_argument("--output-dir", type=Path, required=True)
    build_inv.add_argument("--bounds", nargs=4, type=float, default=DEFAULT_PELICAN_BOUNDS)
    build_inv.add_argument("--dx-deg", type=float, default=DEFAULT_DX_DEG)
    build_inv.add_argument("--tile-size", type=int, default=DEFAULT_TILE_SIZE)
    build_inv.add_argument("--tile-border", type=int, default=DEFAULT_TILE_BORDER)
    build_inv.add_argument("--resampling", default="bilinear")
    build_inv.add_argument("--description", default="Custom 3-arc-second topography height for BRC WRF")
    build_inv.add_argument(
        "--filename-digits",
        type=int,
        default=None,
        help="override static-tile filename digit width (5 or 6); default derives it from the in-region tiles",
    )
    build_inv.set_defaults(func=cmd_build_from_inventory)

    patch = sub.add_parser("patch-geogrid-table", help="insert a custom HGT_M token into GEOGRID.TBL")
    patch.add_argument("--base", type=Path, required=True)
    patch.add_argument("--output", type=Path, required=True)
    patch.add_argument("--token", default=DEFAULT_TOKEN)
    patch.add_argument("--rel-path", default=DEFAULT_REL_PATH)
    patch.add_argument("--interp", default=DEFAULT_INTERP)
    patch.set_defaults(func=cmd_patch_geogrid)

    namelist = sub.add_parser("render-namelist", help="render namelist.wps with a custom terrain token")
    namelist.add_argument("--template", type=Path, required=True)
    namelist.add_argument("--output", type=Path, required=True)
    namelist.add_argument("--token", default=DEFAULT_TOKEN)
    namelist.add_argument("--geog-data-path", type=Path, required=True)
    namelist.set_defaults(func=cmd_render_namelist)

    query = sub.add_parser("query-usgs", help="write a USGS TNM download manifest for a lon/lat box")
    query.add_argument("--bounds", nargs=4, type=float, default=DEFAULT_PELICAN_BOUNDS)
    query.add_argument("--expand-for-wps", action="store_true")
    query.add_argument("--dx-deg", type=float, default=DEFAULT_DX_DEG)
    query.add_argument("--tile-size", type=int, default=DEFAULT_TILE_SIZE)
    query.add_argument("--tile-border", type=int, default=DEFAULT_TILE_BORDER)
    query.add_argument("--dataset", default=DEFAULT_USGS_DATASET)
    query.add_argument("--prod-format", default="GeoTIFF")
    query.add_argument("--endpoint", default=DEFAULT_TNM_ENDPOINT)
    query.add_argument("--max-products", type=int, default=500)
    query.add_argument("--timeout", type=int, default=60)
    query.add_argument("--output", type=Path, required=True)
    query.set_defaults(func=cmd_query_usgs)

    download = sub.add_parser("download-manifest", help="download/cache DEM files from a TSV manifest")
    download.add_argument("--manifest", type=Path, required=True)
    download.add_argument("--output-dir", type=Path, required=True)
    download.add_argument("--inventory", type=Path, required=True)
    download.add_argument("--timeout", type=int, default=120)
    download.add_argument("--retries", type=int, default=3)
    download.add_argument("--min-free-gb", type=float, default=5.0)
    download.add_argument("--skip-hash", action="store_true")
    download.add_argument("--strict-bytes", action="store_true")
    download.add_argument("--force", action="store_true")
    download.set_defaults(func=cmd_download_manifest)

    packet = sub.add_parser("render-slurm-packet", help="render DTN download and compute build Slurm scripts")
    packet.add_argument("--case-name", required=True)
    packet.add_argument("--run-id")
    packet.add_argument("--bounds", nargs=4, type=float, default=DEFAULT_PELICAN_BOUNDS)
    packet.add_argument("--packet-dir", type=Path, required=True)
    packet.add_argument("--source-manifest", type=Path)
    packet.add_argument("--usgs-dataset", default=DEFAULT_USGS_DATASET)
    packet.add_argument("--usgs-format", default="GeoTIFF")
    packet.add_argument("--max-products", type=int, default=500)
    packet.add_argument("--download-dir", type=Path)
    packet.add_argument("--geog-data-path", type=Path)
    packet.add_argument("--static-output-dir", type=Path)
    packet.add_argument("--token", default=DEFAULT_TOKEN)
    packet.add_argument("--rel-path", default=DEFAULT_REL_PATH)
    packet.add_argument("--description", default="Custom 3-arc-second topography height for BRC WRF")
    packet.add_argument("--download-account", default="dtn")
    packet.add_argument("--download-partition", default="notchpeak-dtn")
    packet.add_argument("--download-qos", default="notchpeak-dtn")
    packet.add_argument("--download-time", default="02:00:00")
    packet.add_argument("--download-mem", default="8G")
    packet.add_argument("--build-account", default="lawson-np")
    packet.add_argument("--build-partition", default="lawson-np")
    packet.add_argument("--build-qos", default="")
    packet.add_argument("--build-time", default="02:00:00")
    packet.add_argument("--build-mem", default="16G")
    packet.add_argument("--log-root", type=Path, default=DEFAULT_LOG_ROOT)
    packet.add_argument("--timeout", type=int, default=120)
    packet.add_argument("--retries", type=int, default=3)
    packet.add_argument("--min-free-gb", type=float, default=5.0)
    packet.set_defaults(func=cmd_render_slurm_packet)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
