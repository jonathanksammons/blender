# User Guide

## Recommended capture

### Front image
- Neutral expression, mouth closed, eyes open.
- Head level, camera at face height, looking straight at the lens.
- Even, flat lighting; no harsh shadows.
- Minimal perspective distortion (stand back and zoom rather than using a wide
  lens up close).
- No beauty filters or heavy retouching.
- Hair pulled away from the face and forehead where possible.

### Profile images (optional, improve depth)
- True 90° side view, no head tilt.
- Same camera distance, expression and lighting as the front shot.
- Ears visible where possible.

## Workflow

The **PortraitMesh** sidebar tab follows the workflow top to bottom.

### 1. Setup
- Set **Project** name and **Working Scale** (1.0 = metres; the base head is
  ~0.23 m tall).
- **Symmetry** on by default. **Preserve Source Mesh** keeps an untouched base.
- **Load Base Head** creates `PMG_BaseHead_Source` (hidden) and the visible
  `PMG_Head`. **Validate Base Head** checks manifold/UV/version.

### 2. References
- **Load Front** (and optionally Left/Right). Aspect ratio is preserved.
- Toggle visibility and opacity per view. **Front Orthographic View** snaps the
  camera; **Reset Reference Alignment** reloads images at default transforms.

### 3. Landmarks
- Choose the **View** (front/left/right).
- **Create Manual Landmarks** drops the schema points onto the reference.
- In **Front Orthographic** view, select and drag each empty onto the matching
  feature. Empties are colour-coded by category.
- **Mirror L>R / R>L** copies one side to the other about the face midline.
- **Lock/Unlock** selected points to protect them; **Reset** selected/all.
- **Display**: point size, show names, per-category visibility.
- **Import/Export** versioned landmark JSON.

Tip: place the pupils first — they define the normalization scale used by every
measurement.

### 4. Measurements
Live, normalized values (by interpupillary distance). A ⚠ icon marks a value
that was clamped to a safe range; the fit will warn you too.

### 5. Fit
- **Generate / Fit Full Head** loads the base if needed and fits to front
  landmarks.
- **Fit Front View** re-fits without reloading.
- **Fit Profiles** previews depth estimates (not yet applied — Phase 5).
- **Reset Fit** restores the neutral base exactly.
- Solver: **Quality** (Preview/Final), iterations, regularization, symmetry.
- Result shows status, residual and a quality label.

### 6. Refine
Nine live sliders (head, face, jaw/chin, eyes, nose, mouth) let you hand-tune the
result. They are the source of truth for the head shape, so **Reset Section** and
**Reset Fit** behave predictably.

### 7. Texture
- **Create Material** builds a Principled BSDF using the front image on the
  existing UVs. Full multi-view projection is Phase 7.
- Hair must be created separately; it only appears in textures, never geometry.

### 8. Export
- Set **Output Dir**, pick **FBX** or **glTF**, keep **Unity Preset** on.
- Export runs on a duplicate with transforms applied; your working mesh is never
  altered, and helper objects (references, landmarks) are excluded.

### 9. Diagnostics
Versions, detector availability, per-view image presence, landmark count and
confidence, mesh validity, residual and the log file name.

## Verifying the vertical slice (acceptance walkthrough)

You can verify end-to-end **without a real portrait** using the synthetic sample:

1. Setup ▸ **Load Base Head**. Confirm `PMG_Head` appears (770 verts).
2. References ▸ **Load Front** — pick any image (even a placeholder); aspect is
   used only for the frame.
3. Landmarks ▸ **Import** ▸ `assets/sample_landmarks_front.json`. 49 landmarks
   appear over the reference.
4. Measurements panel populates with normalized values.
5. Fit ▸ **Generate / Fit Full Head** — the head visibly widens/lengthens. Status
   shows iterations and residual.
6. Object mode: select `PMG_Head`, confirm it is one continuous mesh; vertex
   count is still 770 and the UVMap is present.
7. Fit ▸ **Reset Fit** — head returns to the neutral base shape.
8. Landmarks ▸ **Export** — save JSON, then **Import** it again to confirm
   round-trip.
9. Export ▸ set a directory ▸ **Export Character** — confirm a valid `.fbx`.
10. Disable the add-on in Preferences — no errors; handlers/classes removed.
