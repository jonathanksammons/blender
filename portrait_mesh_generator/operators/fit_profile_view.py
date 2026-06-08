"""Profile (depth) fitting operator.

Full profile-driven depth reconstruction is **Phase 5** and is *not implemented*
in this version (the first vertical slice is front-view only, by design). This
operator is a clearly-labelled placeholder: it computes and reports the depth
*estimates* that Phase 5 will consume, but does not yet deform along depth.
"""

from __future__ import annotations

import bpy
from bpy.types import Operator

from ..core import landmark_objects as LO, logging_utils, profile_depth
from ..properties import get_props

log = logging_utils.get_logger("fit_profile_view")


class PMG_OT_fit_profile_view(Operator):
    """Estimate depth from profile landmarks (Phase 5 preview; not yet applied)"""

    bl_idname = "pmg.fit_profile_view"
    bl_label = "Fit Profiles (Preview)"
    bl_options = {"REGISTER"}

    def execute(self, context):
        left = LO.read_points("left") or None
        right = LO.read_points("right") or None
        depths = profile_depth.reconcile_profiles(left, right)
        n_measured = sum(1 for d in depths.values() if not d.estimated)
        log.info("Profile depth preview: %d measured, %d estimated",
                 n_measured, len(depths) - n_measured)
        self.report(
            {"WARNING"},
            "Profile depth fitting is not applied in this version (Phase 5). "
            f"Preview: {n_measured} measured / {len(depths) - n_measured} estimated depths.",
        )
        return {"FINISHED"}


classes = (PMG_OT_fit_profile_view,)
