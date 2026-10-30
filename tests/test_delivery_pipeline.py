import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "engine"))

from process_order import _build_review
from report_generator import build_optimization_offer, generate_deliverables


class DeliveryPipelineTests(unittest.TestCase):
    def test_review_guardrail_auto_confirms_only_automatic(self):
        analysis = {
            "candidate_findings": [
                {"rule_id": "AUTO-1", "detection_mode": "automatic", "status": "candidate"},
                {"rule_id": "HYB-1", "detection_mode": "hybrid", "status": "candidate"},
            ]
        }
        confirmed, review, rejected = _build_review(analysis, {"auto_confirm_automatic": True})
        self.assertEqual([x["rule_id"] for x in confirmed], ["AUTO-1"])
        self.assertEqual([x["rule_id"] for x in review], ["HYB-1"])
        self.assertEqual(rejected, [])

    def test_explicit_rejection_overrides_candidate(self):
        analysis = {"candidate_findings": [{"rule_id": "DMA-003", "detection_mode": "hybrid", "status": "candidate"}]}
        confirmed, review, rejected = _build_review(analysis, {"confirmed_findings": [{"rule_id": "DMA-003", "status": "rejected"}]})
        self.assertEqual(confirmed, [])
        self.assertEqual(review, [])
        self.assertEqual(len(rejected), 1)

    def test_manual_confirmation_is_preserved_without_static_candidate(self):
        analysis = {"candidate_findings": []}
        confirmed, review, rejected = _build_review(
            analysis,
            {"confirmed_findings": [{"rule_id": "DMA-001", "status": "confirmed", "notes": "Expert validated model role mixing."}]},
        )
        self.assertEqual([x["rule_id"] for x in confirmed], ["DMA-001"])
        self.assertEqual(review, [])
        self.assertEqual(rejected, [])

    def test_generate_standard_deliverables(self):
        result = {
            "order_id": "ORDER-TEST-001",
            "package": "standard",
            "customer_name": "Test Client",
            "project_name": "Sales Reporting",
            "business_goal": "Improve reliable executive reporting and maintainability.",
            "primary_concern": "Model quality and performance",
            "assessment": {
                "score": 82,
                "band": "Good",
                "category_scores": {
                    "data_model_architecture": 18,
                    "relationships": 8,
                    "dax_quality": 13,
                    "power_query_transformation": 10,
                    "performance": 13,
                    "dashboard_ux_visual_design": 10,
                    "business_kpi_alignment": 10,
                    "maintainability_governance": 0
                },
                "findings": [
                    {"rule_id": "REL-001", "title": "Bidirectional relationship used without clear need", "category": "relationships", "severity": "high", "impact": "high", "effort": "medium", "priority": "P1", "score_deduction": 2}
                ]
            },
            "review": {"review_required_count": 0, "review_required": [], "rejected_count": 0, "rejected": []}
        }
        with tempfile.TemporaryDirectory() as td:
            manifest = generate_deliverables(result, Path(td))
            self.assertTrue(manifest["final_ready"])
            self.assertTrue((Path(td) / manifest["customer_report"]).exists())
            self.assertTrue((Path(td) / "fiverr_delivery_message.txt").exists())
            self.assertTrue((Path(td) / "optimization_offer.md").exists())
            offer = build_optimization_offer(result)
            self.assertGreaterEqual(offer["suggested_price_low_usd"], 250)
            self.assertGreater(offer["suggested_price_high_usd"], offer["suggested_price_low_usd"])


if __name__ == "__main__":
    unittest.main()
