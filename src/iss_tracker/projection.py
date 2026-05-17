"""Orthographic projection of a unit sphere onto the screen plane.

Conventions:
- World cartesian: (x, y, z) with x out of the prime meridian at the equator,
  z = north pole, y = 90E equator. (Right-handed.)
- Camera frame: after applying the view rotation, the visible hemisphere is the
  one with z' >= 0. Screen x is camera-x', screen y is camera-z'.
- The view rotation takes a target (view_lat, view_lon) to (0, 0, 1) in camera
  space, i.e. centers it on screen.
- Screen coords (sx, sy) are in [-1, 1] (disc radius = 1). sy is positive UP.
"""

from __future__ import annotations

import math


def geo_to_unit_sphere(lat: float, lon: float) -> tuple[float, float, float]:
    lat_r = math.radians(lat)
    lon_r = math.radians(lon)
    cos_lat = math.cos(lat_r)
    x = cos_lat * math.cos(lon_r)
    y = cos_lat * math.sin(lon_r)
    z = math.sin(lat_r)
    return x, y, z


def unit_sphere_to_geo(x: float, y: float, z: float) -> tuple[float, float]:
    # Clamp z to avoid NaN from float drift.
    z = max(-1.0, min(1.0, z))
    lat = math.degrees(math.asin(z))
    lon = math.degrees(math.atan2(y, x))
    return lat, lon


def _view_basis(view_lat: float, view_lon: float
                ) -> tuple[tuple[float, float, float],
                            tuple[float, float, float],
                            tuple[float, float, float]]:
    """Return the camera basis vectors (e_right, e_up, e_forward) in world space.

    Applying the matrix [e_right; e_up; e_forward] to a world point gives the
    camera-space coords (x', y', z'). The view target maps to (0, 0, 1).
    """
    lat_r = math.radians(view_lat)
    lon_r = math.radians(view_lon)
    cos_lat = math.cos(lat_r)
    sin_lat = math.sin(lat_r)
    cos_lon = math.cos(lon_r)
    sin_lon = math.sin(lon_r)
    # Forward (e_z'): the view target itself.
    e_forward = (cos_lat * cos_lon, cos_lat * sin_lon, sin_lat)
    # Up (e_y'): world north projected onto the plane perpendicular to forward.
    # Equivalent to rotating "north" by the same view rotation. Closed form:
    e_up = (-sin_lat * cos_lon, -sin_lat * sin_lon, cos_lat)
    # Right (e_x'): forward x up (right-handed). Closed form:
    e_right = (-sin_lon, cos_lon, 0.0)
    return e_right, e_up, e_forward


def project_to_screen(lat: float, lon: float,
                      view_lat: float, view_lon: float
                      ) -> tuple[float, float, bool]:
    """Return (sx, sy, visible). sx,sy in [-1,1] when visible."""
    p = geo_to_unit_sphere(lat, lon)
    e_right, e_up, e_forward = _view_basis(view_lat, view_lon)
    sx = p[0] * e_right[0] + p[1] * e_right[1] + p[2] * e_right[2]
    sy = p[0] * e_up[0] + p[1] * e_up[1] + p[2] * e_up[2]
    sz = p[0] * e_forward[0] + p[1] * e_forward[1] + p[2] * e_forward[2]
    return sx, sy, sz >= 0.0


def unproject_from_screen(sx: float, sy: float,
                          view_lat: float, view_lon: float
                          ) -> tuple[float, float] | None:
    """Inverse of project_to_screen. Returns None if (sx, sy) is off the disc."""
    r2 = sx * sx + sy * sy
    if r2 > 1.0:
        return None
    sz = math.sqrt(1.0 - r2)
    e_right, e_up, e_forward = _view_basis(view_lat, view_lon)
    # World point = sx*e_right + sy*e_up + sz*e_forward (basis is orthonormal,
    # so the transpose-multiply is the same as inverse-multiply).
    x = sx * e_right[0] + sy * e_up[0] + sz * e_forward[0]
    y = sx * e_right[1] + sy * e_up[1] + sz * e_forward[1]
    z = sx * e_right[2] + sy * e_up[2] + sz * e_forward[2]
    return unit_sphere_to_geo(x, y, z)
