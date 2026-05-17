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
