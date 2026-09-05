# Desktop screenshots

Use `scripts/webmind_screenshot.py` to inspect the visible desktop. For the contents of a browser tab, prefer Core `read-page`; for a browser viewport, Core `screenshot` does not require desktop packages.

Install the optional desktop dependencies from the repository root:

```bash
python -m pip install -r requirements-desktop.txt
python scripts/webmind_screenshot.py self-check --json
```

`self-check` imports packages and checks whether the native macOS command exists. It takes no screenshot and does not prove screen-recording permission or access to the current desktop. A graphical session and the operating system's screen-recording permission may be required.

## Commands

Every capture command reads the current desktop bounds before choosing its region. Do not reuse dimensions after moving a window or changing displays.

```bash
python scripts/webmind_screenshot.py resolution --json
python scripts/webmind_screenshot.py full --output screen.png --json
python scripts/webmind_screenshot.py half --side left --output left.png --json
python scripts/webmind_screenshot.py half --side right --output right.png --json
python scripts/webmind_screenshot.py region --x1 100 --y1 100 --x2 900 --y2 700 --output region.png --json
```

The region example is illustrative; obtain coordinates from the current capture metadata. `x2` and `y2` are the exclusive right and bottom edges. The region must have positive size and fit inside the reported bounds. `--output` also accepts `-o`; omitted paths become timestamped PNGs in the working directory. Invalid regions do not create output directories or execute the requested capture; reading the bounds may itself need a temporary fallback image.

## Coordinates and output

JSON contains `ok`, `task`, `resolution`, `desktop`, `backend`, `monitors`, `coordinate_space`, `capture_scope`, and `mouse_mapping_verified`. Captures also include `output` (absolute PNG path), `region`, `capture_backend`, and `image.width` / `image.height` (actual PNG dimensions).

- MSS reports a virtual desktop, including monitor origins that may be negative.
- Pillow fallback regions use coordinates within its captured image. The native macOS fallback explicitly captures the primary display and crops that image.
- Once a backend supplies the bounds, capture uses that same backend. A failure does not silently reuse the coordinates with another backend.
- `resolution` may take a temporary image when a fallback needs one to determine dimensions. It does not return a saved screenshot.

**Screenshot pixels are not automatically mouse coordinates.** The Mouse module uses PyAutoGUI's primary-screen coordinate system. Retina / DPI scaling, negative monitor origins, image crops, and multiple displays can change the mapping. Compare the screenshot's `region` and actual `image` size with Mouse `position`, confirm the target visually, and verify the mapping before sending input. Screenshots may omit the cursor; use the reported live pointer position as well as the image.

With `--json`, results and runtime errors are written to stdout; errors have `ok: false` and a nonzero exit code. Parser errors use stderr and exit code 2. A returned image proves capture, not that an application operation succeeded. Inspect the PNG before deciding the next action.

Return to the [suite README](../README.md) or continue with [Mouse](mouse.md).
