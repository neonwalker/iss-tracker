import math

import pytest

from iss_tracker.projection import (
    geo_to_unit_sphere,
    unit_sphere_to_geo,
    project_to_screen,
    unproject_from_screen,
)


def assert_close(a: float, b: float, tol: float = 1e-6) -> None:
    assert abs(a - b) < tol, f"{a} != {b} (tol {tol})"


# --- Sphere <-> geo conversion ---

def test_geo_origin_maps_to_x_axis():
    x, y, z = geo_to_unit_sphere(0.0, 0.0)
    assert_close(x, 1.0)
    assert_close(y, 0.0)
    assert_close(z, 0.0)


def test_geo_north_pole_maps_to_z_axis():
    x, y, z = geo_to_unit_sphere(90.0, 0.0)
    assert_close(x, 0.0)
    assert_close(y, 0.0)
    assert_close(z, 1.0)


def test_geo_to_sphere_unit_length():
    for lat, lon in [(45, 30), (-60, 170), (12.5, -34.7), (-89, -180)]:
        x, y, z = geo_to_unit_sphere(lat, lon)
        assert_close(x * x + y * y + z * z, 1.0)


def test_sphere_to_geo_roundtrip():
    for lat, lon in [(45, 30), (-60, 170), (12.5, -34.7), (0, 0)]:
        x, y, z = geo_to_unit_sphere(lat, lon)
        lat2, lon2 = unit_sphere_to_geo(x, y, z)
        assert_close(lat, lat2, tol=1e-6)
        # lon at the poles is ambiguous, but we're not testing poles here
        assert_close(lon, lon2, tol=1e-6)


# --- Forward projection ---

def test_view_target_projects_to_screen_center():
    # Viewing (10, 20), the point (10, 20) should land at screen (0, 0) and be visible.
    sx, sy, visible = project_to_screen(lat=10.0, lon=20.0,
                                        view_lat=10.0, view_lon=20.0)
    assert visible is True
    assert_close(sx, 0.0, tol=1e-6)
    assert_close(sy, 0.0, tol=1e-6)


def test_antipode_is_hidden():
    # Viewing (0, 0), the antipode (0, 180) is on the far side.
    _, _, visible = project_to_screen(lat=0.0, lon=180.0,
                                      view_lat=0.0, view_lon=0.0)
    assert visible is False


def test_quarter_turn_lon_projects_to_unit_x():
    # Viewing (0, 0), the point (0, 90) is on the right limb.
    sx, sy, visible = project_to_screen(lat=0.0, lon=90.0,
                                        view_lat=0.0, view_lon=0.0)
    assert visible is True
    assert_close(sx, 1.0, tol=1e-6)
    assert_close(sy, 0.0, tol=1e-6)


def test_north_pole_projects_above_center():
    # Viewing equator, the north pole sits at the top (positive y in our convention).
    sx, sy, visible = project_to_screen(lat=90.0, lon=0.0,
                                        view_lat=0.0, view_lon=0.0)
    assert visible is True
    assert_close(sx, 0.0, tol=1e-6)
    assert_close(sy, 1.0, tol=1e-6)


# --- Inverse projection ---

def test_screen_center_unprojects_to_view_target():
    lat, lon = unproject_from_screen(sx=0.0, sy=0.0,
                                     view_lat=42.0, view_lon=-17.0)
    assert_close(lat, 42.0, tol=1e-6)
    assert_close(lon, -17.0, tol=1e-6)


def test_unproject_off_disc_returns_none():
    result = unproject_from_screen(sx=0.9, sy=0.9,
                                   view_lat=0.0, view_lon=0.0)
    assert result is None  # 0.9^2 + 0.9^2 > 1


def test_forward_inverse_roundtrip():
    # Pick a visible point and round-trip it.
    view_lat, view_lon = 30.0, -45.0
    for lat, lon in [(35, -40), (10, -50), (20, -30)]:
        sx, sy, visible = project_to_screen(lat, lon, view_lat, view_lon)
        assert visible
        result = unproject_from_screen(sx, sy, view_lat, view_lon)
        assert result is not None
        lat2, lon2 = result
        assert_close(lat, lat2, tol=1e-6)
        assert_close(lon, lon2, tol=1e-6)
