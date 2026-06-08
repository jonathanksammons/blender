# Installation

## Build the ZIP

From the repository root:

```
python build_addon.py
```

This writes `dist/portrait_mesh_generator-0.1.0.zip` with the package at the
archive root (required by Blender's installer). Add `--no-tests` to omit the test
suite from the shipped ZIP.

## Install in Blender 5.1

### Option A — Install from Disk (legacy add-on path)
1. *Edit ▸ Preferences ▸ Add-ons*.
2. Top-right dropdown ▸ **Install from Disk…**.
3. Select `dist/portrait_mesh_generator-0.1.0.zip`.
4. Enable **PortraitMesh Generator** in the list.

### Option B — Drag and drop
Drag the ZIP into the Blender window and confirm the install dialog.

### Option C — Run from source (development)
Symlink or copy `portrait_mesh_generator/` into your Blender add-ons directory:

```
%APPDATA%\Blender Foundation\Blender\5.1\scripts\addons\portrait_mesh_generator
```

Then enable it in Preferences. On Windows, a developer copy is simplest:
`Copy-Item -Recurse portrait_mesh_generator "$env:APPDATA\Blender Foundation\Blender\5.1\scripts\addons\"`.

## Verify the install

- The 3D Viewport sidebar (`N`) shows a **PortraitMesh** tab.
- *Preferences ▸ Add-ons ▸ PortraitMesh Generator* shows the panel with the
  "local-only, no network" notice.
- No Python errors appear in the System Console (*Window ▸ Toggle System
  Console*).

## Optional: automatic landmark detection

Automatic detection is optional and never auto-installs anything. If you want it
(Phase 6), set up a **separate** Python environment with a detector and point the
add-on at it:

1. Create a Python (e.g. `python -m venv pmg-detect`) and `pip install mediapipe`
   yourself.
2. *Preferences ▸ Add-ons ▸ PortraitMesh Generator ▸ External Python* → set the
   path to that interpreter.
3. Use **Diagnostics ▸ Run Detector Diagnostics** to confirm it is detected.

Blender's bundled Python is **not** modified.

## Running the tests

Pure-Python (no Blender):
```
python -m unittest discover -s portrait_mesh_generator/tests -t .
```

Blender integration (launches Blender):
```
"C:\Program Files\Blender Foundation\Blender 5.1\blender.exe" --background --factory-startup --python portrait_mesh_generator/tests/run_blender_tests.py
```

## Uninstall

Disable the add-on in Preferences (this cleanly unregisters all classes, removes
the Scene property, and shuts down logging) and click **Remove**.
