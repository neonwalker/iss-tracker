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
    # 5 bands from oldest (almost background) to most recent (bright). Indexed
    # by floor(intensity * len(bands)).
    trail_styles: tuple[Style, ...]
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
        trail_styles=(
            Style(color="grey23"),
            Style(color="grey42"),
            Style(color="grey58"),
            Style(color="cyan"),
            Style(color="bright_cyan", bold=True),
        ),
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
        trail_styles=(
            Style(color="grey23"),
            Style(color="grey42"),
            Style(color="grey58"),
            Style(color="green"),
            Style(color="bright_green", bold=True),
        ),
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
        trail_styles=(
            Style(color="grey23"),
            Style(color="grey42"),
            Style(color="grey58"),
            Style(color="red"),
            Style(color="bright_red", bold=True),
        ),
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
        trail_styles=(
            Style(color="grey23"),
            Style(color="grey42"),
            Style(color="grey58"),
            Style(color="magenta"),
            Style(color="bright_magenta", bold=True),
        ),
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
