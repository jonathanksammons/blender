"""Optional-dependency diagnostics for landmark detection.

This module *only inspects* the environment. It never installs, downloads, or
imports heavy packages at module load time, and it never contacts the network.
Automatic detection is always optional; manual landmark editing works
regardless of what this reports.
"""

from __future__ import annotations

import importlib.util
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional


@dataclass
class DependencyStatus:
    name: str
    available: bool
    detail: str = ""


@dataclass
class DetectorReport:
    python_version: str
    dependencies: List[DependencyStatus] = field(default_factory=list)
    detector_available: bool = False
    external_python: Optional[str] = None
    external_python_ok: bool = False
    external_python_detail: str = ""

    @property
    def manual_mode_usable(self) -> bool:
        # Manual mode is *always* usable; this is stated explicitly for the UI.
        return True

    def summary_lines(self) -> List[str]:
        lines = [f"Bundled Python: {self.python_version}"]
        for dep in self.dependencies:
            mark = "available" if dep.available else "missing"
            lines.append(f"  {dep.name}: {mark}{(' - ' + dep.detail) if dep.detail else ''}")
        lines.append(f"Detector available: {self.detector_available}")
        if self.external_python:
            mark = "ok" if self.external_python_ok else "unavailable"
            lines.append(f"External Python: {mark} ({self.external_python_detail})")
        lines.append("Manual mode usable: yes (always)")
        return lines


def _module_present(name: str) -> bool:
    try:
        return importlib.util.find_spec(name) is not None
    except (ImportError, ValueError):
        return False


def check_external_python(executable: Optional[str]) -> tuple[bool, str]:
    """Check a user-configured external Python without importing anything heavy.

    Returns (ok, detail). Times out quickly so Blender never freezes.
    """
    if not executable:
        return False, "not configured"
    exe = shutil.which(executable) or executable
    if not Path(exe).exists() and shutil.which(executable) is None:
        return False, f"executable not found: {executable}"
    try:
        proc = subprocess.run(
            [exe, "-c", "import sys; print(sys.version.split()[0])"],
            capture_output=True,
            text=True,
            timeout=10,
        )
    except (subprocess.TimeoutExpired, OSError) as exc:
        return False, f"failed to launch: {exc}"
    if proc.returncode != 0:
        return False, f"returned {proc.returncode}: {proc.stderr.strip()[:120]}"
    return True, f"python {proc.stdout.strip()}"


def build_report(external_python: Optional[str] = None) -> DetectorReport:
    """Assemble a full diagnostics report."""
    py = ".".join(str(v) for v in sys.version_info[:3])
    deps = [
        DependencyStatus("numpy", _module_present("numpy")),
        DependencyStatus("mediapipe", _module_present("mediapipe")),
        DependencyStatus("cv2 (opencv)", _module_present("cv2")),
    ]
    # In-process detector counts as available only if mediapipe imports cleanly.
    detector = any(d.name == "mediapipe" and d.available for d in deps)

    ext_ok, ext_detail = (False, "not configured")
    if external_python:
        ext_ok, ext_detail = check_external_python(external_python)

    return DetectorReport(
        python_version=py,
        dependencies=deps,
        detector_available=detector or ext_ok,
        external_python=external_python,
        external_python_ok=ext_ok,
        external_python_detail=ext_detail,
    )
