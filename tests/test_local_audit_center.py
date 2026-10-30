import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.main import find_pbip_project, safe_extract_zip, sanitize_order_id


class LocalAuditCenterTests(unittest.TestCase):
    def test_order_id_is_sanitized(self):
        self.assertEqual(sanitize_order_id(" Fiverr #123 / Test "), "Fiverr-123-Test")

    def test_find_single_pbip_in_folder(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            project = root / "Customer" / "Customer.pbip"
            project.parent.mkdir()
            project.write_text("{}", encoding="utf-8")
            self.assertEqual(find_pbip_project(root), project.resolve())

    def test_safe_zip_rejects_path_traversal(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            archive = root / "bad.zip"
            with zipfile.ZipFile(archive, "w") as zf:
                zf.writestr("../escape.txt", "no")
            with self.assertRaises(ValueError):
                safe_extract_zip(archive, root / "out")


if __name__ == "__main__":
    unittest.main()
