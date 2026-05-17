"""Fullscreen globe with stats overlaid in the top-right corner."""

from __future__ import annotations

import time
from dataclasses import dataclass

from rich.console import Console, ConsoleOptions, RenderResult
from rich.style import Style
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
    """Full-terminal renderable: globe canvas with stats stamped on top."""

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
            yield Text("Waiting for ISS data…", style=self._theme.panel_label)
            return
        canvas = render_globe(width=width, height=height,
                              view_lat=view_lat, view_lon=view_lon,
                              iss_lat=sample.lat, iss_lon=sample.lon,
                              trail=self._trail, theme=self._theme)
        _stamp_stats_overlay(canvas, self._state, self._theme)
        yield _canvas_to_text(canvas)


def _stamp_stats_overlay(canvas: list[list[StyledCell]],
                         state: AppState,
                         theme: Theme,
                         now: float | None = None) -> None:
    """Overwrite top-right corner cells with right-aligned stats lines."""
    if now is None:
        now = time.time()
    if not canvas or not canvas[0]:
        return

    label_style = theme.panel_label
    value_style = theme.panel_value

    sample = state.last_sample
    if sample is None:
        rows: list[tuple[str, str, Style]] = [
            ("LAT", "—", value_style),
            ("LON", "—", value_style),
            ("ALT", "—", value_style),
            ("VEL", "—", value_style),
        ]
    else:
        rows = [
            ("LAT", f"{sample.lat:+7.2f}°", value_style),
            ("LON", f"{sample.lon:+7.2f}°", value_style),
            ("ALT", f"{sample.altitude_km:6.1f} km", value_style),
            ("VEL", f"{int(sample.velocity_kmh):>5} km/h", value_style),
        ]

    if state.last_sample_at == 0.0:
        age_text, age_style = "—", value_style
    else:
        age = now - state.last_sample_at
        if age > 30:
            age_text, age_style = f"{int(age)}s stale", theme.panel_stale
        else:
            age_text, age_style = f"{int(age)}s", value_style
    rows.append(("AGE", age_text, age_style))

    if state.last_error:
        rows.append(("ERR", state.last_error[:14], theme.panel_stale))

    canvas_w = len(canvas[0])
    canvas_h = len(canvas)
    max_w = max(len(label) + 2 + len(value) for label, value, _ in rows)
    right_margin = 2
    top_margin = 1
    col_start = max(0, canvas_w - right_margin - max_w)

    for line_idx, (label, value, val_style) in enumerate(rows):
        row_idx = top_margin + line_idx
        if row_idx >= canvas_h:
            break
        gap = max_w - len(label) - len(value)
        col = col_start
        for ch in label:
            if col >= canvas_w:
                break
            canvas[row_idx][col] = StyledCell(ch, label_style)
            col += 1
        for _ in range(gap):
            if col >= canvas_w:
                break
            canvas[row_idx][col] = StyledCell(" ", label_style)
            col += 1
        for ch in value:
            if col >= canvas_w:
                break
            canvas[row_idx][col] = StyledCell(ch, val_style)
            col += 1


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
