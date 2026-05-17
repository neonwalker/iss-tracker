# ISS Tracker Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a terminal app (`iss-tracker`) that renders the ISS on a rotating Braille globe with a live stats panel and a fading 30-min ground track.

**Architecture:** Python + Rich. A render loop ticks at 10 FPS, an async poller hits `wheretheiss.at` every 5s. The globe uses per-cell inverse orthographic projection against a vendored 360×180 land mask (from NetOrbit, MIT). The view damps toward the ISS sub-point so motion is smooth. Modules are small and single-purpose; pure math and state lives outside the renderer for tests.

**Tech Stack:** Python 3.10+, Rich (TUI), httpx (async HTTP), pytest + pytest-asyncio (tests), hatchling (build).

**Spec:** [docs/superpowers/specs/2026-05-17-iss-tracker-design.md](../specs/2026-05-17-iss-tracker-design.md)

**Vendored source:** NetOrbit lives at `../NetOrbit/` (sibling). Specifically, [`src/netorbit/world_map.py`](../../../../NetOrbit/src/netorbit/world_map.py) is the reference for the land mask and Braille primitives. Copy verbatim with an attribution comment; do not import from NetOrbit.

---

## File Structure

Final layout after all tasks are done:

```
iss-tracker/
├── pyproject.toml
├── README.md
├── .gitignore
├── docs/
│   └── superpowers/
│       ├── specs/2026-05-17-iss-tracker-design.md
│       └── plans/2026-05-17-iss-tracker.md
├── src/iss_tracker/
│   ├── __init__.py
│   ├── main.py          # entry point + Rich Live loop
│   ├── cli.py           # argparse, flags, demo mode synth
│   ├── iss_api.py       # async wheretheiss.at client
│   ├── globe.py         # orthographic globe renderer
│   ├── tracker.py       # view damping + sub-point interpolation
│   ├── trail.py         # ring buffer of recent positions
│   ├── land_mask.py     # vendored 360×180 land mask + lookup
│   ├── braille.py       # vendored 2×4 Braille canvas
│   ├── theme.py         # color tokens
│   └── ui.py            # Rich layout (globe + stats panel)
└── tests/
    ├── __init__.py
    ├── test_land_mask.py
    ├── test_braille.py
    ├── test_projection.py
    ├── test_trail.py
    ├── test_iss_api.py
    ├── test_tracker.py
    └── test_globe.py
```

All work happens in `/home/neo/Projects/iss/iss-tracker/`. Git is already initialized there.

---

## Task 1: Project skeleton

**Files:**
- Create: `pyproject.toml`
- Create: `.gitignore`
- Create: `README.md`
- Create: `src/iss_tracker/__init__.py`
- Create: `tests/__init__.py`
- Create: `tests/test_smoke.py`

- [ ] **Step 1: Write `pyproject.toml`**

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "iss-tracker"
version = "0.1.0"
description = "Live ISS position on a rotating Braille globe in your terminal"
readme = "README.md"
license = {text = "MIT"}
requires-python = ">=3.10"
dependencies = [
    "rich>=13.7.0",
    "httpx>=0.27.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0",
    "pytest-asyncio>=0.23",
    "respx>=0.21",
]

[project.scripts]
iss-tracker = "iss_tracker.main:main"

[tool.hatch.build.targets.wheel]
packages = ["src/iss_tracker"]

[tool.pytest.ini_options]
testpaths = ["tests"]
asyncio_mode = "auto"
```

- [ ] **Step 2: Write `.gitignore`**

```
__pycache__/
*.py[cod]
*.egg-info/
.pytest_cache/
.venv/
venv/
dist/
build/
.coverage
```

- [ ] **Step 3: Write `README.md`**

```markdown
# iss-tracker

Live ISS position on a rotating Braille globe in your terminal.

## Install

```bash
pipx install .
```

## Run

```bash
iss-tracker
iss-tracker --theme green
iss-tracker --demo          # offline synthetic motion
```

## Credits

Land mask and Braille rendering primitives adapted from [NetOrbit](https://github.com/ZXCurban/NetOrbit) (MIT).
```

- [ ] **Step 4: Write `src/iss_tracker/__init__.py`**

```python
__version__ = "0.1.0"
```

- [ ] **Step 5: Write `tests/__init__.py`**

(Empty file — makes `tests/` a package.)

- [ ] **Step 6: Write `tests/test_smoke.py`**

```python
import iss_tracker


def test_package_importable():
    assert iss_tracker.__version__ == "0.1.0"
```

- [ ] **Step 7: Create venv and install in editable mode**

```bash
python3 -m venv .venv
.venv/bin/pip install -e ".[dev]"
```

Expected: installs cleanly, exits 0.

- [ ] **Step 8: Run the smoke test**

```bash
.venv/bin/pytest tests/test_smoke.py -v
```

Expected: 1 passed.

- [ ] **Step 9: Commit**

```bash
git add pyproject.toml .gitignore README.md src tests
git commit -m "chore: project skeleton with smoke test"
```

---

## Task 2: Land mask (vendored from NetOrbit)

**Files:**
- Create: `src/iss_tracker/land_mask.py`
- Create: `tests/test_land_mask.py`

- [ ] **Step 1: Write the failing test**

`tests/test_land_mask.py`:
```python
from iss_tracker.land_mask import is_land


def test_london_is_land():
    assert is_land(51.5, -0.1) is True


def test_sydney_is_land():
    assert is_land(-33.87, 151.21) is True


def test_mid_pacific_is_ocean():
    assert is_land(0.0, -150.0) is False


def test_mid_atlantic_is_ocean():
    assert is_land(0.0, -30.0) is False


def test_antarctica_is_land():
    assert is_land(-85.0, 0.0) is True


def test_longitude_wraps():
    # 181 should behave like -179
    assert is_land(0.0, 181.0) == is_land(0.0, -179.0)


def test_latitude_clamps_at_poles():
    # Above 90 / below -90 should not raise
    assert is_land(95.0, 0.0) == is_land(90.0, 0.0)
    assert is_land(-95.0, 0.0) == is_land(-90.0, 0.0)
```

- [ ] **Step 2: Run to verify all fail**

```bash
.venv/bin/pytest tests/test_land_mask.py -v
```

Expected: ImportError / module not found.

- [ ] **Step 3: Write `src/iss_tracker/land_mask.py`**

Copy `LAND_MASK_B85` (the multi-line base85 blob) verbatim from `../NetOrbit/src/netorbit/world_map.py` lines 39–41 — it's the giant string assigned to `LAND_MASK_B85`. Don't retype it; use the editor to copy-paste.

The full module:

```python
"""360x180 Natural Earth 1:110m land mask.

Vendored from NetOrbit (https://github.com/ZXCurban/NetOrbit), MIT-licensed.
The mask is one bit per 1-degree cell, row-major, lat top-down (90..-90), lon
left-to-right (-180..180).
"""

from __future__ import annotations

import base64
import zlib
from functools import lru_cache

MASK_WIDTH = 360
MASK_HEIGHT = 180

# --- BEGIN VENDORED FROM NetOrbit/src/netorbit/world_map.py ---
LAND_MASK_B85 = """
<paste the entire multi-line base85 string from NetOrbit/src/netorbit/world_map.py:39-41 here, exactly as-is, including the surrounding triple quotes and .strip() chain>
""".strip()
# --- END VENDORED ---


@lru_cache(maxsize=1)
def _mask_bytes() -> bytes:
    return zlib.decompress(base64.b85decode(LAND_MASK_B85.encode("ascii")))


def is_land_index(x: int, y: int) -> bool:
    """Look up a cell in the raw 360x180 grid (no clamping, no wrap)."""
    data = _mask_bytes()
    index = y * MASK_WIDTH + x
    return bool(data[index // 8] & (1 << (index % 8)))


def is_land(lat: float, lon: float) -> bool:
    """Look up a (lat, lon) coordinate. Wraps longitude, clamps latitude."""
    # Clamp lat to [-90, 90]
    if lat > 90.0:
        lat = 90.0
    elif lat < -90.0:
        lat = -90.0
    # Wrap lon to [-180, 180)
    lon = ((lon + 180.0) % 360.0) - 180.0

    x = int((lon + 180.0) / 360.0 * MASK_WIDTH)
    y = int((90.0 - lat) / 180.0 * MASK_HEIGHT)
    if x >= MASK_WIDTH:
        x = MASK_WIDTH - 1
    if y >= MASK_HEIGHT:
        y = MASK_HEIGHT - 1
    if x < 0:
        x = 0
    if y < 0:
        y = 0
    return is_land_index(x, y)
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
.venv/bin/pytest tests/test_land_mask.py -v
```

Expected: 7 passed. If a specific city/ocean point disagrees with the mask (the 1:110m resolution misses some small features), adjust the test coordinate by 1–2 degrees inland/offshore until it matches reality, but DO NOT loosen the API — the function should be deterministic.

- [ ] **Step 5: Commit**

```bash
git add src/iss_tracker/land_mask.py tests/test_land_mask.py
git commit -m "feat: vendored 360x180 land mask with lat/lon lookup"
```

---

## Task 3: Braille canvas (vendored from NetOrbit)

**Files:**
- Create: `src/iss_tracker/braille.py`
- Create: `tests/test_braille.py`

- [ ] **Step 1: Write the failing test**

`tests/test_braille.py`:
```python
from iss_tracker.braille import BRAILLE_BASE, BrailleCanvas


def test_empty_canvas_renders_spaces():
    canvas = BrailleCanvas(width=4, height=2)
    rows = canvas.to_chars()
    assert len(rows) == 2
    assert all(len(row) == 4 for row in rows)
    assert all(ch == "⠀" for row in rows for ch in row)


def test_plot_dot_sets_correct_bit():
    canvas = BrailleCanvas(width=2, height=1)
    canvas.plot(0, 0)  # top-left dot of cell (0,0)
    rows = canvas.to_chars()
    assert ord(rows[0][0]) == BRAILLE_BASE | 0x01


def test_plot_bottom_right_dot():
    canvas = BrailleCanvas(width=2, height=1)
    canvas.plot(1, 3)  # bottom-right dot of cell (0,0)
    rows = canvas.to_chars()
    assert ord(rows[0][0]) == BRAILLE_BASE | 0x80


def test_plot_outside_bounds_is_noop():
    canvas = BrailleCanvas(width=2, height=1)
    canvas.plot(-1, 0)
    canvas.plot(100, 0)
    canvas.plot(0, -1)
    canvas.plot(0, 100)
    rows = canvas.to_chars()
    assert all(ch == "⠀" for row in rows for ch in row)


def test_intensity_tracks_max():
    canvas = BrailleCanvas(width=2, height=1)
    canvas.plot(0, 0, intensity=0.3)
    canvas.plot(0, 0, intensity=0.9)
    canvas.plot(0, 0, intensity=0.5)
    assert canvas.intensity_at_char(0, 0) == 0.9


def test_virtual_dimensions():
    canvas = BrailleCanvas(width=10, height=5)
    assert canvas.virtual_width == 20
    assert canvas.virtual_height == 20
```

- [ ] **Step 2: Run to verify all fail**

```bash
.venv/bin/pytest tests/test_braille.py -v
```

Expected: ImportError.

- [ ] **Step 3: Write `src/iss_tracker/braille.py`**

Adapted from `../NetOrbit/src/netorbit/world_map.py` lines 26–35 and 65–111:

```python
"""2x4-dot Braille canvas primitives.

Vendored from NetOrbit (MIT). Each terminal cell is U+2800 + 8-bit pattern,
where each bit corresponds to one of 2 columns x 4 rows of sub-pixels.
"""

from __future__ import annotations

# Bit at [row][col]
BRAILLE_BITS: tuple[tuple[int, int], ...] = (
    (0x01, 0x08),
    (0x02, 0x10),
    (0x04, 0x20),
    (0x40, 0x80),
)

VIRTUAL_DOT_WIDTH = 2
VIRTUAL_DOT_HEIGHT = 4

BRAILLE_BASE = 0x2800
BRAILLE_CHARS: tuple[str, ...] = tuple(chr(BRAILLE_BASE + p) for p in range(256))


class BrailleCanvas:
    """A grid of `width x height` terminal cells, each holding a Braille pattern."""

    __slots__ = ("width", "height", "virtual_width", "virtual_height",
                 "_patterns", "_intensities")

    def __init__(self, width: int, height: int) -> None:
        self.width = width
        self.height = height
        self.virtual_width = width * VIRTUAL_DOT_WIDTH
        self.virtual_height = height * VIRTUAL_DOT_HEIGHT
        n = width * height
        self._patterns = [0] * n
        self._intensities = [0.0] * n

    def plot(self, x: int, y: int, intensity: float = 1.0) -> None:
        """Plot a single sub-pixel at virtual coordinates (x, y)."""
        if not (0 <= x < self.virtual_width and 0 <= y < self.virtual_height):
            return
        char_x = x // VIRTUAL_DOT_WIDTH
        char_y = y // VIRTUAL_DOT_HEIGHT
        i = char_y * self.width + char_x
        self._patterns[i] |= BRAILLE_BITS[y % VIRTUAL_DOT_HEIGHT][x % VIRTUAL_DOT_WIDTH]
        if intensity > self._intensities[i]:
            self._intensities[i] = 1.0 if intensity > 1.0 else intensity

    def pattern_at_char(self, char_x: int, char_y: int) -> int:
        return self._patterns[char_y * self.width + char_x]

    def intensity_at_char(self, char_x: int, char_y: int) -> float:
        return self._intensities[char_y * self.width + char_x]

    def to_chars(self) -> list[list[str]]:
        rows: list[list[str]] = []
        for y in range(self.height):
            row = [BRAILLE_CHARS[self._patterns[y * self.width + x]]
                   for x in range(self.width)]
            rows.append(row)
        return rows
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
.venv/bin/pytest tests/test_braille.py -v
```

Expected: 6 passed.

- [ ] **Step 5: Commit**

```bash
git add src/iss_tracker/braille.py tests/test_braille.py
git commit -m "feat: 2x4 braille canvas with intensity tracking"
```

---

## Task 4: Orthographic projection math

**Files:**
- Create: `src/iss_tracker/projection.py`
- Create: `tests/test_projection.py`

This is the renderer's load-bearing math. TDD strictly.

- [ ] **Step 1: Write the failing test**

`tests/test_projection.py`:
```python
import math

import pytest

from iss_tracker.projection import (
    geo_to_unit_sphere,
    unit_sphere_to_geo,
    project_to_screen,
    unproject_from_screen,
)


def assert_close(a: float, b: float, tol: float = 1e-6) -> None:
    assert abs(a - b) < tol, f"{a} != {b} (tol {tol})"


# --- Sphere <-> geo conversion ---

def test_geo_origin_maps_to_x_axis():
    x, y, z = geo_to_unit_sphere(0.0, 0.0)
    assert_close(x, 1.0)
    assert_close(y, 0.0)
    assert_close(z, 0.0)


def test_geo_north_pole_maps_to_z_axis():
    x, y, z = geo_to_unit_sphere(90.0, 0.0)
    assert_close(x, 0.0)
    assert_close(y, 0.0)
    assert_close(z, 1.0)


def test_geo_to_sphere_unit_length():
    for lat, lon in [(45, 30), (-60, 170), (12.5, -34.7), (-89, -180)]:
        x, y, z = geo_to_unit_sphere(lat, lon)
        assert_close(x * x + y * y + z * z, 1.0)


def test_sphere_to_geo_roundtrip():
    for lat, lon in [(45, 30), (-60, 170), (12.5, -34.7), (0, 0)]:
        x, y, z = geo_to_unit_sphere(lat, lon)
        lat2, lon2 = unit_sphere_to_geo(x, y, z)
        assert_close(lat, lat2, tol=1e-6)
        # lon at the poles is ambiguous, but we're not testing poles here
        assert_close(lon, lon2, tol=1e-6)


# --- Forward projection ---

def test_view_target_projects_to_screen_center():
    # Viewing (10, 20), the point (10, 20) should land at screen (0, 0) and be visible.
    sx, sy, visible = project_to_screen(lat=10.0, lon=20.0,
                                        view_lat=10.0, view_lon=20.0)
    assert visible is True
    assert_close(sx, 0.0, tol=1e-6)
    assert_close(sy, 0.0, tol=1e-6)


def test_antipode_is_hidden():
    # Viewing (0, 0), the antipode (0, 180) is on the far side.
    _, _, visible = project_to_screen(lat=0.0, lon=180.0,
                                      view_lat=0.0, view_lon=0.0)
    assert visible is False


def test_quarter_turn_lon_projects_to_unit_x():
    # Viewing (0, 0), the point (0, 90) is on the right limb.
    sx, sy, visible = project_to_screen(lat=0.0, lon=90.0,
                                        view_lat=0.0, view_lon=0.0)
    assert visible is True
    assert_close(sx, 1.0, tol=1e-6)
    assert_close(sy, 0.0, tol=1e-6)


def test_north_pole_projects_above_center():
    # Viewing equator, the north pole sits at the top (positive y in our convention).
    sx, sy, visible = project_to_screen(lat=90.0, lon=0.0,
                                        view_lat=0.0, view_lon=0.0)
    assert visible is True
    assert_close(sx, 0.0, tol=1e-6)
    assert_close(sy, 1.0, tol=1e-6)


# --- Inverse projection ---

def test_screen_center_unprojects_to_view_target():
    lat, lon = unproject_from_screen(sx=0.0, sy=0.0,
                                     view_lat=42.0, view_lon=-17.0)
    assert_close(lat, 42.0, tol=1e-6)
    assert_close(lon, -17.0, tol=1e-6)


def test_unproject_off_disc_returns_none():
    result = unproject_from_screen(sx=0.9, sy=0.9,
                                   view_lat=0.0, view_lon=0.0)
    assert result is None  # 0.9^2 + 0.9^2 > 1


def test_forward_inverse_roundtrip():
    # Pick a visible point and round-trip it.
    view_lat, view_lon = 30.0, -45.0
    for lat, lon in [(35, -40), (10, -50), (20, -30)]:
        sx, sy, visible = project_to_screen(lat, lon, view_lat, view_lon)
        assert visible
        result = unproject_from_screen(sx, sy, view_lat, view_lon)
        assert result is not None
        lat2, lon2 = result
        assert_close(lat, lat2, tol=1e-6)
        assert_close(lon, lon2, tol=1e-6)
```

- [ ] **Step 2: Run to verify all fail**

```bash
.venv/bin/pytest tests/test_projection.py -v
```

Expected: ImportError.

- [ ] **Step 3: Write `src/iss_tracker/projection.py`**

```python
"""Orthographic projection of a unit sphere onto the screen plane.

Conventions:
- World cartesian: (x, y, z) with x out of the prime meridian at the equator,
  z = north pole, y = 90E equator. (Right-handed.)
- Camera frame: after applying the view rotation, the visible hemisphere is the
  one with z' >= 0. Screen x is camera-x', screen y is camera-z'.
- The view rotation takes a target (view_lat, view_lon) to (0, 0, 1) in camera
  space, i.e. centers it on screen.
- Screen coords (sx, sy) are in [-1, 1] (disc radius = 1). sy is positive UP.
"""

from __future__ import annotations

import math


def geo_to_unit_sphere(lat: float, lon: float) -> tuple[float, float, float]:
    lat_r = math.radians(lat)
    lon_r = math.radians(lon)
    cos_lat = math.cos(lat_r)
    x = cos_lat * math.cos(lon_r)
    y = cos_lat * math.sin(lon_r)
    z = math.sin(lat_r)
    return x, y, z


def unit_sphere_to_geo(x: float, y: float, z: float) -> tuple[float, float]:
    # Clamp z to avoid NaN from float drift.
    z = max(-1.0, min(1.0, z))
    lat = math.degrees(math.asin(z))
    lon = math.degrees(math.atan2(y, x))
    return lat, lon


def _view_basis(view_lat: float, view_lon: float
                ) -> tuple[tuple[float, float, float],
                            tuple[float, float, float],
                            tuple[float, float, float]]:
    """Return the camera basis vectors (e_right, e_up, e_forward) in world space.

    Applying the matrix [e_right; e_up; e_forward] to a world point gives the
    camera-space coords (x', y', z'). The view target maps to (0, 0, 1).
    """
    lat_r = math.radians(view_lat)
    lon_r = math.radians(view_lon)
    cos_lat = math.cos(lat_r)
    sin_lat = math.sin(lat_r)
    cos_lon = math.cos(lon_r)
    sin_lon = math.sin(lon_r)
    # Forward (e_z'): the view target itself.
    e_forward = (cos_lat * cos_lon, cos_lat * sin_lon, sin_lat)
    # Up (e_y'): world north projected onto the plane perpendicular to forward.
    # Equivalent to rotating "north" by the same view rotation. Closed form:
    e_up = (-sin_lat * cos_lon, -sin_lat * sin_lon, cos_lat)
    # Right (e_x'): forward x up (right-handed). Closed form:
    e_right = (-sin_lon, cos_lon, 0.0)
    return e_right, e_up, e_forward


def project_to_screen(lat: float, lon: float,
                      view_lat: float, view_lon: float
                      ) -> tuple[float, float, bool]:
    """Return (sx, sy, visible). sx,sy in [-1,1] when visible."""
    p = geo_to_unit_sphere(lat, lon)
    e_right, e_up, e_forward = _view_basis(view_lat, view_lon)
    sx = p[0] * e_right[0] + p[1] * e_right[1] + p[2] * e_right[2]
    sy = p[0] * e_up[0] + p[1] * e_up[1] + p[2] * e_up[2]
    sz = p[0] * e_forward[0] + p[1] * e_forward[1] + p[2] * e_forward[2]
    return sx, sy, sz >= 0.0


def unproject_from_screen(sx: float, sy: float,
                          view_lat: float, view_lon: float
                          ) -> tuple[float, float] | None:
    """Inverse of project_to_screen. Returns None if (sx, sy) is off the disc."""
    r2 = sx * sx + sy * sy
    if r2 > 1.0:
        return None
    sz = math.sqrt(1.0 - r2)
    e_right, e_up, e_forward = _view_basis(view_lat, view_lon)
    # World point = sx*e_right + sy*e_up + sz*e_forward (basis is orthonormal,
    # so the transpose-multiply is the same as inverse-multiply).
    x = sx * e_right[0] + sy * e_up[0] + sz * e_forward[0]
    y = sx * e_right[1] + sy * e_up[1] + sz * e_forward[1]
    z = sx * e_right[2] + sy * e_up[2] + sz * e_forward[2]
    return unit_sphere_to_geo(x, y, z)
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
.venv/bin/pytest tests/test_projection.py -v
```

Expected: 10 passed.

- [ ] **Step 5: Commit**

```bash
git add src/iss_tracker/projection.py tests/test_projection.py
git commit -m "feat: orthographic projection math with round-trip tests"
```

---

## Task 5: Trail ring buffer

**Files:**
- Create: `src/iss_tracker/trail.py`
- Create: `tests/test_trail.py`

- [ ] **Step 1: Write the failing test**

`tests/test_trail.py`:
```python
from iss_tracker.trail import Trail, TrailPoint


def test_empty_trail():
    trail = Trail(capacity=3)
    assert list(trail) == []


def test_append_and_iterate_in_order():
    trail = Trail(capacity=5)
    trail.append(lat=1.0, lon=2.0, timestamp=100.0)
    trail.append(lat=3.0, lon=4.0, timestamp=101.0)
    points = list(trail)
    assert points == [
        TrailPoint(lat=1.0, lon=2.0, timestamp=100.0),
        TrailPoint(lat=3.0, lon=4.0, timestamp=101.0),
    ]


def test_capacity_evicts_oldest():
    trail = Trail(capacity=3)
    trail.append(0.0, 0.0, 100.0)
    trail.append(1.0, 1.0, 101.0)
    trail.append(2.0, 2.0, 102.0)
    trail.append(3.0, 3.0, 103.0)
    timestamps = [p.timestamp for p in trail]
    assert timestamps == [101.0, 102.0, 103.0]


def test_len_reflects_size():
    trail = Trail(capacity=3)
    assert len(trail) == 0
    trail.append(0.0, 0.0, 100.0)
    assert len(trail) == 1
    trail.append(0.0, 0.0, 101.0)
    trail.append(0.0, 0.0, 102.0)
    trail.append(0.0, 0.0, 103.0)
    assert len(trail) == 3  # capped


def test_latest_returns_most_recent():
    trail = Trail(capacity=3)
    assert trail.latest() is None
    trail.append(1.0, 2.0, 100.0)
    trail.append(3.0, 4.0, 200.0)
    assert trail.latest() == TrailPoint(3.0, 4.0, 200.0)
```

- [ ] **Step 2: Run to verify fails**

```bash
.venv/bin/pytest tests/test_trail.py -v
```

Expected: ImportError.

- [ ] **Step 3: Write `src/iss_tracker/trail.py`**

```python
"""Ring buffer of recent ISS positions for trail rendering."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from typing import Iterator


@dataclass(frozen=True, slots=True)
class TrailPoint:
    lat: float
    lon: float
    timestamp: float


class Trail:
    __slots__ = ("_buf",)

    def __init__(self, capacity: int) -> None:
        self._buf: deque[TrailPoint] = deque(maxlen=capacity)

    def append(self, lat: float, lon: float, timestamp: float) -> None:
        self._buf.append(TrailPoint(lat, lon, timestamp))

    def latest(self) -> TrailPoint | None:
        return self._buf[-1] if self._buf else None

    def __iter__(self) -> Iterator[TrailPoint]:
        return iter(self._buf)

    def __len__(self) -> int:
        return len(self._buf)
```

- [ ] **Step 4: Run tests**

```bash
.venv/bin/pytest tests/test_trail.py -v
```

Expected: 5 passed.

- [ ] **Step 5: Commit**

```bash
git add src/iss_tracker/trail.py tests/test_trail.py
git commit -m "feat: trail ring buffer with eviction"
```

---

## Task 6: ISS API client

**Files:**
- Create: `src/iss_tracker/iss_api.py`
- Create: `tests/test_iss_api.py`

- [ ] **Step 1: Write the failing test**

`tests/test_iss_api.py`:
```python
import httpx
import pytest
import respx

from iss_tracker.iss_api import IssApi, IssSample


SAMPLE_JSON = {
    "name": "iss",
    "id": 25544,
    "latitude": -34.21,
    "longitude": 151.07,
    "altitude": 421.6,
    "velocity": 27620.0,
    "visibility": "daylight",
    "footprint": 4530.0,
    "timestamp": 1715900000,
    "daynum": 2460443.0,
    "solar_lat": 19.0,
    "solar_lon": 100.0,
    "units": "kilometers",
}


@respx.mock
@pytest.mark.asyncio
async def test_fetch_parses_response():
    respx.get("https://api.wheretheiss.at/v1/satellites/25544").mock(
        return_value=httpx.Response(200, json=SAMPLE_JSON)
    )
    api = IssApi()
    sample = await api.fetch()
    assert isinstance(sample, IssSample)
    assert sample.lat == -34.21
    assert sample.lon == 151.07
    assert sample.altitude_km == 421.6
    assert sample.velocity_kmh == 27620.0
    assert sample.timestamp == 1715900000


@respx.mock
@pytest.mark.asyncio
async def test_fetch_retries_on_server_error_then_succeeds():
    route = respx.get("https://api.wheretheiss.at/v1/satellites/25544")
    route.side_effect = [
        httpx.Response(503),
        httpx.Response(503),
        httpx.Response(200, json=SAMPLE_JSON),
    ]
    api = IssApi(retry_backoff_seconds=(0.0, 0.0, 0.0))
    sample = await api.fetch()
    assert sample.lat == -34.21
    assert route.call_count == 3


@respx.mock
@pytest.mark.asyncio
async def test_fetch_raises_after_exhausted_retries():
    respx.get("https://api.wheretheiss.at/v1/satellites/25544").mock(
        return_value=httpx.Response(500)
    )
    api = IssApi(retry_backoff_seconds=(0.0, 0.0))
    with pytest.raises(httpx.HTTPStatusError):
        await api.fetch()
```

- [ ] **Step 2: Run to verify fails**

```bash
.venv/bin/pytest tests/test_iss_api.py -v
```

Expected: ImportError.

- [ ] **Step 3: Write `src/iss_tracker/iss_api.py`**

```python
"""Async client for https://wheretheiss.at."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Sequence

import httpx


ISS_ID = 25544
ENDPOINT = f"https://api.wheretheiss.at/v1/satellites/{ISS_ID}"
DEFAULT_BACKOFF = (1.0, 2.0, 4.0, 8.0, 16.0, 30.0)


@dataclass(frozen=True, slots=True)
class IssSample:
    lat: float
    lon: float
    altitude_km: float
    velocity_kmh: float
    timestamp: int


class IssApi:
    def __init__(self, *,
                 client: httpx.AsyncClient | None = None,
                 retry_backoff_seconds: Sequence[float] = DEFAULT_BACKOFF) -> None:
        self._client = client
        self._owns_client = client is None
        self._backoff = tuple(retry_backoff_seconds)

    async def fetch(self) -> IssSample:
        client = self._client or httpx.AsyncClient(timeout=10.0)
        try:
            last_error: Exception | None = None
            attempts = len(self._backoff) + 1
            for attempt in range(attempts):
                try:
                    response = await client.get(ENDPOINT)
                    response.raise_for_status()
                    data = response.json()
                    return IssSample(
                        lat=float(data["latitude"]),
                        lon=float(data["longitude"]),
                        altitude_km=float(data["altitude"]),
                        velocity_kmh=float(data["velocity"]),
                        timestamp=int(data["timestamp"]),
                    )
                except (httpx.HTTPStatusError, httpx.RequestError) as exc:
                    last_error = exc
                    if attempt < attempts - 1:
                        await asyncio.sleep(self._backoff[attempt])
            assert last_error is not None
            raise last_error
        finally:
            if self._owns_client:
                await client.aclose()
```

- [ ] **Step 4: Run tests**

```bash
.venv/bin/pytest tests/test_iss_api.py -v
```

Expected: 3 passed.

- [ ] **Step 5: Commit**

```bash
git add src/iss_tracker/iss_api.py tests/test_iss_api.py
git commit -m "feat: async wheretheiss.at client with retry backoff"
```

---

## Task 7: View tracker (interpolation + damping)

**Files:**
- Create: `src/iss_tracker/tracker.py`
- Create: `tests/test_tracker.py`

- [ ] **Step 1: Write the failing test**

`tests/test_tracker.py`:
```python
import math

import pytest

from iss_tracker.tracker import ViewTracker, shortest_lon_delta


def test_shortest_lon_delta_simple():
    assert shortest_lon_delta(10.0, 20.0) == pytest.approx(10.0)
    assert shortest_lon_delta(20.0, 10.0) == pytest.approx(-10.0)


def test_shortest_lon_delta_wraps_across_antimeridian():
    # 170 -> -170 should be +20 (going east), not -340.
    assert shortest_lon_delta(170.0, -170.0) == pytest.approx(20.0)
    assert shortest_lon_delta(-170.0, 170.0) == pytest.approx(-20.0)


def test_tracker_initial_state_matches_first_target():
    t = ViewTracker(damping=0.2)
    t.set_target(lat=30.0, lon=-45.0)
    lat, lon = t.view()
    assert lat == 30.0
    assert lon == -45.0


def test_tracker_chases_target():
    t = ViewTracker(damping=0.5)
    t.set_target(lat=0.0, lon=0.0)
    t.set_target(lat=10.0, lon=20.0)
    # First step: halfway.
    t.step()
    lat, lon = t.view()
    assert lat == pytest.approx(5.0)
    assert lon == pytest.approx(10.0)
    # Second step: another half.
    t.step()
    lat, lon = t.view()
    assert lat == pytest.approx(7.5)
    assert lon == pytest.approx(15.0)


def test_tracker_takes_shortest_path_across_antimeridian():
    t = ViewTracker(damping=0.5)
    t.set_target(lat=0.0, lon=170.0)
    t.set_target(lat=0.0, lon=-170.0)
    t.step()
    lat, lon = t.view()
    # Should move east by half of +20, landing at 180 == -180.
    assert lat == pytest.approx(0.0)
    # Normalize lon to [-180, 180) for comparison.
    norm = ((lon + 180.0) % 360.0) - 180.0
    assert norm == pytest.approx(-180.0)
```

- [ ] **Step 2: Run to verify fails**

```bash
.venv/bin/pytest tests/test_tracker.py -v
```

Expected: ImportError.

- [ ] **Step 3: Write `src/iss_tracker/tracker.py`**

```python
"""View damping for the globe camera, plus longitude wrap helpers."""

from __future__ import annotations


def shortest_lon_delta(from_lon: float, to_lon: float) -> float:
    """Smallest signed delta to get from from_lon to to_lon, in [-180, 180]."""
    delta = (to_lon - from_lon) % 360.0
    if delta > 180.0:
        delta -= 360.0
    return delta


def _normalize_lon(lon: float) -> float:
    return ((lon + 180.0) % 360.0) - 180.0


class ViewTracker:
    """Exponentially damped chase of a (lat, lon) target."""

    __slots__ = ("_damping", "_lat", "_lon", "_target_lat", "_target_lon",
                 "_initialized")

    def __init__(self, damping: float) -> None:
        if not 0.0 < damping <= 1.0:
            raise ValueError("damping must be in (0, 1]")
        self._damping = damping
        self._lat = 0.0
        self._lon = 0.0
        self._target_lat = 0.0
        self._target_lon = 0.0
        self._initialized = False

    def set_target(self, lat: float, lon: float) -> None:
        self._target_lat = lat
        self._target_lon = lon
        if not self._initialized:
            self._lat = lat
            self._lon = lon
            self._initialized = True

    def step(self) -> None:
        if not self._initialized:
            return
        d_lat = self._target_lat - self._lat
        d_lon = shortest_lon_delta(self._lon, self._target_lon)
        self._lat += self._damping * d_lat
        self._lon = _normalize_lon(self._lon + self._damping * d_lon)
        # Clamp lat to valid range.
        if self._lat > 90.0:
            self._lat = 90.0
        elif self._lat < -90.0:
            self._lat = -90.0

    def view(self) -> tuple[float, float]:
        return self._lat, self._lon
```

- [ ] **Step 4: Run tests**

```bash
.venv/bin/pytest tests/test_tracker.py -v
```

Expected: 5 passed.

- [ ] **Step 5: Commit**

```bash
git add src/iss_tracker/tracker.py tests/test_tracker.py
git commit -m "feat: damped view tracker with longitude wrap"
```

---

## Task 8: Theme

**Files:**
- Create: `src/iss_tracker/theme.py`

No tests — pure data module. Smoke-check by importing in later tasks.

- [ ] **Step 1: Write `src/iss_tracker/theme.py`**

```python
"""Color tokens for globe rendering. Mirrors NetOrbit themes."""

from __future__ import annotations

from dataclasses import dataclass

from rich.style import Style


@dataclass(frozen=True, slots=True)
class Theme:
    name: str
    background: Style
    land: Style
    grid: Style
    iss_marker: Style
    trail_dim: Style
    trail_bright: Style
    panel_label: Style
    panel_value: Style
    panel_stale: Style


_THEMES: dict[str, Theme] = {
    "default": Theme(
        name="default",
        background=Style(color="grey15"),
        land=Style(color="cyan3"),
        grid=Style(color="grey23"),
        iss_marker=Style(color="bright_white", bold=True),
        trail_dim=Style(color="grey42"),
        trail_bright=Style(color="bright_cyan"),
        panel_label=Style(color="grey58"),
        panel_value=Style(color="bright_white", bold=True),
        panel_stale=Style(color="red"),
    ),
    "green": Theme(
        name="green",
        background=Style(color="grey15"),
        land=Style(color="green4"),
        grid=Style(color="grey23"),
        iss_marker=Style(color="bright_white", bold=True),
        trail_dim=Style(color="grey42"),
        trail_bright=Style(color="bright_green"),
        panel_label=Style(color="grey58"),
        panel_value=Style(color="bright_white", bold=True),
        panel_stale=Style(color="red"),
    ),
    "red": Theme(
        name="red",
        background=Style(color="grey15"),
        land=Style(color="red3"),
        grid=Style(color="grey23"),
        iss_marker=Style(color="bright_white", bold=True),
        trail_dim=Style(color="grey42"),
        trail_bright=Style(color="bright_red"),
        panel_label=Style(color="grey58"),
        panel_value=Style(color="bright_white", bold=True),
        panel_stale=Style(color="yellow"),
    ),
    "violet": Theme(
        name="violet",
        background=Style(color="grey15"),
        land=Style(color="purple4"),
        grid=Style(color="grey23"),
        iss_marker=Style(color="bright_white", bold=True),
        trail_dim=Style(color="grey42"),
        trail_bright=Style(color="bright_magenta"),
        panel_label=Style(color="grey58"),
        panel_value=Style(color="bright_white", bold=True),
        panel_stale=Style(color="red"),
    ),
}


def get_theme(name: str) -> Theme:
    if name not in _THEMES:
        raise ValueError(f"unknown theme {name!r}; choose from {sorted(_THEMES)}")
    return _THEMES[name]


def theme_names() -> list[str]:
    return sorted(_THEMES)
```

- [ ] **Step 2: Smoke-check it imports**

```bash
.venv/bin/python -c "from iss_tracker.theme import get_theme; print(get_theme('default').name)"
```

Expected: `default`.

- [ ] **Step 3: Commit**

```bash
git add src/iss_tracker/theme.py
git commit -m "feat: color themes (default/green/red/violet)"
```

---

## Task 9: Globe renderer

**Files:**
- Create: `src/iss_tracker/globe.py`
- Create: `tests/test_globe.py`

- [ ] **Step 1: Write the failing test**

`tests/test_globe.py`:
```python
from iss_tracker.globe import render_globe
from iss_tracker.theme import get_theme
from iss_tracker.trail import Trail


def _count_non_background(canvas, theme):
    bg_style = theme.background
    n = 0
    for row in canvas:
        for cell in row:
            if cell.style != bg_style:
                n += 1
    return n


def test_render_produces_canvas_of_requested_size():
    theme = get_theme("default")
    trail = Trail(capacity=10)
    canvas = render_globe(width=40, height=20,
                          view_lat=0.0, view_lon=0.0,
                          iss_lat=0.0, iss_lon=0.0,
                          trail=trail, theme=theme)
    assert len(canvas) == 20
    assert all(len(row) == 40 for row in canvas)


def test_render_draws_something():
    theme = get_theme("default")
    trail = Trail(capacity=10)
    canvas = render_globe(width=60, height=30,
                          view_lat=0.0, view_lon=0.0,
                          iss_lat=0.0, iss_lon=0.0,
                          trail=trail, theme=theme)
    # The visible hemisphere centered on (0,0) should produce *some* land cells.
    assert _count_non_background(canvas, theme) > 50


def test_iss_marker_cell_has_marker_style():
    theme = get_theme("default")
    trail = Trail(capacity=10)
    iss_lat, iss_lon = 0.0, 0.0  # centered
    canvas = render_globe(width=60, height=30,
                          view_lat=iss_lat, view_lon=iss_lon,
                          iss_lat=iss_lat, iss_lon=iss_lon,
                          trail=trail, theme=theme)
    # Center cell carries the marker.
    center = canvas[15][30]
    assert center.style == theme.iss_marker


def test_corners_are_background():
    theme = get_theme("default")
    trail = Trail(capacity=10)
    canvas = render_globe(width=60, height=30,
                          view_lat=0.0, view_lon=0.0,
                          iss_lat=0.0, iss_lon=0.0,
                          trail=trail, theme=theme)
    # The four corners must be outside the disc.
    assert canvas[0][0].style == theme.background
    assert canvas[0][-1].style == theme.background
    assert canvas[-1][0].style == theme.background
    assert canvas[-1][-1].style == theme.background
```

- [ ] **Step 2: Run to verify fails**

```bash
.venv/bin/pytest tests/test_globe.py -v
```

Expected: ImportError.

- [ ] **Step 3: Write `src/iss_tracker/globe.py`**

```python
"""Orthographic globe renderer. Returns a 2D grid of styled cells."""

from __future__ import annotations

import time
from dataclasses import dataclass

from rich.style import Style

from .braille import BRAILLE_BITS, BRAILLE_CHARS, VIRTUAL_DOT_HEIGHT, VIRTUAL_DOT_WIDTH
from .land_mask import is_land
from .projection import project_to_screen, unproject_from_screen
from .theme import Theme
from .trail import Trail

# How far back in seconds the trail fades from bright to dim. After this it
# rolls off the back of the buffer entirely.
TRAIL_AGE_FOR_FULL_FADE = 30 * 60  # 30 min


@dataclass(frozen=True, slots=True)
class StyledCell:
    char: str
    style: Style


def render_globe(*,
                 width: int, height: int,
                 view_lat: float, view_lon: float,
                 iss_lat: float, iss_lon: float,
                 trail: Trail, theme: Theme,
                 now: float | None = None) -> list[list[StyledCell]]:
    """Render the globe into a 2D list of StyledCell rows.

    Aspect note: terminal characters are roughly 2:1 (tall:wide) and Braille
    puts 2 sub-pixel dots horizontally and 4 vertically per char. Those cancel
    out, so sub-pixels are square in screen units. No aspect correction here.
    """
    if now is None:
        now = time.time()

    bg = StyledCell(" ", theme.background)
    canvas: list[list[StyledCell]] = [[bg] * width for _ in range(height)]

    # Virtual sub-pixel dimensions.
    vw = width * VIRTUAL_DOT_WIDTH
    vh = height * VIRTUAL_DOT_HEIGHT

    radius = min(vw, vh) / 2.0
    cx = vw / 2.0
    cy = vh / 2.0

    # --- Pass 1: land disc. Iterate sub-pixels, inverse-project, hit land mask.
    land_patterns = [0] * (width * height)
    for py in range(vh):
        sy = (cy - py - 0.5) / radius  # positive UP
        if abs(sy) > 1.0:
            continue
        sy2 = sy * sy
        for px in range(vw):
            sx = ((px + 0.5) - cx) / radius
            if sx * sx + sy2 > 1.0:
                continue
            geo = unproject_from_screen(sx, sy, view_lat, view_lon)
            if geo is None:
                continue
            lat, lon = geo
            if not is_land(lat, lon):
                continue
            cx_idx = px // VIRTUAL_DOT_WIDTH
            cy_idx = py // VIRTUAL_DOT_HEIGHT
            i = cy_idx * width + cx_idx
            land_patterns[i] |= BRAILLE_BITS[py % VIRTUAL_DOT_HEIGHT][px % VIRTUAL_DOT_WIDTH]

    for cy_idx in range(height):
        for cx_idx in range(width):
            pattern = land_patterns[cy_idx * width + cx_idx]
            if pattern:
                canvas[cy_idx][cx_idx] = StyledCell(BRAILLE_CHARS[pattern], theme.land)

    # --- Pass 2: trail. Forward-project each stored point.
    for point in trail:
        sx, sy, visible = project_to_screen(point.lat, point.lon, view_lat, view_lon)
        if not visible:
            continue
        px = int(cx + sx * radius)
        py = int(cy - sy * radius)
        if not (0 <= px < vw and 0 <= py < vh):
            continue
        char_x = px // VIRTUAL_DOT_WIDTH
        char_y = py // VIRTUAL_DOT_HEIGHT
        age = max(0.0, now - point.timestamp)
        recency = max(0.0, 1.0 - age / TRAIL_AGE_FOR_FULL_FADE)
        style = theme.trail_bright if recency > 0.5 else theme.trail_dim
        canvas[char_y][char_x] = StyledCell("•", style)

    # --- Pass 3: ISS marker (overrides whatever was at its cell).
    sx, sy, visible = project_to_screen(iss_lat, iss_lon, view_lat, view_lon)
    if visible:
        px = int(cx + sx * radius)
        py = int(cy - sy * radius)
        if 0 <= px < vw and 0 <= py < vh:
            char_x = px // VIRTUAL_DOT_WIDTH
            char_y = py // VIRTUAL_DOT_HEIGHT
            canvas[char_y][char_x] = StyledCell("●", theme.iss_marker)

    return canvas
```

- [ ] **Step 4: Run tests**

```bash
.venv/bin/pytest tests/test_globe.py -v
```

Expected: 4 passed. If `test_render_draws_something` returns too few cells, the per-pixel sampling may be too sparse — verify the `radius` computation. If the marker test fails because of off-by-one cell rounding, adjust the marker cell index check in the test to allow ±1 cell tolerance.

- [ ] **Step 5: Commit**

```bash
git add src/iss_tracker/globe.py tests/test_globe.py
git commit -m "feat: orthographic globe renderer with land disc, trail, marker"
```

---

## Task 10: UI layout

**Files:**
- Create: `src/iss_tracker/ui.py`

No unit tests — Rich rendering is visual. Smoke-check it composes.

- [ ] **Step 1: Write `src/iss_tracker/ui.py`**

```python
"""Rich layout composition: globe panel + stats panel."""

from __future__ import annotations

import time
from dataclasses import dataclass

from rich.align import Align
from rich.console import Console, ConsoleOptions, RenderResult
from rich.layout import Layout
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from .globe import StyledCell, render_globe
from .iss_api import IssSample
from .theme import Theme
from .tracker import ViewTracker
from .trail import Trail


@dataclass
class AppState:
    last_sample: IssSample | None = None
    last_sample_at: float = 0.0
    last_error: str | None = None


class GlobePane:
    def __init__(self, *, tracker: ViewTracker, trail: Trail, theme: Theme,
                 state: AppState) -> None:
        self._tracker = tracker
        self._trail = trail
        self._theme = theme
        self._state = state

    def __rich_console__(self, console: Console, options: ConsoleOptions) -> RenderResult:
        width = options.max_width
        height = options.height or 24
        view_lat, view_lon = self._tracker.view()
        sample = self._state.last_sample
        if sample is None:
            yield Text("Waiting for ISS data...", style=self._theme.panel_label)
            return
        canvas = render_globe(width=width, height=height,
                              view_lat=view_lat, view_lon=view_lon,
                              iss_lat=sample.lat, iss_lon=sample.lon,
                              trail=self._trail, theme=self._theme)
        yield _canvas_to_text(canvas)


def _canvas_to_text(canvas: list[list[StyledCell]]) -> Text:
    text = Text()
    for y, row in enumerate(canvas):
        if not row:
            continue
        run_style = row[0].style
        run_chars: list[str] = []
        for cell in row:
            if cell.style == run_style:
                run_chars.append(cell.char)
                continue
            text.append("".join(run_chars), style=run_style)
            run_style = cell.style
            run_chars = [cell.char]
        text.append("".join(run_chars), style=run_style)
        if y < len(canvas) - 1:
            text.append("\n")
    return text


def stats_panel(state: AppState, theme: Theme, now: float | None = None) -> Panel:
    if now is None:
        now = time.time()

    table = Table.grid(padding=(0, 1))
    table.add_column(justify="left", style=theme.panel_label)
    table.add_column(justify="right", style=theme.panel_value)

    sample = state.last_sample
    if sample is None:
        table.add_row("LAT", "—")
        table.add_row("LON", "—")
        table.add_row("ALT", "—")
        table.add_row("VEL", "—")
    else:
        table.add_row("LAT", f"{sample.lat:+8.2f}°")
        table.add_row("LON", f"{sample.lon:+8.2f}°")
        table.add_row("ALT", f"{sample.altitude_km:6.1f} km")
        table.add_row("VEL", f"{sample.velocity_kmh:6.0f} km/h")

    age = now - state.last_sample_at if state.last_sample_at else None
    if age is None:
        age_text = Text("—", style=theme.panel_value)
    elif age > 30:
        age_text = Text(f"{int(age)}s (stale)", style=theme.panel_stale)
    else:
        age_text = Text(f"{int(age)}s", style=theme.panel_value)
    table.add_row("AGE", age_text)

    if state.last_error:
        table.add_row("ERR", Text(state.last_error[:18], style=theme.panel_stale))

    return Panel(table, title="ISS", title_align="left",
                 border_style=theme.panel_label)


def build_layout(*, tracker: ViewTracker, trail: Trail, theme: Theme,
                 state: AppState) -> Layout:
    layout = Layout()
    layout.split_row(
        Layout(name="globe", ratio=4),
        Layout(name="stats", size=26),
    )
    layout["globe"].update(Align.center(
        GlobePane(tracker=tracker, trail=trail, theme=theme, state=state),
        vertical="middle",
    ))
    layout["stats"].update(stats_panel(state, theme))
    return layout
```

- [ ] **Step 2: Smoke-check import**

```bash
.venv/bin/python -c "from iss_tracker.ui import build_layout, AppState; print('ok')"
```

Expected: `ok`.

- [ ] **Step 3: Commit**

```bash
git add src/iss_tracker/ui.py
git commit -m "feat: rich layout with globe pane and stats panel"
```

---

## Task 11: CLI + main entry + demo mode

**Files:**
- Create: `src/iss_tracker/cli.py`
- Create: `src/iss_tracker/main.py`

- [ ] **Step 1: Write `src/iss_tracker/cli.py`**

```python
"""Argparse wiring + synthetic demo sample generator."""

from __future__ import annotations

import argparse
import math
import time
from dataclasses import dataclass

from .iss_api import IssSample
from .theme import theme_names


@dataclass(frozen=True, slots=True)
class Args:
    fps: int
    poll: float
    theme: str
    demo: bool


def parse_args(argv: list[str] | None = None) -> Args:
    parser = argparse.ArgumentParser(
        prog="iss-tracker",
        description="Live ISS position on a rotating Braille globe.",
    )
    parser.add_argument("--fps", type=int, default=10,
                        help="render frames per second (default: 10)")
    parser.add_argument("--poll", type=float, default=5.0,
                        help="API poll interval seconds (default: 5, min 2)")
    parser.add_argument("--theme", choices=theme_names(), default="default")
    parser.add_argument("--demo", action="store_true",
                        help="use synthetic ISS motion instead of the API")
    ns = parser.parse_args(argv)
    if ns.poll < 2.0:
        parser.error("--poll must be >= 2.0")
    if ns.fps < 1 or ns.fps > 60:
        parser.error("--fps must be in [1, 60]")
    return Args(fps=ns.fps, poll=ns.poll, theme=ns.theme, demo=ns.demo)


class DemoSource:
    """Generates synthetic ISS samples following a 51.6 deg inclined orbit."""

    INCLINATION_DEG = 51.6
    PERIOD_SECONDS = 90.0 * 60.0
    ALTITUDE_KM = 420.0
    VELOCITY_KMH = 27600.0

    def __init__(self, t0: float | None = None) -> None:
        self._t0 = t0 if t0 is not None else time.time()

    async def fetch(self) -> IssSample:
        now = time.time()
        t = now - self._t0
        # Mean anomaly along the orbit (radians).
        anomaly = 2.0 * math.pi * (t % self.PERIOD_SECONDS) / self.PERIOD_SECONDS
        incl = math.radians(self.INCLINATION_DEG)
        # Position on great circle; sub-point ignores Earth rotation drift for demo.
        x = math.cos(anomaly)
        y = math.sin(anomaly) * math.cos(incl)
        z = math.sin(anomaly) * math.sin(incl)
        lat = math.degrees(math.asin(z))
        lon = math.degrees(math.atan2(y, x))
        # Approximate eastward drift due to Earth rotation in real life; here we
        # add a slow westward longitudinal drift so successive orbits don't
        # overlap exactly.
        lon -= (t / self.PERIOD_SECONDS) * 22.5
        lon = ((lon + 180.0) % 360.0) - 180.0
        return IssSample(
            lat=lat, lon=lon,
            altitude_km=self.ALTITUDE_KM,
            velocity_kmh=self.VELOCITY_KMH,
            timestamp=int(now),
        )
```

- [ ] **Step 2: Write `src/iss_tracker/main.py`**

```python
"""Entry point. Runs the async poller and the Rich Live render loop."""

from __future__ import annotations

import asyncio
import time

from rich.console import Console
from rich.live import Live

from .cli import Args, DemoSource, parse_args
from .iss_api import IssApi
from .theme import get_theme
from .tracker import ViewTracker
from .trail import Trail
from .ui import AppState, build_layout, stats_panel


VIEW_DAMPING = 0.15  # per render frame
TRAIL_MINUTES = 30
DAMPED_STEPS_PER_FRAME = 1


async def _poller(source, state: AppState, trail: Trail, tracker: ViewTracker,
                  poll_seconds: float, stop: asyncio.Event) -> None:
    while not stop.is_set():
        try:
            sample = await source.fetch()
        except Exception as exc:  # network errors land here after retries
            state.last_error = type(exc).__name__
        else:
            state.last_sample = sample
            state.last_sample_at = time.time()
            state.last_error = None
            trail.append(sample.lat, sample.lon, float(sample.timestamp))
            tracker.set_target(sample.lat, sample.lon)
        try:
            await asyncio.wait_for(stop.wait(), timeout=poll_seconds)
        except asyncio.TimeoutError:
            pass


async def _render_loop(args: Args, source, console: Console) -> None:
    theme = get_theme(args.theme)
    trail_capacity = int(TRAIL_MINUTES * 60 / args.poll)
    trail = Trail(capacity=trail_capacity)
    tracker = ViewTracker(damping=VIEW_DAMPING)
    state = AppState()

    stop = asyncio.Event()
    poll_task = asyncio.create_task(
        _poller(source, state, trail, tracker, args.poll, stop)
    )

    frame_interval = 1.0 / args.fps
    layout = build_layout(tracker=tracker, trail=trail, theme=theme, state=state)
    try:
        with Live(layout, console=console, screen=True,
                  refresh_per_second=args.fps) as live:
            while True:
                for _ in range(DAMPED_STEPS_PER_FRAME):
                    tracker.step()
                # Rebuild the stats panel each frame (table is small).
                layout["stats"].update(stats_panel(state, theme))
                live.refresh()
                await asyncio.sleep(frame_interval)
    except (KeyboardInterrupt, asyncio.CancelledError):
        pass
    finally:
        stop.set()
        await poll_task


def main() -> None:
    args = parse_args()
    console = Console()
    source = DemoSource() if args.demo else IssApi()
    try:
        asyncio.run(_render_loop(args, source, console))
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
```

- [ ] **Step 3: Smoke-check CLI parses**

```bash
.venv/bin/python -m iss_tracker.cli --help 2>&1 | head -20
.venv/bin/iss-tracker --help
```

Expected: argparse help text including `--fps`, `--poll`, `--theme`, `--demo`.

- [ ] **Step 4: Run the demo mode briefly**

```bash
timeout 3 .venv/bin/iss-tracker --demo --fps 5 || true
```

Expected: terminal enters alternate screen, shows a globe and stats, exits cleanly after 3s. If you see a Python exception, fix it before continuing. Common things to check: terminal size (resize to at least 80x24), `Layout` ratios giving the globe a usable width.

- [ ] **Step 5: Commit**

```bash
git add src/iss_tracker/cli.py src/iss_tracker/main.py
git commit -m "feat: CLI, async render loop, and synthetic demo source"
```

---

## Task 12: Full test pass + end-to-end run

- [ ] **Step 1: Run the full test suite**

```bash
.venv/bin/pytest -v
```

Expected: all tests pass. No skipped tests. If any test fails, fix it before continuing.

- [ ] **Step 2: Manual live run (network required)**

```bash
timeout 15 .venv/bin/iss-tracker --fps 10 || true
```

Expected: globe renders, ISS marker visible, stats panel shows real lat/lon/alt/vel, AGE counter increments and resets each poll. If the API errors, the AGE field should turn red and the marker should freeze rather than crash. After 15s, ctrl-c handling exits cleanly.

- [ ] **Step 3: Manual theme check**

```bash
timeout 5 .venv/bin/iss-tracker --demo --theme green || true
timeout 5 .venv/bin/iss-tracker --demo --theme red || true
timeout 5 .venv/bin/iss-tracker --demo --theme violet || true
```

Expected: land color changes per theme, trail color follows.

- [ ] **Step 4: Final commit if anything changed**

If any tweaks were needed during manual testing:

```bash
git add -A
git commit -m "fix: tweaks from end-to-end testing"
```

If nothing changed, skip this step.

- [ ] **Step 5: Tag v0.1.0**

```bash
git tag v0.1.0
git log --oneline
```

Expected: clean linear history, ending at `v0.1.0`.
