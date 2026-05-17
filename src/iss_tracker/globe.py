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

    vw = width * VIRTUAL_DOT_WIDTH
    vh = height * VIRTUAL_DOT_HEIGHT

    radius = min(vw, vh) / 2.0
    cx = vw / 2.0
    cy = vh / 2.0

    # Pass 1: land disc via per-cell inverse projection.
    land_patterns = [0] * (width * height)
    for py in range(vh):
        sy = (cy - py - 0.5) / radius
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

    # Pass 1.5: graticule (lat/lon lines). Sample every 30° and walk densely
    # along each line, projecting to screen. Skip sub-pixels that fall on a
    # land bit — the graticule never draws *over* land. Cells that contain
    # any land are also left alone at finalize so the lines break at coasts.
    grid_patterns = [0] * (width * height)

    def _plot_grid(vx: int, vy: int) -> None:
        if not (0 <= vx < vw and 0 <= vy < vh):
            return
        ci = (vy // VIRTUAL_DOT_HEIGHT) * width + (vx // VIRTUAL_DOT_WIDTH)
        bit = BRAILLE_BITS[vy % VIRTUAL_DOT_HEIGHT][vx % VIRTUAL_DOT_WIDTH]
        if land_patterns[ci] & bit:
            return
        grid_patterns[ci] |= bit

    sample_step = 0.5  # degrees along each line; oversampled for smooth curves
    # Latitude rings at -60, -30, 0, 30, 60.
    for lat_deg in (-60.0, -30.0, 0.0, 30.0, 60.0):
        lon = -180.0
        while lon < 180.0:
            sx, sy, vis = project_to_screen(lat_deg, lon, view_lat, view_lon)
            if vis:
                _plot_grid(int(cx + sx * radius), int(cy - sy * radius))
            lon += sample_step
    # Longitude meridians every 30°.
    for lon_deg_i in range(-180, 180, 30):
        lon_deg = float(lon_deg_i)
        lat = -89.0
        while lat <= 89.0:
            sx, sy, vis = project_to_screen(lat, lon_deg, view_lat, view_lon)
            if vis:
                _plot_grid(int(cx + sx * radius), int(cy - sy * radius))
            lat += sample_step

    # A fully-saturated cell (0xFF) is interior land; any partial pattern
    # straddles land + ocean → coastline. Cells with no land bits but grid
    # bits render as graticule.
    for cy_idx in range(height):
        for cx_idx in range(width):
            i = cy_idx * width + cx_idx
            land_pat = land_patterns[i]
            if land_pat:
                style = theme.land if land_pat == 0xFF else theme.coast
                canvas[cy_idx][cx_idx] = StyledCell(BRAILLE_CHARS[land_pat], style)
                continue
            grid_pat = grid_patterns[i]
            if grid_pat:
                canvas[cy_idx][cx_idx] = StyledCell(BRAILLE_CHARS[grid_pat], theme.grid)

    # Pass 2: trail (forward-project each stored point).
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

    # Pass 3: ISS marker (overrides trail).
    sx, sy, visible = project_to_screen(iss_lat, iss_lon, view_lat, view_lon)
    if visible:
        px = int(cx + sx * radius)
        py = int(cy - sy * radius)
        if 0 <= px < vw and 0 <= py < vh:
            char_x = px // VIRTUAL_DOT_WIDTH
            char_y = py // VIRTUAL_DOT_HEIGHT
            canvas[char_y][char_x] = StyledCell("●", theme.iss_marker)

    return canvas
