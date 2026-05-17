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
