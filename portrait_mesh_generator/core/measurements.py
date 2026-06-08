"""Normalized facial measurements derived from 2-D landmark positions.

Pure Python, no ``bpy`` dependency, so this module is fully unit-testable.

All inputs are 2-D points in normalized image coordinates (x right, y down) as
defined by :mod:`landmark_schema`. Measurements are *normalized* against a
stable reference distance (interpupillary distance by default) so that camera
distance and image resolution do not bias the result. Raw values are also kept
for diagnostics.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Dict, Mapping, Optional, Tuple

Point = Tuple[float, float]

# Plausible normalized ranges (relative to interpupillary distance). Values
# outside these are clamped and the clamp is reported to the user.
MEASUREMENT_RANGES: Dict[str, Tuple[float, float]] = {
    "face_width": (1.4, 3.4),
    "face_height": (2.4, 4.6),
    "jaw_width": (1.2, 3.0),
    "chin_width": (0.5, 1.6),
    "cheekbone_width": (1.6, 3.4),
    "temple_width": (1.8, 3.6),
    "eye_spacing": (0.7, 1.5),
    "eye_width": (0.6, 1.3),
    "eye_height": (0.15, 0.6),
    "brow_height": (0.2, 0.9),
    "nose_width": (0.5, 1.4),
    "nose_length": (1.0, 2.4),
    "nose_bridge_width": (0.15, 0.6),
    "mouth_width": (0.9, 2.0),
    "upper_lip_height": (0.1, 0.6),
    "lower_lip_height": (0.1, 0.7),
    "philtrum_length": (0.1, 0.6),
    "chin_height": (0.3, 1.4),
    "ear_height": (0.8, 2.0),
    "ear_offset": (-0.5, 0.5),
    "neck_width": (1.2, 3.0),
    "forehead_height": (0.6, 2.0),
}


@dataclass
class Measurement:
    """A single computed measurement and its provenance."""

    name: str
    raw: float
    normalized: float
    sources: Tuple[str, ...]
    available: bool = True
    clamped: bool = False
    clamped_to: Optional[float] = None
    confidence: float = 1.0
    overridden: bool = False


def _dist(a: Point, b: Point) -> float:
    return math.hypot(a[0] - b[0], a[1] - b[1])


def _mid(a: Point, b: Point) -> Point:
    return ((a[0] + b[0]) * 0.5, (a[1] + b[1]) * 0.5)


def _has(points: Mapping[str, Point], *names: str) -> bool:
    return all(n in points and points[n] is not None for n in names)


def reference_scale(points: Mapping[str, Point]) -> Tuple[float, str]:
    """Return the normalization distance and its name.

    Prefers interpupillary distance, then eye-corner distance, then face height.
    Returns ``(0.0, "none")`` when nothing usable is present.
    """
    if _has(points, "pupil_l", "pupil_r"):
        d = _dist(points["pupil_l"], points["pupil_r"])
        if d > 1e-6:
            return d, "interpupillary"
    if _has(points, "eye_inner_l", "eye_inner_r"):
        d = _dist(points["eye_inner_l"], points["eye_inner_r"])
        if d > 1e-6:
            return d, "eye_corner"
    if _has(points, "skull_top", "chin"):
        d = _dist(points["skull_top"], points["chin"])
        if d > 1e-6:
            return d, "face_height"
    return 0.0, "none"


# Each entry: name -> (callable(points) -> (raw, sources) or None, confidence_keys)
def _vert(a: Point, b: Point) -> float:
    """Vertical (y-axis) extent, always positive."""
    return abs(a[1] - b[1])


def compute_measurements(
    points: Mapping[str, Point],
    overrides: Optional[Mapping[str, float]] = None,
) -> Dict[str, Measurement]:
    """Compute all measurements possible from ``points``.

    ``overrides`` maps measurement name -> normalized value supplied manually by
    the user; those replace the computed normalized value and are flagged.
    """
    overrides = overrides or {}
    scale, _scale_name = reference_scale(points)
    results: Dict[str, Measurement] = {}

    def add(name: str, raw: Optional[float], sources: Tuple[str, ...]) -> None:
        if raw is None or scale <= 1e-6:
            results[name] = Measurement(name, 0.0, 0.0, sources, available=False)
            return
        normalized = raw / scale
        clamped = False
        clamped_to = None
        lo, hi = MEASUREMENT_RANGES.get(name, (-math.inf, math.inf))
        if normalized < lo:
            clamped, clamped_to, normalized = True, normalized, lo
        elif normalized > hi:
            clamped, clamped_to, normalized = True, normalized, hi
        m = Measurement(name, raw, normalized, sources, True, clamped, clamped_to)
        if name in overrides:
            m.normalized = float(overrides[name])
            m.overridden = True
        results[name] = m

    P = points

    add(
        "face_width",
        _dist(P["cheekbone_l"], P["cheekbone_r"]) if _has(P, "cheekbone_l", "cheekbone_r") else None,
        ("cheekbone_l", "cheekbone_r"),
    )
    add(
        "face_height",
        _dist(P["skull_top"], P["chin"]) if _has(P, "skull_top", "chin") else None,
        ("skull_top", "chin"),
    )
    add(
        "jaw_width",
        _dist(P["jaw_corner_l"], P["jaw_corner_r"]) if _has(P, "jaw_corner_l", "jaw_corner_r") else None,
        ("jaw_corner_l", "jaw_corner_r"),
    )
    add(
        "chin_width",
        _dist(P["jaw_l"], P["jaw_r"]) if _has(P, "jaw_l", "jaw_r") else None,
        ("jaw_l", "jaw_r"),
    )
    add(
        "cheekbone_width",
        _dist(P["cheekbone_l"], P["cheekbone_r"]) if _has(P, "cheekbone_l", "cheekbone_r") else None,
        ("cheekbone_l", "cheekbone_r"),
    )
    add(
        "temple_width",
        _dist(P["temple_l"], P["temple_r"]) if _has(P, "temple_l", "temple_r") else None,
        ("temple_l", "temple_r"),
    )
    add(
        "eye_spacing",
        _dist(P["eye_inner_l"], P["eye_inner_r"]) if _has(P, "eye_inner_l", "eye_inner_r") else None,
        ("eye_inner_l", "eye_inner_r"),
    )

    # Eye width / height averaged over both sides when available.
    eye_widths = []
    for side in ("l", "r"):
        if _has(P, f"eye_inner_{side}", f"eye_outer_{side}"):
            eye_widths.append(_dist(P[f"eye_inner_{side}"], P[f"eye_outer_{side}"]))
    add("eye_width", sum(eye_widths) / len(eye_widths) if eye_widths else None,
        ("eye_inner_l", "eye_outer_l", "eye_inner_r", "eye_outer_r"))

    eye_heights = []
    for side in ("l", "r"):
        if _has(P, f"eyelid_upper_{side}", f"eyelid_lower_{side}"):
            eye_heights.append(_vert(P[f"eyelid_upper_{side}"], P[f"eyelid_lower_{side}"]))
    add("eye_height", sum(eye_heights) / len(eye_heights) if eye_heights else None,
        ("eyelid_upper_l", "eyelid_lower_l", "eyelid_upper_r", "eyelid_lower_r"))

    # Brow height: vertical distance from brow arch to pupil, averaged.
    brow_heights = []
    for side in ("l", "r"):
        if _has(P, f"brow_arch_{side}", f"pupil_{side}"):
            brow_heights.append(_vert(P[f"brow_arch_{side}"], P[f"pupil_{side}"]))
    add("brow_height", sum(brow_heights) / len(brow_heights) if brow_heights else None,
        ("brow_arch_l", "pupil_l", "brow_arch_r", "pupil_r"))

    add(
        "nose_width",
        _dist(P["nostril_l"], P["nostril_r"]) if _has(P, "nostril_l", "nostril_r") else None,
        ("nostril_l", "nostril_r"),
    )
    add(
        "nose_length",
        _dist(P["nose_bridge_top"], P["nose_base"]) if _has(P, "nose_bridge_top", "nose_base") else None,
        ("nose_bridge_top", "nose_base"),
    )
    add(
        "nose_bridge_width",
        # Approximated from inner eye corners scaled down; reported as estimate.
        0.35 * _dist(P["eye_inner_l"], P["eye_inner_r"]) if _has(P, "eye_inner_l", "eye_inner_r") else None,
        ("eye_inner_l", "eye_inner_r"),
    )
    add(
        "mouth_width",
        _dist(P["mouth_corner_l"], P["mouth_corner_r"]) if _has(P, "mouth_corner_l", "mouth_corner_r") else None,
        ("mouth_corner_l", "mouth_corner_r"),
    )
    add(
        "upper_lip_height",
        _vert(P["upper_lip"], P["philtrum"]) if _has(P, "upper_lip", "philtrum") else None,
        ("upper_lip", "philtrum"),
    )
    add(
        "lower_lip_height",
        _vert(P["lower_lip"], P["upper_lip"]) if _has(P, "lower_lip", "upper_lip") else None,
        ("lower_lip", "upper_lip"),
    )
    add(
        "philtrum_length",
        _vert(P["nose_base"], P["upper_lip"]) if _has(P, "nose_base", "upper_lip") else None,
        ("nose_base", "upper_lip"),
    )

    add(
        "chin_height",
        _vert(P["chin"], P["lower_lip"]) if _has(P, "chin", "lower_lip") else None,
        ("chin", "lower_lip"),
    )

    ear_heights = []
    for side in ("l", "r"):
        if _has(P, f"ear_top_{side}", f"ear_bottom_{side}"):
            ear_heights.append(_vert(P[f"ear_top_{side}"], P[f"ear_bottom_{side}"]))
    add("ear_height", sum(ear_heights) / len(ear_heights) if ear_heights else None,
        ("ear_top_l", "ear_bottom_l", "ear_top_r", "ear_bottom_r"))

    # Ear vertical offset relative to eye line (positive = lower than eyes).
    if _has(P, "ear_top_l", "ear_top_r", "pupil_l", "pupil_r"):
        ear_mid_y = _mid(P["ear_top_l"], P["ear_top_r"])[1]
        eye_mid_y = _mid(P["pupil_l"], P["pupil_r"])[1]
        add("ear_offset", ear_mid_y - eye_mid_y, ("ear_top_l", "ear_top_r", "pupil_l", "pupil_r"))
    else:
        add("ear_offset", None, ("ear_top_l", "ear_top_r"))

    add(
        "neck_width",
        _dist(P["neck_l"], P["neck_r"]) if _has(P, "neck_l", "neck_r") else None,
        ("neck_l", "neck_r"),
    )
    add(
        "forehead_height",
        _vert(P["skull_top"], P["brow_arch_l"]) if _has(P, "skull_top", "brow_arch_l") else None,
        ("skull_top", "brow_arch_l"),
    )
    return results


def facial_thirds(points: Mapping[str, Point]) -> Optional[Tuple[float, float, float]]:
    """Return the three vertical facial thirds as fractions summing to 1.0.

    Upper: brow line -> hairline (approx skull_top), Middle: brow -> nose base,
    Lower: nose base -> chin.
    """
    if not _has(points, "skull_top", "brow_arch_l", "nose_base", "chin"):
        return None
    brow_y = points["brow_arch_l"][1]
    upper = abs(brow_y - points["skull_top"][1])
    middle = abs(points["nose_base"][1] - brow_y)
    lower = abs(points["chin"][1] - points["nose_base"][1])
    total = upper + middle + lower
    if total <= 1e-6:
        return None
    return (upper / total, middle / total, lower / total)


def facial_fifths(points: Mapping[str, Point]) -> Optional[Tuple[float, ...]]:
    """Return horizontal facial fifths as fractions across the face width."""
    needed = ("ear_top_l", "eye_outer_l", "eye_inner_l", "eye_inner_r", "eye_outer_r", "ear_top_r")
    if not _has(points, *needed):
        return None
    xs = [points[n][0] for n in needed]
    xs.sort()
    spans = [xs[i + 1] - xs[i] for i in range(len(xs) - 1)]
    total = sum(spans)
    if total <= 1e-6:
        return None
    return tuple(s / total for s in spans)
