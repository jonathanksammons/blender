# Troubleshooting

Open *Window ▸ Toggle System Console* (Windows) to see messages, and check the
log file shown in the **Diagnostics** panel.

| Symptom | Cause | Fix |
|---|---|---|
| No **PortraitMesh** tab | Add-on not enabled | Preferences ▸ Add-ons ▸ enable it; press `N` in the viewport |
| "Image file not found" | Path moved/typo | Re-load the reference; use an absolute path |
| "Unsupported image format" | Exotic format | Convert to PNG/JPG/TGA/BMP/TIF/EXR |
| "Load the *front* reference image first" | Creating landmarks with no reference | Load the reference for the active view first |
| "Missing required landmarks: …" | Required points absent/disabled | Create landmarks; ensure pupils, cheekbones, skull_top, chin exist |
| Fit warns "Clamped measurements/parameters" | Landmarks imply extreme proportions | Re-check landmark placement; clamping kept the mesh safe |
| Fit barely changes the head | Landmarks close to the neutral defaults | That is correct — a neutral face → near-identity fit |
| "Base mesh version mismatch" | Working mesh from an older version | Re-run **Load Base Head** |
| "Anchor mismatch / vertex count" | Base topology changed | Reload base head; a custom base must keep stable indices |
| Reset Fit doesn't fully restore | Manual vertex edits on `PMG_Head` | Reset deforms from the source; avoid editing `PMG_Head` verts directly — use Refine |
| Export: "Output directory not writable" | Permissions / missing dir | Choose a writable folder |
| Export: "FBX exporter not available" | FBX I/O add-on disabled | Enable the bundled FBX/glTF I/O add-on |
| Detector "unavailable" | No local detector configured | Expected. Use manual landmarks, or set an External Python (Phase 6) |
| External Python check fails/times out | Wrong path / slow start | Verify the path runs `python -c "print(1)"`; the check times out at 10 s so Blender never freezes |
| Reference image not visible | Behind the head / opacity 0 | Raise opacity, toggle visibility, or use Front Orthographic view |
| Landmarks not where expected over photo | Image aspect vs frame | Aspect is preserved; nudge landmarks manually — they store normalized coords |

## Clean reinstall

1. Disable and **Remove** the add-on in Preferences (unregisters cleanly).
2. Delete any leftover `portrait_mesh_generator` folder in the add-ons directory.
3. Rebuild with `python build_addon.py` and install the fresh ZIP.

## Reporting a problem

Include: Blender version (Diagnostics panel), add-on version, the exact operator
you ran, the System Console output, and the latest lines of the log file. Do
**not** include the portrait image itself.
