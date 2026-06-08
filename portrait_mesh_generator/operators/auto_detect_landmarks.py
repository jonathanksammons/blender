"""Automatic landmark detection (optional).

Automatic detection is **Phase 6** and is optional by design: manual landmark
editing always works without it. This version ships the *diagnostics* and the
safe operator scaffold but does not bundle a detector and never installs or
downloads anything.

When a detector is wired up it will run either:
  * in-process (if the user opts in and a compatible package imports), or
  * out-of-process via a user-configured external Python that prints landmark
    JSON to stdout (captured with a timeout so Blender never freezes).
"""

from __future__ import annotations

import bpy
from bpy.types import Operator

from ..core import dependency_manager, logging_utils
from ..preferences import get_preferences

log = logging_utils.get_logger("auto_detect")


class PMG_OT_run_diagnostics(Operator):
    """Inspect optional detector dependencies (no install, no network)"""

    bl_idname = "pmg.run_diagnostics"
    bl_label = "Run Detector Diagnostics"
    bl_options = {"REGISTER"}

    def execute(self, context):
        prefs = get_preferences(context)
        report = dependency_manager.build_report(prefs.external_python_path or None)
        for line in report.summary_lines():
            log.info("DIAG %s", line)
        msg = "Detector available" if report.detector_available else "Manual mode only (detector unavailable)"
        self.report({"INFO"}, msg + " — see System Console / log for details.")
        return {"FINISHED"}


class PMG_OT_auto_detect_landmarks(Operator):
    """Auto-detect landmarks if a detector is configured (else stays manual)"""

    bl_idname = "pmg.auto_detect_landmarks"
    bl_label = "Auto Detect Landmarks"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        prefs = get_preferences(context)
        report = dependency_manager.build_report(prefs.external_python_path or None)
        if not report.detector_available:
            self.report(
                {"WARNING"},
                "No local detector available. Use Create Manual Landmarks. "
                "Configure an external Python in add-on preferences to enable "
                "auto-detection (Phase 6).",
            )
            return {"CANCELLED"}
        # Detector present but the conversion adapter is a Phase 6 deliverable.
        self.report(
            {"WARNING"},
            "Detector detected, but the detection adapter is not implemented in "
            "this version (Phase 6). Manual landmarks remain fully functional.",
        )
        return {"CANCELLED"}


classes = (
    PMG_OT_run_diagnostics,
    PMG_OT_auto_detect_landmarks,
)
