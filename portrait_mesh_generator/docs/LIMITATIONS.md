# Limitations

Read this before relying on results.

## Fundamental

- **A single image cannot reveal hidden geometry.** Depth, the back of the skull,
  and ear shape are *estimated* from anatomical ratios when no profile image is
  provided. These estimates are exposed as editable sliders and clearly labelled;
  they are not photographically exact.
- **This is not exact, forensic, biometric, medical, or identity-verification
  software.** It produces a plausible, recognizable, editable approximation —
  nothing more. Do not use it to identify or match people.

## Capture / input factors

- **Lighting and perspective affect fitting.** Shadows can hide landmarks; wide
  lenses up close distort proportions. Use flat lighting and stand back.
- **Expressions reduce accuracy.** A neutral, mouth-closed expression fits best.
- **Hair obscures skull shape.** Pull hair away from the face; otherwise the
  forehead/skull fit is guessed.
- **Head tilt / non-frontal pose** reduces accuracy. The tool does not assume a
  perfectly frontal image, but extreme angles need manual landmark correction.

## This version (0.1.0) specifically

- The **base head is a procedural anatomical approximation**, not a sculpted
  identity mesh. It has clean quad topology except two pole triangle-fans (skull
  top, neck base). A sculpted `assets/base_head.blend` (object `PMG_BaseHead`) is
  loaded automatically if you provide one.
- **Ears, eyelids, nostrils and lip interiors are not separately modelled** in
  the procedural base, so feature-level fitting is coarse.
- **Profile (depth) fitting is not applied yet** (Phase 5). Profiles can be
  loaded and landmarked, and depth is *previewed*, but the mesh is fit from the
  front view plus anatomical depth defaults.
- **Automatic landmark detection is a scaffold** (Phase 6). Manual landmarks are
  fully functional and are the intended primary workflow.
- **Texture projection from cameras is not implemented** (Phase 7). `Create
  Material` maps the front image onto the existing UVs only.
- **No eyeball/teeth/mouth-interior placeholders yet.**
- Manual refinement is expected and encouraged; automatic output is a starting
  point, not a finished asset.

## Topology guarantees that *do* hold

- Vertex count and UV layout are preserved across every fit (deformation moves
  coordinates only).
- The working mesh remains a single, continuous, manifold mesh.
- The neutral base source mesh is never destructively modified.
