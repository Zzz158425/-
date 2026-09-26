"""Test backfill safeguards and the technical route's drawn text bounds."""
import importlib.util
from pathlib import Path
import tempfile
import unittest
import xml.etree.ElementTree as ET


class SvgDeliveryTests(unittest.TestCase):
    def copier(self):
        self.assertIsNotNone(importlib.util.find_spec("backfill_svg"))
        from backfill_svg import copy_verified_companion
        return copy_verified_companion

    def test_matching_replay_adds_svg_without_modifying_png(self):
        copy = self.copier()
        with tempfile.TemporaryDirectory() as folder:
            original, replay = Path(folder) / "original.png", Path(folder) / "replay.png"
            original.write_bytes(b"same frozen plot")
            replay.write_bytes(b"same frozen plot")
            svg = b'<svg xmlns="http://www.w3.org/2000/svg"><text>editable</text></svg>'
            replay.with_suffix(".svg").write_bytes(svg)
            copy(original, replay)
            self.assertEqual(original.read_bytes(), b"same frozen plot")
            self.assertEqual(original.with_suffix(".svg").read_bytes(), svg)

    def test_different_replay_is_rejected_before_copy(self):
        copy = self.copier()
        with tempfile.TemporaryDirectory() as folder:
            original, replay = Path(folder) / "original.png", Path(folder) / "replay.png"
            original.write_bytes(b"old layout")
            replay.write_bytes(b"different layout")
            with self.assertRaises(ValueError):
                copy(original, replay)
            self.assertFalse(original.with_suffix(".svg").exists())
            self.assertEqual(original.read_bytes(), b"old layout")

    def test_existing_svg_is_rejected(self):
        copy = self.copier()
        with tempfile.TemporaryDirectory() as folder:
            original, replay = Path(folder) / "original.png", Path(folder) / "replay.png"
            original.write_bytes(b"same plot")
            replay.write_bytes(b"same plot")
            original.with_suffix(".svg").write_bytes(b"teammate edits")
            replay.with_suffix(".svg").write_bytes(b'<svg xmlns="http://www.w3.org/2000/svg"><text>x</text></svg>')
            with self.assertRaises(FileExistsError):
                copy(original, replay)
            self.assertEqual(original.with_suffix(".svg").read_bytes(), b"teammate edits")

    def test_route_has_nonoverlapping_text_and_editable_vector_export(self):
        self.assertIsNotNone(importlib.util.find_spec("overall_technical_route"))
        from overall_technical_route import build_figure
        from plot_export import save_figure_variants
        import matplotlib.pyplot as plt
        from matplotlib.text import Text
        fig = build_figure()
        self.addCleanup(plt.close, fig)
        fig.canvas.draw()
        renderer = fig.canvas.get_renderer()
        items = [(text, text.get_window_extent(renderer)) for text in fig.findobj(Text)
                 if text.get_visible() and text.get_text().strip()]
        self.assertGreater(len(items), 15)
        for i, (text, box) in enumerate(items):
            self.assertTrue(fig.bbox.contains(box.x0, box.y0), text.get_text())
            self.assertTrue(fig.bbox.contains(box.x1, box.y1), text.get_text())
            for other, other_box in items[i + 1:]:
                self.assertFalse(box.overlaps(other_box), (text.get_text(), other.get_text()))
        with tempfile.TemporaryDirectory() as folder:
            svg = save_figure_variants(fig, Path(folder) / "route.png", dpi=80)
            root = ET.parse(svg).getroot()
            self.assertGreater(len(list(root.iter("{http://www.w3.org/2000/svg}text"))), 15)
            self.assertEqual(len(list(root.iter("{http://www.w3.org/2000/svg}image"))), 0)


if __name__ == "__main__":
    unittest.main()
