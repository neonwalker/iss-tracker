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
    PERIOD_SECONDS = 60.0  # synthetic: full orbit per minute so rotation is visible
    ALTITUDE_KM = 420.0
    VELOCITY_KMH = 27600.0

    def __init__(self, t0: float | None = None) -> None:
        self._t0 = t0 if t0 is not None else time.time()

    async def fetch(self) -> IssSample:
        now = time.time()
        t = now - self._t0
        anomaly = 2.0 * math.pi * (t % self.PERIOD_SECONDS) / self.PERIOD_SECONDS
        incl = math.radians(self.INCLINATION_DEG)
        x = math.cos(anomaly)
        y = math.sin(anomaly) * math.cos(incl)
        z = math.sin(anomaly) * math.sin(incl)
        lat = math.degrees(math.asin(z))
        lon = math.degrees(math.atan2(y, x))
        lon -= (t / self.PERIOD_SECONDS) * 22.5
        lon = ((lon + 180.0) % 360.0) - 180.0
        return IssSample(
            lat=lat, lon=lon,
            altitude_km=self.ALTITUDE_KM,
            velocity_kmh=self.VELOCITY_KMH,
            timestamp=int(now),
        )
