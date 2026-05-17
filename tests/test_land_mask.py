from iss_tracker.land_mask import is_land


def test_london_is_land():
    assert is_land(51.5, -0.1) is True


def test_sydney_is_land():
    # Sydney region, adjusted to lon 150.0 to hit landmass at 1:110m resolution
    assert is_land(-33.87, 150.0) is True


def test_mid_pacific_is_ocean():
    assert is_land(0.0, -150.0) is False


def test_mid_atlantic_is_ocean():
    assert is_land(0.0, -30.0) is False


def test_antarctica_is_land():
    assert is_land(-85.0, 0.0) is True


def test_longitude_wraps():
    # 181 should behave like -179
    assert is_land(0.0, 181.0) == is_land(0.0, -179.0)


def test_latitude_clamps_at_poles():
    # Above 90 / below -90 should not raise
    assert is_land(95.0, 0.0) == is_land(90.0, 0.0)
    assert is_land(-95.0, 0.0) == is_land(-90.0, 0.0)
