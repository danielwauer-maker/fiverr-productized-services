import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "app"))

import main as audit_app


class DeliveryZipTests(unittest.TestCase):
    def test_build_delivery_zip_uses_order_id_and_contains_all_delivery_files(self):
        original_runtime = audit_app.RUNTIME_DIR
        try:
            with tempfile.TemporaryDirectory() as td:
                audit_app.RUNTIME_DIR = Path(td)
                order_id = "TEST-BASIC-001"
                delivery = audit_app.RUNTIME_DIR / order_id / "delivery"
                delivery.mkdir(parents=True)
                (delivery / "01_basic_cover.png").write_bytes(b"png")
                (delivery / "delivery_manifest.json").write_text("{}", encoding="utf-8")
                (delivery / "optimization_offer.md").write_text("offer", encoding="utf-8")

                zip_path = audit_app.build_delivery_zip(order_id)
                self.assertEqual(zip_path.name, f"{order_id}.zip")
                self.assertTrue(zip_path.exists())
                with zipfile.ZipFile(zip_path) as archive:
                    self.assertEqual(
                        sorted(archive.namelist()),
                        ["01_basic_cover.png", "delivery_manifest.json", "optimization_offer.md"],
                    )
        finally:
            audit_app.RUNTIME_DIR = original_runtime


if __name__ == "__main__":
    unittest.main()
