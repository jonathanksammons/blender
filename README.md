# PortraitMesh Generator

Local-only **Blender 5.1** add-on that builds a recognizable, editable 3D human
head by deforming one standardized base mesh to match facial landmarks placed
over portrait references. Procedural and deterministic — **no neural training,
no cloud, no paid APIs, no automatic downloads.**

> Landmark-driven portrait-to-mesh reconstruction. **Not** facial recognition,
> biometric, forensic, medical, or identity-verification software.

## Quick start

```bash
# Build the installable ZIP
python build_addon.py            # -> dist/portrait_mesh_generator-0.1.0.zip

# Pure-Python unit tests (no Blender needed)
python -m unittest discover -s portrait_mesh_generator/tests -t .

# Blender integration tests (launches Blender 5.1)
"C:\Program Files\Blender Foundation\Blender 5.1\blender.exe" \
  --background --factory-startup \
  --python portrait_mesh_generator/tests/run_blender_tests.py
```

Then install the ZIP in Blender via *Preferences ▸ Add-ons ▸ Install from Disk*
and open the **PortraitMesh** tab in the 3D Viewport sidebar (`N`).

## Status

Phase 1 + the first vertical slice are complete and verified (28 unit tests, 6
Blender integration tests passing in Blender 5.1.1). Profile depth fitting,
automatic landmark detection, and camera texture projection are present as
clearly-labelled scaffolds for later phases.

## Documentation

All docs live in [`portrait_mesh_generator/docs/`](portrait_mesh_generator/docs/):

- [README](portrait_mesh_generator/docs/README.md) — overview
- [INSTALLATION](portrait_mesh_generator/docs/INSTALLATION.md)
- [USER_GUIDE](portrait_mesh_generator/docs/USER_GUIDE.md) — workflow + acceptance walkthrough
- [ARCHITECTURE](portrait_mesh_generator/docs/ARCHITECTURE.md)
- [CURRENT_STATE](portrait_mesh_generator/docs/CURRENT_STATE.md) — development progress
- [IMPLEMENTATION_PLAN](portrait_mesh_generator/docs/IMPLEMENTATION_PLAN.md)
- [LIMITATIONS](portrait_mesh_generator/docs/LIMITATIONS.md)
- [PRIVACY](portrait_mesh_generator/docs/PRIVACY.md)
- [TROUBLESHOOTING](portrait_mesh_generator/docs/TROUBLESHOOTING.md)

## License

GPL-3.0-or-later (consistent with Blender add-ons).
