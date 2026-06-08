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

# This script lives inside the package directory, so PKG_DIR is the package
# itself and REPO_ROOT is its parent. Archive entries are written relative to
# REPO_ROOT so the ZIP keeps the ``portrait_mesh_generator/`` prefix that
# Blender's "Install from Disk" expects.
PKG_DIR = Path(__file__).resolve().parent
PKG = PKG_DIR.name
REPO_ROOT = PKG_DIR.parent

EXCLUDE_DIRS = {"__pycache__", ".git", ".mypy_cache", ".pytest_cache", "dist"}
EXCLUDE_SUFFIXES = {".pyc", ".pyo"}
# Packaging/meta files that sit at the package root but should not ship inside
# the installable add-on ZIP.
EXCLUDE_ROOT_FILES = {"build_addon.py", "README.md"}


def _version() -> str:
    # Read version without importing bpy-dependent code.
    ns: dict = {}
    exec((PKG_DIR / "addon_info.py").read_text(encoding="utf-8"), ns)
    return ns["addon_version_string"]()


def build(output_dir: Path, include_tests: bool) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    zip_path = output_dir / f"{PKG}-{_version()}.zip"

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for path in sorted(PKG_DIR.rglob("*")):
            rel_parts = path.relative_to(REPO_ROOT).parts
            if any(part in EXCLUDE_DIRS for part in rel_parts):
                continue
            if not include_tests and "tests" in rel_parts:
                continue
            if path.suffix in EXCLUDE_SUFFIXES:
                continue
            if path.parent == PKG_DIR and path.name in EXCLUDE_ROOT_FILES:
                continue
            if path.is_file():
                zf.write(path, path.relative_to(REPO_ROOT).as_posix())
    return zip_path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default="dist", help="output directory")
    parser.add_argument("--no-tests", action="store_true", help="exclude tests/")
    args = parser.parse_args()
    zip_path = build(PKG_DIR / args.output, include_tests=not args.no_tests)
    print(f"Built {zip_path} ({zip_path.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
