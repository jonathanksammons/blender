"""Versioned facial landmark schema.

This module is deliberately free of any ``bpy`` import so that it can be used
by unit tests and the external detector adapter. Landmark default positions are
stored in *normalized image coordinates*:

    x in [0, 1]  -- 0 = image left edge, 1 = image right edge
    y in [0, 1]  -- 0 = image top edge,  1 = image bottom edge

The naming convention ``_l`` / ``_r`` refers to the *image* side as seen by the
viewer (``_l`` = viewer's left = smaller x). This is documented because it is a
common source of confusion when mirroring.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from ..addon_info import LANDMARK_SCHEMA_VERSION

# Categories used for UI grouping, visibility toggles and colour coding.
CATEGORIES = (
    "skull",
    "jaw",
    "eyes",
    "brows",
    "nose",
    "mouth",
    "ears",
    "neck",
    "profile",
)


@dataclass(frozen=True)
class LandmarkDef:
    """Static definition of a single landmark in the schema."""

    name: str
    label: str
    category: str
    default: Tuple[float, float]
    side: str = "C"  # "L", "R" or "C" (centre)
    symmetry_partner: Optional[str] = None
    view: str = "front"  # "front" or "profile"


def _pair(
    base: str,
    label: str,
    category: str,
    left_default: Tuple[float, float],
    right_default: Tuple[float, float],
) -> List[LandmarkDef]:
    """Helper that builds a mirrored left/right pair sharing symmetry partners."""
    left = f"{base}_l"
    right = f"{base}_r"
    return [
        LandmarkDef(left, f"{label} (L)", category, left_default, "L", right),
        LandmarkDef(right, f"{label} (R)", category, right_default, "R", left),
    ]


def _build_front_schema() -> List[LandmarkDef]:
    defs: List[LandmarkDef] = []

    # Skull / outline ------------------------------------------------------
    defs.append(LandmarkDef("skull_top", "Top of Skull", "skull", (0.50, 0.04)))
    defs += _pair("temple", "Temple", "skull", (0.28, 0.22), (0.72, 0.22))

    # Jaw ------------------------------------------------------------------
    defs.append(LandmarkDef("chin", "Chin", "jaw", (0.50, 0.82)))
    defs += _pair("jaw_corner", "Jaw Corner", "jaw", (0.30, 0.62), (0.70, 0.62))
    defs += _pair("jaw", "Jaw Contour", "jaw", (0.37, 0.74), (0.63, 0.74))
    defs += _pair("cheek", "Cheek Outer", "jaw", (0.27, 0.52), (0.73, 0.52))
    defs += _pair("cheekbone", "Cheekbone", "jaw", (0.30, 0.45), (0.70, 0.45))

    # Brows ----------------------------------------------------------------
    defs += _pair("brow_inner", "Brow Inner", "brows", (0.44, 0.34), (0.56, 0.34))
    defs += _pair("brow_arch", "Brow Arch", "brows", (0.38, 0.32), (0.62, 0.32))
    defs += _pair("brow_outer", "Brow Outer", "brows", (0.33, 0.34), (0.67, 0.34))

    # Eyes -----------------------------------------------------------------
    defs += _pair("eye_inner", "Eye Inner Corner", "eyes", (0.44, 0.40), (0.56, 0.40))
    defs += _pair("eye_outer", "Eye Outer Corner", "eyes", (0.36, 0.40), (0.64, 0.40))
    defs += _pair("eyelid_upper", "Upper Eyelid", "eyes", (0.40, 0.385), (0.60, 0.385))
    defs += _pair("eyelid_lower", "Lower Eyelid", "eyes", (0.40, 0.415), (0.60, 0.415))
    defs += _pair("pupil", "Pupil", "eyes", (0.40, 0.40), (0.60, 0.40))

    # Nose -----------------------------------------------------------------
    defs.append(LandmarkDef("nose_bridge_top", "Nose Bridge Top", "nose", (0.50, 0.40)))
    defs.append(LandmarkDef("nose_bridge_mid", "Nose Bridge Mid", "nose", (0.50, 0.48)))
    defs.append(LandmarkDef("nose_tip", "Nose Tip", "nose", (0.50, 0.56)))
    defs.append(LandmarkDef("nose_base", "Nose Base", "nose", (0.50, 0.59)))
    defs += _pair("nostril", "Nostril Outer", "nose", (0.45, 0.58), (0.55, 0.58))

    # Mouth ----------------------------------------------------------------
    defs.append(LandmarkDef("philtrum", "Philtrum", "mouth", (0.50, 0.63)))
    defs.append(LandmarkDef("upper_lip", "Upper Lip Centre", "mouth", (0.50, 0.66)))
    defs.append(LandmarkDef("lower_lip", "Lower Lip Centre", "mouth", (0.50, 0.70)))
    defs += _pair("upper_lip_peak", "Upper Lip Peak", "mouth", (0.47, 0.655), (0.53, 0.655))
    defs += _pair("mouth_corner", "Mouth Corner", "mouth", (0.43, 0.68), (0.57, 0.68))

    # Ears -----------------------------------------------------------------
    defs += _pair("ear_top", "Ear Top", "ears", (0.26, 0.42), (0.74, 0.42))
    defs += _pair("ear_bottom", "Ear Bottom", "ears", (0.27, 0.56), (0.73, 0.56))
    defs += _pair("ear_outer", "Ear Outer", "ears", (0.24, 0.49), (0.76, 0.49))

    # Neck -----------------------------------------------------------------
    defs += _pair("neck", "Neck Width", "neck", (0.40, 0.95), (0.60, 0.95))

    return defs


def _build_profile_schema() -> List[LandmarkDef]:
    # Profile landmarks use the same normalized convention but on a side image.
    # x increases toward the face front, y top-to-bottom.
    return [
        LandmarkDef("p_forehead", "Forehead Projection", "profile", (0.55, 0.18), view="profile"),
        LandmarkDef("p_brow", "Brow Projection", "profile", (0.58, 0.32), view="profile"),
        LandmarkDef("p_nose_bridge", "Nose Bridge", "profile", (0.60, 0.42), view="profile"),
        LandmarkDef("p_nose_tip", "Nose Tip", "profile", (0.70, 0.54), view="profile"),
        LandmarkDef("p_nose_base", "Nose Base", "profile", (0.62, 0.59), view="profile"),
        LandmarkDef("p_upper_lip", "Upper Lip Projection", "profile", (0.62, 0.66), view="profile"),
        LandmarkDef("p_lower_lip", "Lower Lip Projection", "profile", (0.61, 0.70), view="profile"),
        LandmarkDef("p_chin", "Chin Projection", "profile", (0.58, 0.82), view="profile"),
        LandmarkDef("p_jaw_angle", "Jaw Angle", "profile", (0.35, 0.66), view="profile"),
        LandmarkDef("p_ear", "Ear Position", "profile", (0.30, 0.45), view="profile"),
        LandmarkDef("p_rear_skull", "Rear Skull Extent", "profile", (0.12, 0.30), view="profile"),
        LandmarkDef("p_neck", "Neck Transition", "profile", (0.40, 0.92), view="profile"),
    ]


_FRONT_SCHEMA: List[LandmarkDef] = _build_front_schema()
_PROFILE_SCHEMA: List[LandmarkDef] = _build_profile_schema()
_BY_NAME: Dict[str, LandmarkDef] = {d.name: d for d in (_FRONT_SCHEMA + _PROFILE_SCHEMA)}


def front_landmarks() -> List[LandmarkDef]:
    return list(_FRONT_SCHEMA)


def profile_landmarks() -> List[LandmarkDef]:
    return list(_PROFILE_SCHEMA)


def all_landmarks() -> List[LandmarkDef]:
    return _FRONT_SCHEMA + _PROFILE_SCHEMA


def get(name: str) -> Optional[LandmarkDef]:
    return _BY_NAME.get(name)


def front_landmark_names() -> List[str]:
    return [d.name for d in _FRONT_SCHEMA]


def landmarks_in_category(category: str, view: str = "front") -> List[LandmarkDef]:
    source = _FRONT_SCHEMA if view == "front" else _PROFILE_SCHEMA
    return [d for d in source if d.category == category]


def schema_dict() -> dict:
    """Serialisable representation, also written to ``assets/landmark_schema.json``."""
    return {
        "schema_version": LANDMARK_SCHEMA_VERSION,
        "categories": list(CATEGORIES),
        "front": [_def_to_dict(d) for d in _FRONT_SCHEMA],
        "profile": [_def_to_dict(d) for d in _PROFILE_SCHEMA],
    }


def _def_to_dict(d: LandmarkDef) -> dict:
    return {
        "name": d.name,
        "label": d.label,
        "category": d.category,
        "default": list(d.default),
        "side": d.side,
        "symmetry_partner": d.symmetry_partner,
        "view": d.view,
    }


def symmetry_pairs(view: str = "front") -> List[Tuple[str, str]]:
    """Return unique (left, right) name pairs for mirroring."""
    source = _FRONT_SCHEMA if view == "front" else _PROFILE_SCHEMA
    seen = set()
    pairs: List[Tuple[str, str]] = []
    for d in source:
        if d.side == "L" and d.symmetry_partner and d.name not in seen:
            pairs.append((d.name, d.symmetry_partner))
            seen.add(d.name)
            seen.add(d.symmetry_partner)
    return pairs


class SchemaValidationError(ValueError):
    """Raised when an external/imported landmark set violates the schema."""


def validate_landmark_payload(payload: dict) -> List[str]:
    """Validate a parsed landmark JSON payload.

    Returns a list of human-readable warnings. Raises
    :class:`SchemaValidationError` for hard failures that make the payload
    unusable.
    """
    if not isinstance(payload, dict):
        raise SchemaValidationError("Landmark payload must be a JSON object.")

    version = payload.get("schema_version")
    warnings: List[str] = []
    if version is None:
        warnings.append("Payload has no schema_version; assuming current.")
    elif version != LANDMARK_SCHEMA_VERSION:
        warnings.append(
            f"Schema version mismatch: file={version} current={LANDMARK_SCHEMA_VERSION}."
        )

    views = payload.get("views")
    if not isinstance(views, dict) or not views:
        raise SchemaValidationError("Payload missing 'views' object.")

    known = set(_BY_NAME)
    for view_name, points in views.items():
        if not isinstance(points, dict):
            raise SchemaValidationError(f"View '{view_name}' must map names to points.")
        for lname, pdata in points.items():
            if lname not in known:
                warnings.append(f"Unknown landmark '{lname}' ignored.")
                continue
            coords = pdata.get("pos") if isinstance(pdata, dict) else pdata
            if (
                not isinstance(coords, (list, tuple))
                or len(coords) < 2
                or not all(isinstance(c, (int, float)) for c in coords[:2])
            ):
                raise SchemaValidationError(
                    f"Landmark '{lname}' has invalid coordinates: {coords!r}"
                )
    return warnings
