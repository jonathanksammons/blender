# PortraitMesh Generator — Architecture

## Layering

The add-on is split into a **pure-Python core** (no `bpy`) and a **Blender
integration layer**. This keeps the numerics deterministic and unit-testable
outside Blender.

```
portrait_mesh_generator/
  __init__.py            register/unregister (defers bpy imports to register())
  addon_info.py          version + data-contract constants (pure)
  preferences.py         AddonPreferences (external Python path)
  properties.py          PropertyGroup (state only; logic lives in core/)

  core/                  ── pure Python (unit-tested) ──────────────
    landmark_schema.py     versioned landmark definitions + validation
    landmark_storage.py    JSON (de)serialisation of landmark projects
    measurements.py        normalized facial measurements + clamping
    fitting_solver.py      measurements -> bounded deformation parameters
    deformation_solver.py  deform_coords() numerics (+ bpy apply wrapper)
    symmetry.py            landmark mirroring / asymmetry report
    profile_depth.py       anatomical + profile depth estimation
    dependency_manager.py  detector diagnostics (no install, no network)
    logging_utils.py       structured file logging
    ui_theme.py            centralized colours / sizes
                         ── Blender-dependent (bpy/bmesh lazy) ──────
    base_head.py           procedural base head + asset loader
    image_alignment.py     reference empties + image<->world mapping
    landmark_objects.py    empties <-> data bridge
    mesh_validation.py     manifold / UV / version checks
    texture_projection.py  Principled material (projection = Phase 7 stub)

  operators/             one Operator group per workflow step
  panels/                sidebar UI (root PMG_PT_main + child panels)
  assets/                landmark_schema.json, deformation_regions.json,
                         default_fitting_profile.json, sample landmarks
  tests/                 pure-Python unittests + Blender integration tests
  docs/
```

## Data flow (front-view vertical slice)

```
reference image ──> image_alignment (W,H frame, world<->normalized)
                         │
landmark empties ◄───────┘   (landmark_objects bridge)
   │ world positions
   ▼
landmark_objects.read_points("front")  ──> normalized image coords
   ▼
measurements.compute_measurements()    ──> normalized + clamped Measurements
   ▼
fitting_solver.solve()                 ──> bounded params {region: factor}
   ▼  (written into Refine sliders = single source of truth for shape)
deformation_solver.apply_params()      ──> deform working mesh from source rest
   ▼
PMG_Head (working)   PMG_BaseHead_Source (hidden, never mutated)
```

## Key design decisions

- **One reusable base mesh.** Topology never changes per face. The working head
  (`PMG_Head`) is deformed from a hidden, immutable source (`PMG_BaseHead_Source`).
  Deformation moves vertex *coordinates only* (`foreach_get`/`foreach_set`), so
  vertex count and UV loops are preserved exactly.
- **Refine sliders are the source of truth.** `Fit` writes solver output into the
  nine `refine_*` properties; their update callback live-applies the deformation.
  `Reset Fit` sets them to 1.0. This makes manual refinement and reset coherent.
- **Data-driven deformation regions.** `assets/deformation_regions.json` maps
  each parameter to a bbox-relative region (centre, radius, axis, falloff,
  front-mask). The base mesh can be swapped without code changes because regions
  reference the *live* bounding box.
- **Honest stubs.** Features not yet implemented (profile fitting, auto-detect
  adapter, camera texture projection) are explicit operators that report their
  status; they never fake success.
- **Versioned contracts.** `LANDMARK_SCHEMA_VERSION`, `BASE_MESH_VERSION`,
  `PROJECT_FILE_VERSION` gate imports and anchor compatibility.

## Coordinate conventions

- World: +Z up, face front toward **-Y** (reads correctly in Front view).
- Normalized image coords: x in [0,1] left→right, y in [0,1] top→bottom.
- `_l` / `_r` suffixes refer to the **image** side (viewer's left/right), i.e.
  `_l` has the smaller x.
