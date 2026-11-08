"""Native CSD and MPV aspect mapping must not become color-comparison errors."""
import importlib.util
from pathlib import Path
import unittest
from PIL import Image

spec = importlib.util.spec_from_file_location('mpv_colors', Path(__file__).with_name('verify-mpv-colors.py'))
colors = importlib.util.module_from_spec(spec)
spec.loader.exec_module(colors)


class NativeSurfaceReference(unittest.TestCase):
    def test_wider_qt_target_retains_letterbox_when_native_client_clips(self):
        source = Image.new('RGB', (1920, 1080), 'red')
        actual = colors.reference_for_surface(source,
            dict(x=0, y=0, width=1922, height=1080), (1920, 1080), 1, 16 / 9)
        self.assertEqual(actual.getpixel((0, 540)), (0, 0, 0))
        self.assertEqual(actual.getpixel((1, 540)), (255, 0, 0))
        self.assertEqual(actual.getpixel((1919, 540)), (255, 0, 0))

    def test_native_sized_target_has_no_extra_letterbox(self):
        source = Image.new('RGB', (160, 90), 'red')
        actual = colors.reference_for_surface(source,
            dict(x=0, y=0, width=160, height=90), (160, 90), 1, 16 / 9)
        self.assertEqual(actual.tobytes(), source.tobytes())

    def test_surface_position_preserves_the_surrounding_client(self):
        source = Image.new('RGB', (160, 90), 'red')
        actual = colors.reference_for_surface(source,
            dict(x=10, y=20, width=160, height=90), (200, 140), 1, 16 / 9)
        self.assertEqual(actual.getpixel((9, 20)), (0, 0, 0))
        self.assertEqual(actual.getpixel((10, 20)), (255, 0, 0))
        self.assertEqual(actual.getpixel((170, 110)), (0, 0, 0))


if __name__ == '__main__':
    unittest.main()
