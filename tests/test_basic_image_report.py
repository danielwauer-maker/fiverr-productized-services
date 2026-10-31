import sys
import tempfile
import unittest
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "engine"))

from basic_image_report import generate_basic_report_images


class BasicImageReportTests(unittest.TestCase):
    def test_generates_five_basic_png_pages(self):
        result = {
            "order_id": "ORDER-BASIC-TEST",
            "package": "basic",
            "project_name": "Contoso Sales",
            "report_date": "October 2026",
            "analysis": {
                "summary": {"visuals": 9},
                "metadata": {
                    "tables": ["Fact Sales", "Dim Date", "Dim Customer", "Dim Product"],
                    "relationships": [],
                    "page_visual_counts": {"Overview": 9},
                },
            },
            "assessment": {
                "score": 84,
                "band": "Strong",
                "category_scores": {
                    "data_model_architecture": 18,
                    "relationships": 9,
                    "dax_quality": 12,
                    "power_query_transformation": 9,
                    "performance": 11,
                    "dashboard_ux_visual_design": 9,
                    "business_kpi_alignment": 8,
                    "maintainability_governance": 8,
                },
                "findings": [
                    {"title": "Complex DAX logic", "category": "dax_quality", "severity": "high", "impact": "high", "effort": "medium", "priority": "P1", "evidence": {"measure": "Sales Growth"}},
                    {"title": "Performance bottleneck", "category": "performance", "severity": "high", "impact": "high", "effort": "medium", "priority": "P1", "evidence": {"page": "Overview"}},
                    {"title": "Inconsistent report design", "category": "dashboard_ux_visual_design", "severity": "medium", "impact": "medium", "effort": "low", "priority": "P2", "evidence": {}},
                    {"title": "Documentation gap", "category": "maintainability_governance", "severity": "low", "impact": "medium", "effort": "low", "priority": "P3", "evidence": {}},
                ],
            },
        }
        with tempfile.TemporaryDirectory() as td:
            pages = generate_basic_report_images(result, Path(td))
            self.assertEqual(len(pages), 5)
            for page in pages:
                self.assertTrue(page.exists())
                with Image.open(page) as img:
                    self.assertEqual(img.size, (1240, 1754))
                    self.assertEqual(img.format, "PNG")


if __name__ == "__main__":
    unittest.main()
