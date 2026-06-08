"""Landmark project (de)serialisation -- pure Python.

The on-disk format is JSON and is versioned. Coordinates are stored in
*normalized image coordinates* (see :mod:`landmark_schema`) so that a project is
independent of viewport state and image resolution.

Schema (v1)::

    {
      "schema_version": 1,
      "project_file_version": 1,
      "project_name": "...",
      "views": {
        "front": {"<landmark>": {"pos": [x, y], "enabled": true,
                                  "locked": false, "confidence": 1.0,
                                  "overridden": false}},
        "left":  {...},
        "right": {...}
      }
    }
"""

from __future__ import annotations

import json
from dataclasses import dataclass, asdict, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from ..addon_info import LANDMARK_SCHEMA_VERSION, PROJECT_FILE_VERSION
from . import landmark_schema

Point = Tuple[float, float]
VALID_VIEWS = ("front", "left", "right")


@dataclass
class LandmarkPoint:
    pos: Point
    enabled: bool = True
    locked: bool = False
    confidence: float = 1.0
    overridden: bool = False


@dataclass
class LandmarkProject:
    project_name: str = "PortraitMesh Project"
    views: Dict[str, Dict[str, LandmarkPoint]] = field(default_factory=dict)

    def points(self, view: str = "front") -> Dict[str, Point]:
        """Return enabled landmark positions for a view as a plain dict."""
        return {
            name: lp.pos
            for name, lp in self.views.get(view, {}).items()
            if lp.enabled
        }

    def set_point(self, view: str, name: str, pos: Point, **kwargs) -> None:
        self.views.setdefault(view, {})[name] = LandmarkPoint(pos=tuple(pos), **kwargs)


def project_from_defaults(name: str = "PortraitMesh Project") -> LandmarkProject:
    """Build a project pre-populated with schema default front landmarks."""
    proj = LandmarkProject(project_name=name)
    proj.views["front"] = {
        d.name: LandmarkPoint(pos=d.default) for d in landmark_schema.front_landmarks()
    }
    return proj


def to_payload(project: LandmarkProject) -> dict:
    return {
        "schema_version": LANDMARK_SCHEMA_VERSION,
        "project_file_version": PROJECT_FILE_VERSION,
        "project_name": project.project_name,
        "views": {
            view: {
                name: {
                    "pos": [float(lp.pos[0]), float(lp.pos[1])],
                    "enabled": bool(lp.enabled),
                    "locked": bool(lp.locked),
                    "confidence": float(lp.confidence),
                    "overridden": bool(lp.overridden),
                }
                for name, lp in points.items()
            }
            for view, points in project.views.items()
        },
    }


def from_payload(payload: dict) -> Tuple[LandmarkProject, List[str]]:
    """Validate and parse a payload. Returns (project, warnings)."""
    warnings = landmark_schema.validate_landmark_payload(payload)
    project = LandmarkProject(project_name=payload.get("project_name", "Imported Project"))
    known = {d.name for d in landmark_schema.all_landmarks()}
    for view, points in payload.get("views", {}).items():
        if view not in VALID_VIEWS:
            warnings.append(f"Unknown view '{view}' ignored.")
            continue
        parsed: Dict[str, LandmarkPoint] = {}
        for name, pdata in points.items():
            if name not in known:
                continue
            if isinstance(pdata, dict):
                coords = pdata.get("pos", [0.0, 0.0])
                parsed[name] = LandmarkPoint(
                    pos=(float(coords[0]), float(coords[1])),
                    enabled=bool(pdata.get("enabled", True)),
                    locked=bool(pdata.get("locked", False)),
                    confidence=float(pdata.get("confidence", 1.0)),
                    overridden=bool(pdata.get("overridden", False)),
                )
            else:  # bare [x, y]
                parsed[name] = LandmarkPoint(pos=(float(pdata[0]), float(pdata[1])))
        project.views[view] = parsed
    return project, warnings


def save(project: LandmarkProject, path: Path) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        json.dump(to_payload(project), fh, indent=2)


def load(path: Path) -> Tuple[LandmarkProject, List[str]]:
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(f"Landmark file not found: {path}")
    try:
        with path.open("r", encoding="utf-8") as fh:
            payload = json.load(fh)
    except json.JSONDecodeError as exc:
        raise landmark_schema.SchemaValidationError(f"Invalid JSON: {exc}") from exc
    return from_payload(payload)
