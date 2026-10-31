import sys
import tempfile
import unittest
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "engine"))

from basic_image_report import (
    _action_plan,
    _normalized_category_scores,
    _overall_score,
    generate_basic_report_images,
)


def sample_result(score=77):
    return {
        "order_id": "ORDER-BASIC-TEST",
        "package": "basic",
        "project_name": "Contoso Sales",
        "report_date": "October 2026",
        "analysis": {
            "summary": {"visuals": 14},
            "metadata": {
                "tables": ["Fact Sales", "Dim Date", "Dim Customer", "Dim Product"],
                "relationships": [
                    {"fromColumn": "'Fact Sales'.CustomerID", "toColumn": "'Dim Customer'.CustomerID"}
                ],
                "page_visual_counts": {"Overview": 14},
            },
        },
        "assessment": {
            "score": score,
            "band": "Good",
            "category_scores": {
                "data_model_architecture": 17,
                "relationships": 4,
                "dax_quality": 6,
                "power_query_transformation": 10,
                "performance": 12,
                "dashboard_ux_visual_design": 10,
                "business_kpi_alignment": 10,
                "maintainability_governance": 8,
            },
            "findings": [
                {"rule_id": "REL-001", "title": "Bi-directional relationship without a clear modeling requirement", "category": "relationships", "severity": "high", "impact": "high", "effort": "low", "priority": "P1", "evidence": {"relationship": {}}},
                {"rule_id": "REL-002", "title": "Many-to-many relationship without explicit bridge/design rationale", "category": "relationships", "severity": "high", "impact": "high", "effort": "medium", "priority": "P1", "evidence": {"relationship": {}}},
                {"rule_id": "DAX-007", "title": "Complex iterator over a high-cardinality table", "category": "dax_quality", "severity": "high", "impact": "high", "effort": "medium", "priority": "P1", "evidence": {"measure": "Sales LY"}},
                {"rule_id": "DAX-008", "title": "Deeply nested IF/SWITCH logic with duplicated branches", "category": "dax_quality", "severity": "medium", "impact": "medium", "effort": "medium", "priority": "P2", "evidence": {"measure": "Sales Growth"}},
                {"rule_id": "PERF-001", "title": "Report page contains excessive number of query-generating visuals", "category": "performance", "severity": "high", "impact": "high", "effort": "medium", "priority": "P1", "evidence": {"page": "Overview"}},
                {"rule_id": "DMA-003", "title": "No dedicated date dimension where time intelligence is material", "category": "data_model_architecture", "severity": "high", "impact": "high", "effort": "low", "priority": "P1", "evidence": {}},
                {"rule_id": "GOV-003", "title": "Business-critical measures lack descriptions or documentation", "category": "maintainability_governance", "severity": "medium", "impact": "medium", "effort": "low", "priority": "P1", "evidence": {}},
            ],
        },
    }


class BasicImageReportTests(unittest.TestCase):
    def test_uses_current_assessment_score(self):
        result = sample_result(77)
        self.assertEqual(_overall_score(result), 77)
        result["assessment"]["score"] = 64
        self.assertEqual(_overall_score(result), 64)

    def test_category_scores_are_bounded_and_reflect_cross_impact(self):
        scores = _normalized_category_scores(sample_result())
        self.assertTrue(all(0 <= v <= 100 for v in scores.values()))
        self.assertLess(scores["Data Model"], 100)
        self.assertLess(scores["Dashboard Design"], 100)
        self.assertLess(scores["Best Practices"], 100)
        self.assertLess(scores["Performance"], 100)

    def test_action_plan_deduplicates_categories(self):
        actions = _action_plan(sample_result(), 4)
        keys = [a[4] for a in actions]
        self.assertEqual(len(keys), len(set(keys)))
        self.assertEqual(keys.count("dax"), 1)
        self.assertEqual(keys.count("model"), 1)

    def test_generates_five_basic_png_pages(self):
        result = sample_result()
        with tempfile.TemporaryDirectory() as td:
            pages = generate_basic_report_images(result, Path(td))
            self.assertEqual(len(pages), 5)
            for page in pages:
                self.assertTrue(page.exists())
                with Image.open(page) as img:
                    self.assertEqual(img.size, (1240, 1754))
                    self.assertEqual(img.format, "PNG")

    def test_rerun_overwrites_existing_pngs(self):
        result = sample_result(94)
        with tempfile.TemporaryDirectory() as td:
            pages = generate_basic_report_images(result, Path(td))
            first_sizes = [p.stat().st_size for p in pages]
            result["assessment"]["score"] = 77
            pages2 = generate_basic_report_images(result, Path(td))
            self.assertEqual([p.name for p in pages], [p.name for p in pages2])
            self.assertTrue(all(p.exists() for p in pages2))
            # At least one score-bearing image should change after a rerun.
            second_sizes = [p.stat().st_size for p in pages2]
            self.assertNotEqual(first_sizes[:2], second_sizes[:2])


if __name__ == "__main__":
    unittest.main()
