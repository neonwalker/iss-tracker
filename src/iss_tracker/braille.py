"""2x4-dot Braille canvas primitives.

Vendored from NetOrbit (MIT). Each terminal cell is U+2800 + 8-bit pattern,
where each bit corresponds to one of 2 columns x 4 rows of sub-pixels.
"""

from __future__ import annotations

# Bit at [row][col]
BRAILLE_BITS: tuple[tuple[int, int], ...] = (
    (0x01, 0x08),
    (0x02, 0x10),
    (0x04, 0x20),
    (0x40, 0x80),
)

VIRTUAL_DOT_WIDTH = 2
VIRTUAL_DOT_HEIGHT = 4

BRAILLE_BASE = 0x2800
BRAILLE_CHARS: tuple[str, ...] = tuple(chr(BRAILLE_BASE + p) for p in range(256))


class BrailleCanvas:
    """A grid of `width x height` terminal cells, each holding a Braille pattern."""

    __slots__ = ("width", "height", "virtual_width", "virtual_height",
                 "_patterns", "_intensities")

    def __init__(self, width: int, height: int) -> None:
        self.width = width
        self.height = height
        self.virtual_width = width * VIRTUAL_DOT_WIDTH
        self.virtual_height = height * VIRTUAL_DOT_HEIGHT
        n = width * height
        self._patterns = [0] * n
        self._intensities = [0.0] * n

    def plot(self, x: int, y: int, intensity: float = 1.0) -> None:
        """Plot a single sub-pixel at virtual coordinates (x, y)."""
        if not (0 <= x < self.virtual_width and 0 <= y < self.virtual_height):
            return
        char_x = x // VIRTUAL_DOT_WIDTH
        char_y = y // VIRTUAL_DOT_HEIGHT
        i = char_y * self.width + char_x
        self._patterns[i] |= BRAILLE_BITS[y % VIRTUAL_DOT_HEIGHT][x % VIRTUAL_DOT_WIDTH]
        if intensity > self._intensities[i]:
            self._intensities[i] = 1.0 if intensity > 1.0 else intensity

    def pattern_at_char(self, char_x: int, char_y: int) -> int:
        return self._patterns[char_y * self.width + char_x]

    def intensity_at_char(self, char_x: int, char_y: int) -> float:
        return self._intensities[char_y * self.width + char_x]

    def to_chars(self) -> list[list[str]]:
        rows: list[list[str]] = []
        for y in range(self.height):
            row = [BRAILLE_CHARS[self._patterns[y * self.width + x]]
                   for x in range(self.width)]
            rows.append(row)
        return rows


def virtual_line_points(start: tuple[int, int],
                        end: tuple[int, int]) -> list[tuple[int, int]]:
    """Bresenham-ish: dense points along the line from start to end in virtual coords."""
    sx, sy = start
    ex, ey = end
    dx = ex - sx
    dy = ey - sy
    steps = max(abs(dx), abs(dy), 1)
    points: list[tuple[int, int]] = []
    for i in range(steps + 1):
        t = i / steps
        x = round(sx + dx * t)
        y = round(sy + dy * t)
        pt = (x, y)
        if not points or points[-1] != pt:
            points.append(pt)
    return points
