"""Orthographic globe renderer. Returns a 2D grid of styled cells."""

from __future__ import annotations

import time
from dataclasses import dataclass

from rich.style import Style

from .braille import (
    BRAILLE_BITS,
    BRAILLE_CHARS,
    VIRTUAL_DOT_HEIGHT,
    VIRTUAL_DOT_WIDTH,
    BrailleCanvas,
    virtual_line_points,
)
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

    for cy_idx in range(height):
        for cx_idx in range(width):
            pattern = land_patterns[cy_idx * width + cx_idx]
            if pattern:
                canvas[cy_idx][cx_idx] = StyledCell(BRAILLE_CHARS[pattern], theme.land)

    # Pass 2: trail as connected line segments at sub-pixel resolution. Each
    # segment between consecutive trail points is rasterized into a Braille
    # overlay with intensity = recency (older = dimmer). The overlay is then
    # composited onto the main canvas with a 5-band style gradient.
    points = list(trail)
    if len(points) >= 2:
        trail_canvas = BrailleCanvas(width, height)
        for i in range(len(points) - 1):
            p0, p1 = points[i], points[i + 1]
            sx0, sy0, vis0 = project_to_screen(p0.lat, p0.lon, view_lat, view_lon)
            sx1, sy1, vis1 = project_to_screen(p1.lat, p1.lon, view_lat, view_lon)
            if not (vis0 and vis1):
                continue
            px0 = int(cx + sx0 * radius)
            py0 = int(cy - sy0 * radius)
            px1 = int(cx + sx1 * radius)
            py1 = int(cy - sy1 * radius)
            seg_age = max(0.0, now - (p0.timestamp + p1.timestamp) / 2.0)
            recency = max(0.0, 1.0 - seg_age / TRAIL_AGE_FOR_FULL_FADE)
            if recency <= 0.0:
                continue
            for vx, vy in virtual_line_points((px0, py0), (px1, py1)):
                trail_canvas.plot(vx, vy, intensity=recency)

        bands = theme.trail_styles
        nbands = len(bands)
        for cy_idx in range(height):
            for cx_idx in range(width):
                pattern = trail_canvas.pattern_at_char(cx_idx, cy_idx)
                if not pattern:
                    continue
                intensity = trail_canvas.intensity_at_char(cx_idx, cy_idx)
                band_idx = int(intensity * nbands)
                if band_idx >= nbands:
                    band_idx = nbands - 1
                canvas[cy_idx][cx_idx] = StyledCell(
                    BRAILLE_CHARS[pattern], bands[band_idx]
                )

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
