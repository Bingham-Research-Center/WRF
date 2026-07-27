"""Tests for domain_calc: the checks exist to catch mistakes this repo has hit."""

from __future__ import annotations

import copy
import tomllib
from pathlib import Path

import pytest

import domain_calc

SPEC_PATH = Path(__file__).parent / "specs" / "ashley_drainage_120m.domain.toml"


@pytest.fixture
def spec() -> dict:
    return tomllib.loads(SPEC_PATH.read_text())


def test_tracked_spec_is_self_consistent(spec):
    result = domain_calc.build(spec)
    errors = [f for f in result.findings if f.level == "ERROR"]
    assert not errors, [f.text for f in errors]
    assert not result.failed


def test_ladder_matches_declared_ratios(spec):
    result = domain_calc.build(spec)
    for parent, child in zip(result.domains, result.domains[1:]):
        assert parent.dx / child.dx == pytest.approx(child.parent_grid_ratio)


def test_nest_dimensions_tile_the_parent(spec):
    """(e-1) must be divisible by the ratio or WRF cannot align the nest."""
    result = domain_calc.build(spec)
    for d in result.domains[1:]:
        assert (d.e_we - 1) % d.parent_grid_ratio == 0
        assert (d.e_sn - 1) % d.parent_grid_ratio == 0


def test_every_waypoint_is_inside_the_finest_domain(spec):
    """The sibling experiment placed its target canyon 1.3 km OUTSIDE the nest."""
    result = domain_calc.build(spec)
    outside = [f.text for f in result.findings if "OUTSIDE" in f.text]
    assert not outside, outside


def test_waypoint_outside_the_box_is_an_error(spec):
    """Browns Park is the case we deliberately excluded -- assert it would fail."""
    spec["target"]["waypoints"]["browns_park"] = [-108.95, 40.90]
    result = domain_calc.build(spec)
    assert result.failed
    assert any("browns_park" in f.text and "OUTSIDE" in f.text for f in result.findings)


def test_nest_touching_the_parent_rim_is_an_error(spec):
    """A nest inside the relaxation zone ingests boundary noise."""
    spec["coarse"]["e_we"] = 56  # barely wider than d02's 54-cell footprint
    result = domain_calc.build(spec)
    assert result.failed


def test_even_ratio_warns(spec):
    spec["grid"]["dx"] = [3000.0, 750.0, 150.0]
    spec["grid"]["parent_grid_ratio"] = [1, 4, 5]
    result = domain_calc.build(spec)
    assert any(f.level == "WARN" and "even" in f.text for f in result.findings)


def test_dx_ladder_inconsistent_with_ratios_is_an_error(spec):
    spec["grid"]["parent_grid_ratio"] = [1, 3, 5]  # dx says 5, ratio says 3
    result = domain_calc.build(spec)
    assert result.failed


def test_time_step_over_guideline_warns(spec):
    spec["grid"]["time_step"] = 60.0
    result = domain_calc.build(spec)
    assert any(f.level == "WARN" and "guideline" in f.text for f in result.findings)


def test_decoupled_time_ratios_are_honoured(spec):
    result = domain_calc.build(spec)
    # 10 s with ratios 1,4,4 -> 10 / 2.5 / 0.625, NOT 10 / 2 / 0.4 from the 5:1 grid
    assert [d.dt for d in result.domains] == pytest.approx([10.0, 2.5, 0.625])


def test_d02_keeps_its_own_centre(spec):
    """d02 spans the Basin; centring it on d03 would slide it east off Duchesne."""
    with_centre = domain_calc.build(spec)
    spec["d02"].pop("center")
    without = domain_calc.build(spec)
    assert with_centre.domains[1].i_parent_start != without.domains[1].i_parent_start


def test_cost_is_dominated_by_the_finest_domain(spec):
    result = domain_calc.build(spec)
    _, units = domain_calc.cost(result)
    total = sum(u for _, u in units)
    assert units[-1][1] / total > 0.8


def test_namelist_has_one_value_per_domain(spec):
    result = domain_calc.build(spec)
    text = domain_calc.namelist_geogrid(result, spec)
    n = len(result.domains)
    for key in ("parent_id", "parent_grid_ratio", "i_parent_start",
                "j_parent_start", "e_we", "e_sn", "geog_data_res"):
        line = next(ln for ln in text.splitlines() if ln.strip().startswith(key))
        assert line.rstrip().rstrip(",").count(",") == n - 1, line
    assert f"max_dom = {n}," in text


def test_nocolons_is_emitted_only_when_the_spec_asks(spec):
    """WPS and WRF must agree on filename style or real.exe cannot find met_em.

    nocolons lives in namelist.wps &share and namelist.input &time_control, and
    nothing reconciles them. With it set only on the WRF side, WPS writes
    met_em.d01.2026-04-24_23:00:00.nc while real.exe asks for ...23_00_00.nc and
    dies with "bad date in namelist or file not in directory". Cost a gate D
    submission on ashley_drainage_120m before it was caught.
    """
    # the tracked spec sets it, so derive the negative case by removing it
    spec_off = copy.deepcopy(spec)
    spec_off.get("share", {}).pop("nocolons", None)
    without = domain_calc.namelist_geogrid(domain_calc.build(spec_off), spec_off)
    assert "nocolons" not in without

    with_on = domain_calc.namelist_geogrid(domain_calc.build(spec), spec)
    assert " nocolons = .true.," in with_on
    # and it must sit inside &share, not leak into &geogrid
    share_block = with_on.split("&geogrid")[0]
    assert "nocolons" in share_block
