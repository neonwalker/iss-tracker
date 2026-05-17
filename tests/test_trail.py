from iss_tracker.trail import Trail, TrailPoint


def test_empty_trail():
    trail = Trail(capacity=3)
    assert list(trail) == []


def test_append_and_iterate_in_order():
    trail = Trail(capacity=5)
    trail.append(lat=1.0, lon=2.0, timestamp=100.0)
    trail.append(lat=3.0, lon=4.0, timestamp=101.0)
    points = list(trail)
    assert points == [
        TrailPoint(lat=1.0, lon=2.0, timestamp=100.0),
        TrailPoint(lat=3.0, lon=4.0, timestamp=101.0),
    ]


def test_capacity_evicts_oldest():
    trail = Trail(capacity=3)
    trail.append(0.0, 0.0, 100.0)
    trail.append(1.0, 1.0, 101.0)
    trail.append(2.0, 2.0, 102.0)
    trail.append(3.0, 3.0, 103.0)
    timestamps = [p.timestamp for p in trail]
    assert timestamps == [101.0, 102.0, 103.0]


def test_len_reflects_size():
    trail = Trail(capacity=3)
    assert len(trail) == 0
    trail.append(0.0, 0.0, 100.0)
    assert len(trail) == 1
    trail.append(0.0, 0.0, 101.0)
    trail.append(0.0, 0.0, 102.0)
    trail.append(0.0, 0.0, 103.0)
    assert len(trail) == 3  # capped


def test_latest_returns_most_recent():
    trail = Trail(capacity=3)
    assert trail.latest() is None
    trail.append(1.0, 2.0, 100.0)
    trail.append(3.0, 4.0, 200.0)
    assert trail.latest() == TrailPoint(3.0, 4.0, 200.0)
