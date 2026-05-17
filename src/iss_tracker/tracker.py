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
        if self._lat > 90.0:
            self._lat = 90.0
        elif self._lat < -90.0:
            self._lat = -90.0

    def view(self) -> tuple[float, float]:
        return self._lat, self._lon
