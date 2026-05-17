import httpx
import pytest
import respx

from iss_tracker.iss_api import IssApi, IssSample


SAMPLE_JSON = {
    "name": "iss",
    "id": 25544,
    "latitude": -34.21,
    "longitude": 151.07,
    "altitude": 421.6,
    "velocity": 27620.0,
    "visibility": "daylight",
    "footprint": 4530.0,
    "timestamp": 1715900000,
    "daynum": 2460443.0,
    "solar_lat": 19.0,
    "solar_lon": 100.0,
    "units": "kilometers",
}


@respx.mock
@pytest.mark.asyncio
async def test_fetch_parses_response():
    respx.get("https://api.wheretheiss.at/v1/satellites/25544").mock(
        return_value=httpx.Response(200, json=SAMPLE_JSON)
    )
    api = IssApi()
    sample = await api.fetch()
    assert isinstance(sample, IssSample)
    assert sample.lat == -34.21
    assert sample.lon == 151.07
    assert sample.altitude_km == 421.6
    assert sample.velocity_kmh == 27620.0
    assert sample.timestamp == 1715900000


@respx.mock
@pytest.mark.asyncio
async def test_fetch_retries_on_server_error_then_succeeds():
    route = respx.get("https://api.wheretheiss.at/v1/satellites/25544")
    route.side_effect = [
        httpx.Response(503),
        httpx.Response(503),
        httpx.Response(200, json=SAMPLE_JSON),
    ]
    api = IssApi(retry_backoff_seconds=(0.0, 0.0, 0.0))
    sample = await api.fetch()
    assert sample.lat == -34.21
    assert route.call_count == 3


@respx.mock
@pytest.mark.asyncio
async def test_fetch_raises_after_exhausted_retries():
    respx.get("https://api.wheretheiss.at/v1/satellites/25544").mock(
        return_value=httpx.Response(500)
    )
    api = IssApi(retry_backoff_seconds=(0.0, 0.0))
    with pytest.raises(httpx.HTTPStatusError):
        await api.fetch()
