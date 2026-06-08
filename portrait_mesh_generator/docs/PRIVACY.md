# Privacy

PortraitMesh Generator is designed to run **entirely on your machine**.

## What the add-on does NOT do

- It does **not** upload your images, landmarks, or generated meshes anywhere.
- It does **not** call any remote API, cloud service, or hosted inference
  endpoint.
- It does **not** collect analytics or telemetry.
- It does **not** silently install Python packages.
- It does **not** silently download models or data.
- It does **not** identify people or compare faces against any database.
- It does **not** train any model on your images.

## Network access

The add-on makes **no network calls**. There is no code path that opens a socket,
performs an HTTP request, or contacts a server. You can run it fully offline.

## What is written to disk

- **Logs**: operational metadata only — operation names, counts, residuals,
  file *paths*, validation results. **No image pixel data is ever logged.** Logs
  live under Blender's per-user config directory:
  `…/Blender/<ver>/config/portrait_mesh_generator/logs/`.
- **Landmark JSON**: only when you explicitly export it, to the path you choose.
- **Exported meshes/textures**: only to the output directory you choose.

You can delete the log directory at any time.

## Optional external detector (Phase 6)

If you choose to configure an external Python with a landmark detector, the
add-on will run **that local executable** as a subprocess and read its stdout.
This is local computation on your machine. The add-on never installs or downloads
the detector for you — you set it up yourself.

## Your responsibility

Portraits may be personal data. You are responsible for having the right to use
any image you load, and for how you store and share generated assets.
