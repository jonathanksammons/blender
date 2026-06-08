"""Landmark mirroring helpers (pure Python).

Mirroring is performed about a vertical axis located at the mean x of the
interpupillary / face-centre landmarks, expressed in normalized image
coordinates.
"""

from __future__ import annotations

from typing import Dict, Mapping, Optional, Tuple

from . import landmark_schema

Point = Tuple[float, float]


def estimate_midline_x(points: Mapping[str, Point]) -> float:
    """Estimate the face vertical midline x from the most reliable centre cues."""
    centre_names = ("pupil_l", "pupil_r", "eye_inner_l", "eye_inner_r")
    xs = [points[n][0] for n in centre_names if n in points]
    if xs:
        return sum(xs) / len(xs)
    # Fall back to explicit centre landmarks.
    for n in ("nose_tip", "nose_base", "chin", "skull_top"):
        if n in points:
            return points[n][0]
    return 0.5


def mirror_point(p: Point, midline_x: float) -> Point:
    return (2.0 * midline_x - p[0], p[1])


def mirror_landmarks(
    points: Mapping[str, Point],
    source_side: str = "L",
    midline_x: Optional[float] = None,
) -> Dict[str, Point]:
    """Return a new dict where ``source_side`` landmarks are mirrored onto their
    partners. ``source_side`` is "L" or "R".
    """
    if source_side not in ("L", "R"):
        raise ValueError("source_side must be 'L' or 'R'")
    if midline_x is None:
        midline_x = estimate_midline_x(points)

    result: Dict[str, Point] = dict(points)
    for left, right in landmark_schema.symmetry_pairs():
        src, dst = (left, right) if source_side == "L" else (right, left)
        if src in points:
            result[dst] = mirror_point(points[src], midline_x)
    return result


def asymmetry_report(points: Mapping[str, Point]) -> Dict[str, float]:
    """Return per-pair horizontal asymmetry (deviation from perfect mirror).

    Useful for the diagnostics panel and for the controlled-asymmetry layer.
    """
    midline = estimate_midline_x(points)
    report: Dict[str, float] = {}
    for left, right in landmark_schema.symmetry_pairs():
        if left in points and right in points:
            expected_right = mirror_point(points[left], midline)
            dx = points[right][0] - expected_right[0]
            dy = points[right][1] - points[left][1]
            report[f"{left}|{right}"] = (dx * dx + dy * dy) ** 0.5
    return report
