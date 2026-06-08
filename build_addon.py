#!/usr/bin/env python3
"""Build an installable ZIP for the PortraitMesh Generator add-on.

Usage:
    python build_addon.py [--output dist]

Produces ``dist/portrait_mesh_generator-<version>.zip`` containing the
``portrait_mesh_generator/`` package at the archive root (so Blender's
"Install from Disk" recognises it). ``__pycache__`` and test caches are
excluded; the unit tests themselves are kept for transparency but can be
excluded with ``--no-tests``.
"""

from __future__ import annotations

import argparse
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PKG = "portrait_mesh_generator"

EXCLUDE_DIRS = {"__pycache__", ".git", ".mypy_cache", ".pytest_cache"}
EXCLUDE_SUFFIXES = {".pyc", ".pyo"}


def _version() -> str:
    # Read version without importing bpy-dependent code.
    ns: dict = {}
    exec((ROOT / PKG / "addon_info.py").read_text(encoding="utf-8"), ns)
    return ns["addon_version_string"]()


def build(output_dir: Path, include_tests: bool) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    zip_path = output_dir / f"{PKG}-{_version()}.zip"

    pkg_root = ROOT / PKG
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for path in sorted(pkg_root.rglob("*")):
            rel_parts = path.relative_to(ROOT).parts
            if any(part in EXCLUDE_DIRS for part in rel_parts):
                continue
            if not include_tests and "tests" in rel_parts:
                continue
            if path.suffix in EXCLUDE_SUFFIXES:
                continue
            if path.is_file():
                zf.write(path, path.relative_to(ROOT).as_posix())
    return zip_path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default="dist", help="output directory")
    parser.add_argument("--no-tests", action="store_true", help="exclude tests/")
    args = parser.parse_args()
    zip_path = build(ROOT / args.output, include_tests=not args.no_tests)
    print(f"Built {zip_path} ({zip_path.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
