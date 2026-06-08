# PortraitMesh Generator — Implementation Plan

Phased plan. Phase 1 and the first vertical slice are **complete** (see
`CURRENT_STATE.md`). Remaining phases are scoped below.

## Phase 1 — Foundation ✅ (done)
Package, registration, panels, properties, reference loading, base-head loading,
mesh validation, logging, docs skeleton.

## First vertical slice ✅ (done)
Manual-landmark → measurements → solver → deformed head → reset → FBX export →
landmark JSON save/reload. Verified by unit + Blender integration tests.

## Phase 2 — Manual landmarks ✅ (done)
Schema, empties, category controls, mirroring, JSON import/export, normalized
coords. (Folded into the slice.)

## Phase 3 — Measurements ✅ (mostly done)
Normalized measurements, ratios, clamps, UI reporting. **Remaining:** wire the
manual-override fields to panel inputs; expose facial fifths in UI.

## Phase 4 — Procedural fitting ✅ (core done)
Mesh anchors, deformation regions, broad shape keys, staged solver, front fit,
residual, reset. **Remaining for production quality:**
- Add real shape keys to the base mesh (currently region displacement only).
- Barycentric/vertex-index anchors stored in the asset for precise landmark
  alignment (current anchors are region-centroid based).
- Modal/chunked solver for heavier base meshes.

## Phase 5 — Profile fitting (next)
1. Left/right profile landmark editing (schema + empties already exist).
2. `profile_depth` → depth parameters; extend `deformation_regions.json` with
   Y-axis (depth) regions.
3. Reconcile L/R; expose inferred depths as editable, clearly-labelled sliders.
4. Side-view refinement; integrate into the solver objective
   (`profile_depth_error`).

## Phase 6 — Optional automatic detection
1. Out-of-process adapter script (`scripts/detect_landmarks.py`) run with the
   user's external Python; prints validated landmark JSON to stdout.
2. Subprocess invocation with timeout + stdout/stderr capture (scaffold exists
   in `dependency_manager`).
3. MediaPipe→schema landmark name mapping.
4. Optional in-process path behind the preference toggle.
Never installs packages or downloads models.

## Phase 7 — Texturing
Projection cameras, front projection, profile blending, seam feathering, baked
texture image, save to disk. `create_principled_material` already lays the UV
material foundation.

## Phase 8 — Export & polish
Eyeball/teeth/mouth-interior placeholder components; armature option; refined
Unity preset; expanded integration tests; CI wiring.

## Cross-cutting backlog
- Manual measurement overrides UI.
- Undo coverage review for all operators.
- Draw-handler-based landmark labels/guides (currently uses `show_name`).
- Replace procedural base with a sculpted `PMG_BaseHead` asset.
