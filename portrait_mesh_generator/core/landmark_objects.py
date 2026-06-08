"""Bridge between editable Blender landmark empties and pure-Python data.

Landmarks are represented in the viewport as small ``PLAIN_AXES`` empties so the
user can select and drag them with native Blender tools (undo-safe, no custom
modal needed for basic editing). Each empty stores its schema name, category and
lock/enable flags as custom properties. This module converts between those
empties and :class:`landmark_storage.LandmarkProject` / measurement dicts.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Tuple

from . import image_alignment, landmark_schema, ui_theme
from .landmark_storage import LandmarkPoint, LandmarkProject

LANDMARK_COLLECTION = "PortraitMesh_Landmarks"
CONTROLLER_NAME = "PMG_Landmarks"

PROP_IS_LANDMARK = "pmg_is_landmark"
PROP_LM_NAME = "pmg_landmark_name"
PROP_LM_CATEGORY = "pmg_landmark_category"
PROP_LM_VIEW = "pmg_landmark_view"
PROP_LM_ENABLED = "pmg_landmark_enabled"
PROP_LM_LOCKED = "pmg_landmark_locked"
PROP_LM_CONFIDENCE = "pmg_landmark_confidence"


def get_or_create_collection(context):
    import bpy  # type: ignore

    coll = bpy.data.collections.get(LANDMARK_COLLECTION)
    if coll is None:
        coll = bpy.data.collections.new(LANDMARK_COLLECTION)
        context.scene.collection.children.link(coll)
    return coll


def get_controller(create: bool = False, context=None):
    import bpy  # type: ignore

    ctrl = bpy.data.objects.get(CONTROLLER_NAME)
    if ctrl is None and create:
        ctrl = bpy.data.objects.new(CONTROLLER_NAME, None)
        ctrl.empty_display_type = "ARROWS"
        ctrl.empty_display_size = 0.03
        coll = get_or_create_collection(context)
        coll.objects.link(ctrl)
    return ctrl


def _empty_name(view: str, lname: str) -> str:
    return f"PMG_LM_{view}_{lname}"


def create_landmarks_from_project(context, project: LandmarkProject, view: str = "front",
                                  size: float = ui_theme.DEFAULT_LANDMARK_SIZE) -> int:
    """Create empties for every landmark in ``project.views[view]``.

    Returns the number of landmarks created. Existing landmark empties for the
    view are removed first so this is idempotent.
    """
    import bpy  # type: ignore

    ref = image_alignment.find_reference_empty(view)
    if ref is None:
        raise RuntimeError(f"No reference image for view '{view}'. Load it first.")

    clear_landmarks(view)
    coll = get_or_create_collection(context)
    ctrl = get_controller(create=True, context=context)

    points = project.views.get(view, {})
    created = 0
    for lname, lp in points.items():
        ldef = landmark_schema.get(lname)
        category = ldef.category if ldef else "skull"
        wx, wy, wz = image_alignment.normalized_to_world(ref, lp.pos[0], lp.pos[1])

        empty = bpy.data.objects.new(_empty_name(view, lname), None)
        empty.empty_display_type = "PLAIN_AXES"
        empty.empty_display_size = size
        empty.location = (wx, wy, wz)
        empty.show_name = False
        empty.color = ui_theme.category_color(category)
        empty[PROP_IS_LANDMARK] = True
        empty[PROP_LM_NAME] = lname
        empty[PROP_LM_CATEGORY] = category
        empty[PROP_LM_VIEW] = view
        empty[PROP_LM_ENABLED] = bool(lp.enabled)
        empty[PROP_LM_LOCKED] = bool(lp.locked)
        empty[PROP_LM_CONFIDENCE] = float(lp.confidence)
        coll.objects.link(empty)
        empty.parent = ctrl
        created += 1
    return created


def iter_landmark_empties(view: Optional[str] = None):
    import bpy  # type: ignore

    for obj in bpy.data.objects:
        if not obj.get(PROP_IS_LANDMARK):
            continue
        if view is not None and obj.get(PROP_LM_VIEW) != view:
            continue
        yield obj


def clear_landmarks(view: Optional[str] = None) -> int:
    import bpy  # type: ignore

    removed = 0
    for obj in list(iter_landmark_empties(view)):
        bpy.data.objects.remove(obj, do_unlink=True)
        removed += 1
    return removed


def read_points(view: str = "front") -> Dict[str, Tuple[float, float]]:
    """Return enabled landmark positions as normalized image coords."""
    ref = image_alignment.find_reference_empty(view)
    if ref is None:
        return {}
    points: Dict[str, Tuple[float, float]] = {}
    for obj in iter_landmark_empties(view):
        if not obj.get(PROP_LM_ENABLED, True):
            continue
        lname = obj.get(PROP_LM_NAME)
        nx, ny = image_alignment.world_to_normalized(ref, obj.location)
        points[lname] = (nx, ny)
    return points


def read_project(view: str = "front", project_name: str = "PortraitMesh Project") -> LandmarkProject:
    """Build a LandmarkProject snapshot from the current empties."""
    ref = image_alignment.find_reference_empty(view)
    proj = LandmarkProject(project_name=project_name)
    if ref is None:
        return proj
    bucket: Dict[str, LandmarkPoint] = {}
    for obj in iter_landmark_empties(view):
        lname = obj.get(PROP_LM_NAME)
        nx, ny = image_alignment.world_to_normalized(ref, obj.location)
        bucket[lname] = LandmarkPoint(
            pos=(nx, ny),
            enabled=bool(obj.get(PROP_LM_ENABLED, True)),
            locked=bool(obj.get(PROP_LM_LOCKED, False)),
            confidence=float(obj.get(PROP_LM_CONFIDENCE, 1.0)),
        )
    proj.views[view] = bucket
    return proj


def count_landmarks(view: Optional[str] = None) -> int:
    return sum(1 for _ in iter_landmark_empties(view))


def average_confidence(view: Optional[str] = None) -> float:
    confs = [float(o.get(PROP_LM_CONFIDENCE, 1.0)) for o in iter_landmark_empties(view)]
    return sum(confs) / len(confs) if confs else 0.0
