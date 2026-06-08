# PortraitMesh Generator — Current State

_Last updated: 2026-06-06. Add-on version 0.1.0._

This document is the development progress record. It reflects what is actually
implemented and verified, not aspirations.

## Verification status

- **Pure-Python unit tests:** 28 tests, all passing
  (`python -m unittest discover -s portrait_mesh_generator/tests -t .`).
- **Blender integration tests:** 6 tests, all passing in **Blender 5.1.1**
  (`blender --background --factory-startup --python
  portrait_mesh_generator/tests/run_blender_tests.py`). Blender was actually
  launched for this result.
- **Syntax:** all modules byte-compile (`python -m py_compile`).
- **ZIP build:** `python portrait_mesh_generator/build_addon.py` produces
  `portrait_mesh_generator/dist/portrait_mesh_generator-0.1.0.zip`.

## Implemented and working (Phase 1 + first vertical slice)

| Capability | Status | Notes |
|---|---|---|
| Add-on registration / unregistration | done | verified in Blender 5.1.1 |
| Sidebar panels under "PortraitMesh" | done | root + 8 child sections |
| Scene PropertyGroup | done | state separate from logic |
| Add-on preferences (external Python) | done | no install/network |
| Load front/left/right reference images | done | image empties, aspect preserved |
| Front orthographic snap on front load | done | |
| Opacity / visibility / reset alignment | done | |
| Versioned landmark schema (49 front, 12 profile) | done | JSON in assets/ |
| Manual landmark empties (draggable) | done | per-category colour + visibility |
| Mirror L↔R, lock/unlock, reset selected/all | done | |
| Landmark JSON import/export (versioned) | done | round-trip tested |
| Normalized measurements + clamping report | done | IPD-normalized |
| Procedural base head (770 verts, manifold, UVs) | done | deterministic fallback |
| Base head validation (manifold/UV/version) | done | bmesh checks |
| Front-view fitting solver (coordinate descent) | done | residual/convergence reported |
| Layered deformation (9 regions, data-driven) | done | vertex count + UVs preserved |
| Live Refine sliders | done | single source of truth for shape |
| Reset Fit restores neutral base | done | verified exact restore |
| Basic Principled material (front image on UVs) | done | |
| Unity FBX / glTF export on a duplicate | done | source never mutated |
| Diagnostics panel | done | versions, detector, mesh validity |
| Structured logging to user dir | done | no image data logged |

## Implemented as honest, labelled stubs (not yet functional)

- **Automatic landmark detection** (`pmg.auto_detect_landmarks`) — reports
  detector availability via `dependency_manager`; the MediaPipe / external-Python
  conversion adapter is **Phase 6**. Manual mode always works.
- **Profile depth fitting** (`pmg.fit_profile_view`) — computes and reports depth
  estimates (anatomical + profile), but does **not** yet deform along depth
  (**Phase 5**).
- **Camera texture projection** (`pmg.project_texture`) — raises a clear
  not-implemented message (**Phase 7**). `Create Material` is real.

## Known limitations / gaps (this version)

- The base head is a procedural anatomical **approximation**, not an
  artist-sculpted identity mesh. There are pole triangle-fans at the skull top
  and neck base (all other faces are quads). A sculpted `assets/base_head.blend`
  named `PMG_BaseHead` will be loaded automatically if present.
- Ears, eyelid/nostril/lip interior detail are not separately modelled in the
  procedural base, so feature-level fitting is coarse.
- No optional eyeball/teeth placeholder objects yet (spec section pending).
- Measurement manual-override UI is present in the data model but not wired to
  panel inputs yet (overrides are honoured by `compute_measurements`).
- `fit_front_view` is synchronous; it is fast for the 770-vert base, so no modal
  chunking is needed yet. A modal solver is planned for heavier base meshes.

## Files changed in this stage

Entire `portrait_mesh_generator/` package created from scratch, plus
`portrait_mesh_generator/build_addon.py` and
`portrait_mesh_generator/dist/portrait_mesh_generator-0.1.0.zip`. See
`git`-less file listing in the repository root.

## Manual Blender test steps

See `docs/USER_GUIDE.md` → "Verifying the vertical slice" for an exact,
click-by-click acceptance walkthrough.
