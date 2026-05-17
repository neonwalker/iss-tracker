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
