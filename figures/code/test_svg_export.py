"""Regression coverage for editable, non-destructive figure export."""
from pathlib import Path
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "common"))
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


class SvgExportTests(unittest.TestCase):
    def exporter(self):
        import importlib.util
        self.assertIsNotNone(importlib.util.find_spec("plot_export"),
                             "The shared PNG/SVG exporter is not implemented")
        from plot_export import save_figure_variants
        return save_figure_variants

    def test_exports_png_and_editable_svg_without_changing_rcparams(self):
        save = self.exporter()
        with tempfile.TemporaryDirectory() as folder:
            fig, ax = plt.subplots()
            self.addCleanup(plt.close, fig)
            ax.plot([0, 1], [1, 0])
            ax.set_title("Editable title")
            before = matplotlib.rcParams["svg.fonttype"]
            path = Path(folder) / "sample.png"
            save(fig, path, dpi=80, facecolor="white")
            self.assertTrue(path.read_bytes().startswith(b"\x89PNG\r\n\x1a\n"))
            root = ET.parse(path.with_suffix(".svg")).getroot()
            texts = [node.text for node in root.iter("{http://www.w3.org/2000/svg}text")]
            self.assertIn("Editable title", texts)
            self.assertEqual(matplotlib.rcParams["svg.fonttype"], before)

    def test_existing_png_is_never_overwritten(self):
        save = self.exporter()
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "sample.png"
            path.write_bytes(b"original PNG sentinel")
            fig = plt.figure()
            self.addCleanup(plt.close, fig)
            with self.assertRaises(FileExistsError):
                save(fig, path)
            self.assertEqual(path.read_bytes(), b"original PNG sentinel")
            self.assertFalse(path.with_suffix(".svg").exists())

    def test_existing_svg_prevents_partial_png_export(self):
        save = self.exporter()
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "sample.png"
            svg = path.with_suffix(".svg")
            svg.write_bytes(b"original SVG sentinel")
            fig = plt.figure()
            self.addCleanup(plt.close, fig)
            with self.assertRaises(FileExistsError):
                save(fig, path)
            self.assertEqual(svg.read_bytes(), b"original SVG sentinel")
            self.assertFalse(path.exists())

    def test_svg_failure_does_not_leave_a_partial_png(self):
        save = self.exporter()
        with tempfile.TemporaryDirectory() as folder:
            fig, ax = plt.subplots()
            self.addCleanup(plt.close, fig)
            ax.set_title("SVG failure")
            real_savefig = fig.savefig

            def fail_svg(target, *args, **kwargs):
                if kwargs.get("format") == "svg":
                    raise RuntimeError("synthetic SVG serialization failure")
                return real_savefig(target, *args, **kwargs)

            fig.savefig = fail_svg
            path = Path(folder) / "partial.png"
            with self.assertRaisesRegex(RuntimeError, "synthetic SVG serialization failure"):
                save(fig, path, dpi=80)
            self.assertFalse(path.exists())
            self.assertFalse(path.with_suffix(".svg").exists())

    def test_svg_metadata_reports_editable_output(self):
        from plot_export import svg_metadata

        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "figure.svg"
            path.write_text('<svg xmlns="http://www.w3.org/2000/svg"><text>editable</text></svg>', encoding="utf-8")
            metadata = svg_metadata(path)
            self.assertEqual(metadata["svg"], str(path))
            self.assertEqual(metadata["svg_sha256"], __import__("hashlib").sha256(path.read_bytes()).hexdigest())
            self.assertTrue(metadata["svg_text_editable"])

    def test_standalone_q1_plotters_record_svg_metadata(self):
        root = Path(__file__).resolve().parents[2]
        for name in ("fig_q1_quality.py", "fig_q1_support.py"):
            source = (root / "code" / "figures" / name).read_text(encoding="utf-8")
            self.assertIn("svg_metadata", source, name)


if __name__ == "__main__":
    unittest.main()
