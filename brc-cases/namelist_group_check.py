#!/usr/bin/env python
"""Check every namelist.input assignment sits in the group the BUILT binary expects.

A Fortran namelist read fails on the first name the group does not recognise, and it
reports the GROUP, never the variable:

    ------ ERROR while reading namelist physics ------
    Maybe here?:     gwd_opt                  = 0,    0,    0,

The "Maybe here?" line is where the parser stopped, which is not reliably the
offending entry, so the usual debugging loop is edit-resubmit-wait. This checks all
of them at once, before the job is queued, against inc/namelist_statements.inc --
the file WRF's build actually generates from the Registry, so it reflects THIS build
rather than the documentation.

Caught in practice: gwd_opt sitting in &physics on the ashley_drainage_120m case.
WRF's Registry declares it "namelist,dynamics"; every reference describes it as a
physics option, and it reads like one. real.exe aborted in 29 s at gate D.

    python -B namelist_group_check.py <namelist.input> [--wrf-root <path>]

Exit 0 if every assignment is in the right group, 1 otherwise. Stdlib only,
login-node safe: it reads two text files.

KNOWN AND EXPECTED: &namelist_quilt (nio_tasks_per_group, nio_groups, poll_servers)
is declared inline in frame/module_io_quilt_old.F rather than via the Registry, so
it never appears in namelist_statements.inc. It is whitelisted below; a bare "not in
the built binary" verdict for those two would be wrong.
"""
from __future__ import annotations

import argparse
import pathlib
import re
import sys

# Groups read outside the Registry's rconfig mechanism, so absent from
# namelist_statements.inc. Not a licence to ignore unknown names -- only these.
NON_REGISTRY_GROUPS = {
    "namelist_quilt": {"nio_tasks_per_group", "nio_groups", "poll_servers"},
}

IDENT = re.compile(r"[a-z][a-z0-9_]*")


def groups_from_build(statements: pathlib.Path) -> dict[str, str]:
    """Map variable -> namelist group, as the built binary declares them."""
    group_of: dict[str, str] = {}
    current: str | None = None
    for line in statements.read_text().splitlines():
        match = re.search(r"NAMELIST\s*/\s*([a-z_]+)\s*/", line)
        if match:
            current = match.group(1)
        if current is None:
            continue
        # after the group name, the rest of the line is the variable list
        tail = line.split("/")[-1]
        for name in IDENT.findall(tail):
            group_of.setdefault(name, current)
    return group_of


def check(namelist: pathlib.Path, statements: pathlib.Path) -> int:
    group_of = groups_from_build(statements)
    if not group_of:
        print(f"error: no NAMELIST groups found in {statements}", file=sys.stderr)
        return 2

    section: str | None = None
    problems: list[tuple[int, str, str, str]] = []
    checked = 0

    for lineno, raw in enumerate(namelist.read_text().splitlines(), 1):
        line = raw.strip()
        if line.startswith("&"):
            section = line[1:].split()[0].lower()
            continue
        if line.startswith("!") or line.startswith("/") or "=" not in line:
            continue
        var = line.split("=")[0].strip().lower()
        if not IDENT.fullmatch(var):
            continue
        checked += 1
        if var in NON_REGISTRY_GROUPS.get(section or "", set()):
            continue
        want = group_of.get(var)
        if want is None:
            problems.append((lineno, var, section or "?", "not in this build"))
        elif want != section:
            problems.append((lineno, var, section or "?", f"belongs in &{want}"))

    print(f"{namelist.name}: checked {checked} assignments against {statements}")
    if not problems:
        print("  OK -- every assignment is in the group this build expects")
        return 0
    print(f"  {len(problems)} PROBLEM(S):")
    for lineno, var, section, why in problems:
        print(f"    line {lineno:4d}  {var:26s} in &{section:<14s} -> {why}")
    return 1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("namelist", type=pathlib.Path)
    parser.add_argument("--wrf-root", type=pathlib.Path,
                        default=pathlib.Path(__file__).resolve().parent.parent,
                        help="WRF source root holding inc/namelist_statements.inc")
    args = parser.parse_args()

    if not args.namelist.is_file():
        return print(f"error: no namelist at {args.namelist}", file=sys.stderr) or 2
    statements = args.wrf_root / "inc" / "namelist_statements.inc"
    if not statements.is_file():
        print(f"error: no {statements} -- has WRF been configured/built?", file=sys.stderr)
        return 2
    return check(args.namelist, statements)


if __name__ == "__main__":
    sys.exit(main())
