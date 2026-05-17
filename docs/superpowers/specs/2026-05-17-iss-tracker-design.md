# ISS Tracker — Design

**Date:** 2026-05-17
**Status:** Approved (brainstorming)

## Goal

A terminal application that renders the International Space Station's live position on a rotating Braille globe. Auto-tracks the ISS so its sub-point stays roughly centered. A small panel shows live latitude, longitude, altitude, and velocity. A fading trail behind the marker shows recent ground track.

Heavily inspired by the sibling project [NetOrbit](../../../../NetOrbit), whose Braille canvas primitives and Natural Earth land mask are vendored in.

## Non-goals

- TLE / SGP4 orbital propagation. Trail is purely "remembered" recent positions.
- Pass predictions for a user location.
- Multiple satellites, ground stations, or downlink visualization.
- Reverse-geocoding (no "over Brazil" text).
- Alerts / notifications / sound.
- A flat-map fallback. Globe only.
- Mouse interaction or arrow-key globe control.

## Architecture

```
iss-tracker/
├── pyproject.toml
├── README.md
├── docs/
│   └── superpowers/specs/2026-05-17-iss-tracker-design.md
└── src/iss_tracker/
    ├── __init__.py
    ├── main.py          # entry point, Rich Live loop
    ├── cli.py           # argparse, flags
    ├── iss_api.py       # wheretheiss.at async client
    ├── globe.py         # orthographic globe renderer (the new piece)
    ├── land_mask.py     # vendored 360×180 land mask from NetOrbit
    ├── braille.py       # vendored 2×4 Braille canvas primitives
    ├── trail.py         # ring buffer of recent (lat, lon, ts)
    ├── theme.py         # color themes (mirror NetOrbit)
    └── ui.py            # Rich layout: globe + stats panel
```

One job per module. `globe.py` is the only piece doing 3D math; everything else is plumbing.

## Data flow

```
┌──────────────┐    poll      ┌─────────┐    update     ┌────────┐
│ wheretheiss  │ ───5s──────▶ │ iss_api │ ───────────▶  │ state  │
└──────────────┘              └─────────┘               │        │
                                                        │ - last │
┌──────────────┐    tick                                │   sub  │
│ render loop  │ ───10fps──┐                            │   point│
└──────────────┘           │                            │ - trail│
        ▲                  ▼                            │   ring │
        │           ┌────────────┐    sub_point         │   buf  │
        │           │ tracker    │ ──────────────────▶  └────────┘
        │           │ (smoothing │                            │
        │           │  + interp) │                            │
        │           └────────────┘                            │
        │                                                     │
        │           ┌────────────┐                            │
        └────────── │   ui.py    │ ◀──────────────────────────┘
                    │ (globe +   │
                    │  stats)    │
                    └────────────┘
```

The API poller and the render loop run independently; the render loop reads whatever the latest state is and interpolates between samples for smooth motion.

## Globe renderer (`globe.py`)

**Approach: per-cell inverse orthographic projection.**

For each Braille sub-pixel `(sx, sy)` on screen:

1. Normalize screen coordinates to `(u, v) ∈ [-1, 1]²` with aspect correction so the globe looks round in a terminal where characters are ~2:1 tall:wide and Braille cells are 2 dots wide × 4 dots tall.
2. If `u² + v² > 1`, the pixel is off the visible disc — leave it as background (space) or a faint star.
3. Otherwise compute `w = √(1 − u² − v²)`, giving a point `(u, v, w)` on the unit sphere in camera space (visible hemisphere).
4. Rotate `(u, v, w)` from camera space back to world space using the inverse of the camera rotation `R_view`. The camera rotation is chosen so that the ISS sub-point `(lat_view, lon_view)` maps to `(0, 0, 1)` in camera space. This is two Euler rotations: rotate world by `−lon_view` around the polar axis, then by `−(90° − lat_view)` around the horizontal axis.
5. Convert the resulting world-space `(x, y, z)` back to `(lat, lon)`.
6. Index `(lat, lon)` into the vendored 360×180 land mask. If land, plot to the Braille canvas with the land style; otherwise the cell stays background.

For the trail: same projection forward. For each stored `(lat, lon)`, convert to world cartesian, apply `R_view` to put it in camera space, check `z ≥ 0` (visible hemisphere). If visible, the screen position is `(u·R, v·R)` where `R` is the sphere radius in screen units. Plot to the same Braille canvas with intensity proportional to recency.

The ISS marker itself is just the most recent trail point rendered as a bright dot.

### Sizing

The globe disc fits inside whatever portion of the terminal the layout gives it. Compute radius as `min(width, height·2) / 2` Braille sub-pixels (the `·2` corrects for character aspect). The renderer is resolution-agnostic — the same code works for an 80×24 terminal or a 200×60 one.

## ISS data source (`iss_api.py`)

- Endpoint: `GET https://api.wheretheiss.at/v1/satellites/25544`
- Response includes: `latitude`, `longitude`, `altitude` (km), `velocity` (km/h), `timestamp`.
- No API key. Free tier rate limit ~1 req/sec; we poll every **5 seconds**.
- Async (`aiohttp` or `httpx`), with exponential backoff on failure (1s → 2s → 4s, cap 30s). On extended failure, the UI shows "stale" indicator next to coords but keeps rendering with last known state.

## Position smoothing & globe tracking

Two interpolations layered:

1. **Sub-point interpolation**: between API polls, advance the ISS sub-point linearly from the previous sample toward the latest one, paced by wall-clock time. Render uses this interpolated value.
2. **View damping**: the view target (`lat_view`, `lon_view`) chases the interpolated sub-point with first-order exponential damping (e.g. `view += 0.15 · (target − view)` per frame), so the globe doesn't jitter and rotation looks smooth. Handles longitude wrap-around (take shortest path).

## Trail (`trail.py`)

- Ring buffer, fixed capacity (`30 min ÷ 5s = 360 entries`).
- Each entry: `(lat, lon, timestamp)`.
- Each poll appends; oldest is evicted when full.
- Rendering reads the buffer, projects each point, and styles by `age = now − ts`: newer = bright, older = dim, oldest = invisible (linear fade).

## UI (`ui.py`)

Rich `Live` loop at 10 FPS. `Layout` splits the screen:

- **Left**: globe panel (takes ~75% width). Border title "ISS".
- **Right**: stats panel (fixed ~24 columns):
  - `LAT  -34.21°`
  - `LON +151.07°`
  - `ALT  421.6 km`
  - `VEL 27620 km/h`
  - `AGE  3s` (seconds since last successful poll; turns dim/red if stale)

Themes mirror NetOrbit: `default`, `green`, `red`, `violet` — same color tokens for land, marker, trail gradient, grid.

## CLI (`cli.py`)

```
iss-tracker [--fps N] [--poll SECONDS] [--theme NAME] [--demo]
```

- `--fps`: render rate. Default `10`.
- `--poll`: API poll interval seconds. Default `5`. Min `2` (rate-limit respect).
- `--theme`: `default | green | red | violet`. Default `default`.
- `--demo`: skip the API, generate synthetic ISS motion (a 90-minute inclined orbit) for offline testing and demos.

## Testing

Unit tests only, no integration tests. The renderer is visual; hand-verify by running it.

- `tests/test_globe.py`: orthographic projection round-trip — pick known `(lat, lon)`, project to screen with a known view, project back, assert it lands near the input. Hidden-hemisphere culling: a point on the antipode of `view` should be culled. Edge: pixel at `u² + v² = 1` exactly.
- `tests/test_trail.py`: ring buffer capacity, eviction order, age computation.
- `tests/test_iss_api.py`: parse a captured API response into the internal model; verify backoff on injected failures (mocked transport).
- `tests/test_land_mask.py`: a few known land points (London, Sydney CBD) return `True`; known ocean points (mid-Pacific) return `False`.

## Reuse from NetOrbit

Vendored verbatim (with attribution comment), since NetOrbit is MIT and not packaged as a library:

- The Natural Earth 1:110m land mask (`LAND_MASK_B85` constant + decoder in [NetOrbit/src/netorbit/world_map.py:39](../../../../NetOrbit/src/netorbit/world_map.py#L39)).
- Braille bit table & `BRAILLE_CHARS` lookup ([NetOrbit/src/netorbit/world_map.py:26-35](../../../../NetOrbit/src/netorbit/world_map.py#L26-L35)).
- `BrailleCanvas` plot/composite primitives ([NetOrbit/src/netorbit/world_map.py:65-111](../../../../NetOrbit/src/netorbit/world_map.py#L65-L111)).
- `Theme` color tokens (subset — land, marker, trail gradient, background).

**Not reused:** equirectangular `geo_to_canvas`, ballistic Bezier trail drawing, packet capture, GeoIP, CLI plumbing. Those are NetOrbit-specific.

## Open questions (deferred to implementation)

- Exact HTTP client: `httpx` vs `aiohttp`. Lean `httpx` for simpler async-sync interop.
- Whether to render a faint star background outside the globe disc. Stretch — drop if it adds noise.
- Whether the globe disc gets a 1-cell border / limb highlight. Probably yes for legibility.
