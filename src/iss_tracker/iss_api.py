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
