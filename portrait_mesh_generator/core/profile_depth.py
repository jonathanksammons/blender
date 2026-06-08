"""Profile-depth estimation (pure Python).

Phase 5 will drive head depth from real profile landmarks. For the first
vertical slice this module provides:

* anatomical default depth ratios (relative to face height) used when no profile
  image is available, and
* a clearly-labelled estimator that turns profile landmarks into normalized
  depth offsets when they *are* available.

Every returned value carries an ``estimated`` flag so the UI can label inferred
geometry honestly (never claim hidden geometry is photographically exact).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Mapping, Optional, Tuple

Point = Tuple[float, float]

# Default sagittal projections as a fraction of face height (chin->skull).
# These are population-average approximations, intentionally conservative.
ANATOMICAL_DEPTH_DEFAULTS: Dict[str, float] = {
    "forehead": 0.46,
    "brow": 0.50,
    "nose_bridge": 0.55,
    "nose_tip": 0.70,
    "nose_base": 0.58,
    "upper_lip": 0.54,
    "lower_lip": 0.52,
    "chin": 0.50,
    "jaw_angle": 0.10,
    "ear": 0.18,
    "rear_skull": -0.50,
}


@dataclass
class DepthValue:
    name: str
    value: float
    estimated: bool
    source: str  # "profile", "anatomical", "reconciled"


def anatomical_depths() -> Dict[str, DepthValue]:
    return {
        k: DepthValue(k, v, estimated=True, source="anatomical")
        for k, v in ANATOMICAL_DEPTH_DEFAULTS.items()
    }


# Map profile landmark names -> depth keys for estimation.
_PROFILE_TO_DEPTH = {
    "p_forehead": "forehead",
    "p_brow": "brow",
    "p_nose_bridge": "nose_bridge",
    "p_nose_tip": "nose_tip",
    "p_nose_base": "nose_base",
    "p_upper_lip": "upper_lip",
    "p_lower_lip": "lower_lip",
    "p_chin": "chin",
    "p_jaw_angle": "jaw_angle",
    "p_ear": "ear",
    "p_rear_skull": "rear_skull",
}


def depths_from_profile(points: Mapping[str, Point]) -> Dict[str, DepthValue]:
    """Estimate normalized depths from a single profile's landmarks.

    Depth is measured along the profile's horizontal axis relative to the ear
    landmark (a stable rotational pivot), normalized by the vertical face span.
    Missing landmarks fall back to anatomical defaults.
    """
    result = anatomical_depths()
    if "p_ear" not in points:
        return result

    pivot_x = points["p_ear"][0]
    # Vertical normalizer: forehead -> chin span.
    if "p_forehead" in points and "p_chin" in points:
        span = abs(points["p_chin"][1] - points["p_forehead"][1])
    else:
        span = 1.0
    if span <= 1e-6:
        span = 1.0

    for pname, dkey in _PROFILE_TO_DEPTH.items():
        if pname in points:
            depth = (points[pname][0] - pivot_x) / span
            result[dkey] = DepthValue(dkey, depth, estimated=False, source="profile")
    return result


def reconcile_profiles(
    left: Optional[Mapping[str, Point]],
    right: Optional[Mapping[str, Point]],
) -> Dict[str, DepthValue]:
    """Reconcile left/right profile depth estimates.

    * both present  -> average per key (source "reconciled")
    * one present   -> use it, mirror by symmetry (source "profile")
    * none present  -> anatomical defaults
    """
    if not left and not right:
        return anatomical_depths()
    if left and not right:
        return depths_from_profile(left)
    if right and not left:
        return depths_from_profile(right)

    ld = depths_from_profile(left)
    rd = depths_from_profile(right)
    out: Dict[str, DepthValue] = {}
    for key in set(ld) | set(rd):
        a, b = ld.get(key), rd.get(key)
        if a and b and not a.estimated and not b.estimated:
            out[key] = DepthValue(key, (a.value + b.value) * 0.5, False, "reconciled")
        else:
            chosen = a if (a and not a.estimated) else (b if (b and not b.estimated) else a or b)
            out[key] = chosen
    return out
