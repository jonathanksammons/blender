# PortraitMesh Generator

A **local-only** Blender 5.1 add-on that generates a recognizable, editable 3D
human head by deforming a single standardized base mesh to match facial
landmarks placed over portrait reference images.

> This is a **landmark-driven portrait-to-mesh reconstruction tool**. It is
> **not** identity verification, facial recognition, biometric, forensic, or
> medical software. See `LIMITATIONS.md` and `PRIVACY.md`.

## What it does

- Loads a front portrait (and optional left/right profiles) as reference planes.
- Lets you place and drag **manually editable** facial landmarks.
- Computes normalized facial measurements.
- Fits a clean-topology base head to those measurements (procedural,
  deterministic — **no neural network training**).
- Keeps **consistent topology and UVs** across every generated face.
- Exports for Unity as FBX or glTF.

## What it does NOT do

- No cloud services, paid APIs, or remote inference. Everything runs locally.
- No automatic package installation or model downloads.
- It does not invent photographically exact hidden geometry (back of skull, ears
  from a single front photo are estimated and editable).
- It does not create hair geometry. Hair may appear in a projected texture only.
- It does not identify, match, or compare people.

## Requirements

- **Blender 5.1** (uses current APIs; no 3.x/4.x-only behaviour).
- Windows 11 supported and tested; the pure-Python core is OS-independent.
- Optional automatic landmark detection requires you to set up your own local
  Python with a detector (e.g. MediaPipe). Manual mode needs nothing extra.

## Install

See `INSTALLATION.md`. In short: build the ZIP with `python portrait_mesh_generator/build_addon.py`,
then in Blender use *Edit ▸ Preferences ▸ Add-ons ▸ Install from Disk* and pick
the ZIP, or drag-and-drop it.

## First run

1. Open the 3D Viewport sidebar (`N`) → **PortraitMesh** tab.
2. **Setup**: name your project, click **Load Base Head**.
3. **References**: **Load Front** and pick a neutral front portrait.
4. **Landmarks**: **Create Manual Landmarks**, then drag each point onto the
   matching facial feature in front orthographic view.
5. **Fit**: **Generate / Fit Full Head**.
6. **Refine**: nudge the sliders if needed.
7. **Export**: set an output directory and **Export Character**.

A full walkthrough (including a synthetic, no-portrait-needed test using
`assets/sample_landmarks_front.json`) is in `USER_GUIDE.md`.

## Manual vs automatic landmarks

Manual landmark editing is the primary, always-available workflow. Automatic
detection is **optional** and, in this version, is a clearly-labelled scaffold
(Phase 6) — the add-on remains fully usable without it.

## Front-only vs profiles

A single front image cannot reveal depth. Front-only fits use anatomical depth
defaults (editable, labelled as estimates). Adding true 90° profile images
improves depth (Phase 5).

## Privacy & licensing

All processing is local; no data leaves your machine (`PRIVACY.md`). Licensed
GPL-3.0-or-later (consistent with Blender add-ons).
