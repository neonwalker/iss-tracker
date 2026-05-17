from iss_tracker.braille import BRAILLE_BASE, BrailleCanvas


def test_empty_canvas_renders_spaces():
    canvas = BrailleCanvas(width=4, height=2)
    rows = canvas.to_chars()
    assert len(rows) == 2
    assert all(len(row) == 4 for row in rows)
    assert all(ch == "⠀" for row in rows for ch in row)


def test_plot_dot_sets_correct_bit():
    canvas = BrailleCanvas(width=2, height=1)
    canvas.plot(0, 0)  # top-left dot of cell (0,0)
    rows = canvas.to_chars()
    assert ord(rows[0][0]) == BRAILLE_BASE | 0x01


def test_plot_bottom_right_dot():
    canvas = BrailleCanvas(width=2, height=1)
    canvas.plot(1, 3)  # bottom-right dot of cell (0,0)
    rows = canvas.to_chars()
    assert ord(rows[0][0]) == BRAILLE_BASE | 0x80


def test_plot_outside_bounds_is_noop():
    canvas = BrailleCanvas(width=2, height=1)
    canvas.plot(-1, 0)
    canvas.plot(100, 0)
    canvas.plot(0, -1)
    canvas.plot(0, 100)
    rows = canvas.to_chars()
    assert all(ch == "⠀" for row in rows for ch in row)


def test_intensity_tracks_max():
    canvas = BrailleCanvas(width=2, height=1)
    canvas.plot(0, 0, intensity=0.3)
    canvas.plot(0, 0, intensity=0.9)
    canvas.plot(0, 0, intensity=0.5)
    assert canvas.intensity_at_char(0, 0) == 0.9


def test_virtual_dimensions():
    canvas = BrailleCanvas(width=10, height=5)
    assert canvas.virtual_width == 20
    assert canvas.virtual_height == 20
