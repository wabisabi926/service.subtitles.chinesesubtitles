"""
Zimuku captcha OCR solver.
Recognizes 5 digits from a Base64 encoded BMP image using template matching.
"""
import base64
import struct


class ZimukuSolver:
    """Performs OCR on a 100x27 24-bit BMP image containing 5 digits."""

    IMG_WIDTH, IMG_HEIGHT = 100, 27
    CHAR_WIDTH, NUM_CHARS = 20, 5
    PIXEL_DATA_OFFSET = 54

    SAMPLE_POINTS = [
        (10, 7), (7, 8), (12, 8), (10, 13),
        (7, 19), (12, 19), (10, 20), (6, 13), (14, 13)
    ]

    TEMPLATES = {
        '0': [1, 1, 1, 1, 1, 1, 1, 1, 0],
        '1': [0, 1, 0, 0, 0, 0, 1, 0, 0],
        '2': [1, 0, 1, 0, 1, 0, 1, 0, 0],
        '3': [1, 0, 1, 1, 0, 1, 1, 0, 0],
        '4': [0, 0, 1, 0, 0, 1, 0, 0, 0],
        '5': [1, 1, 0, 0, 0, 1, 1, 0, 0],
        '6': [1, 0, 1, 1, 1, 1, 1, 1, 0],
        '7': [1, 0, 1, 0, 0, 0, 0, 0, 0],
        '8': [1, 1, 1, 1, 1, 1, 1, 0, 0],
        '9': [1, 1, 1, 0, 1, 0, 1, 0, 0],
    }

    def __init__(self, b64_string: str):
        try:
            self._data = base64.b64decode(b64_string)
        except (ValueError, TypeError):
            raise ValueError("Invalid Base64 string")

        if len(self._data) < self.PIXEL_DATA_OFFSET or self._data[:2] != b'BM':
            raise ValueError("Invalid BMP data")

        w = struct.unpack_from('<i', self._data, 18)[0]
        h = struct.unpack_from('<i', self._data, 22)[0]
        if (w, h) != (self.IMG_WIDTH, self.IMG_HEIGHT):
            raise ValueError(f"Expected {self.IMG_WIDTH}x{self.IMG_HEIGHT}, got {w}x{h}")

        self._stride = (self.IMG_WIDTH * 3 + 3) & ~3

    def _is_foreground(self, x, y, threshold=70):
        bmp_y = self.IMG_HEIGHT - 1 - y
        offset = self.PIXEL_DATA_OFFSET + bmp_y * self._stride + x * 3
        b, g, r = self._data[offset], self._data[offset + 1], self._data[offset + 2]
        return (r + g + b) / 3 < threshold

    def _match_digit(self, features):
        best, min_diff = '?', float('inf')
        for digit, template in self.TEMPLATES.items():
            diff = sum(f != t for f, t in zip(features, template))
            if diff < min_diff:
                min_diff, best = diff, digit
            if min_diff == 0:
                break
        return best

    def recognize(self):
        result = []
        one_offset = 0

        for i in range(self.NUM_CHARS):
            char_x = i * self.CHAR_WIDTH
            features = [
                1 if self._is_foreground(char_x + px - one_offset, py) else 0
                for px, py in self.SAMPLE_POINTS
            ]

            digit = self._match_digit(features)

            # Adjust for narrow characters
            if digit == '1':
                one_offset += 1
            elif digit == '4':
                one_offset -= 1

            result.append(digit)

        return "".join(result)
