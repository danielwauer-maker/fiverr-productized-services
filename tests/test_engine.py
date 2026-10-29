import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "engine"))
sys.path.insert(0, str(ROOT / "scripts"))
from analyzer_v1 import analyze
from evaluate import evaluate
from process_order import validate_order, process
from build_demo_fixture import build

class EngineTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.demo = build(Path(self.tmp.name) / "PowerBI_Audit_Demo", optimized=False)

    def tearDown(self):
        self.tmp.cleanup()

    def test_demo_analyzer_has_expected_shape(self):
        r = analyze(self.demo)
        self.assertGreater(r["summary"]["tables"], 0)
        self.assertGreater(r["summary"]["measures"], 0)
        self.assertGreater(len(r["candidate_findings"]), 0)
        self.assertIn("delivery_guardrail", r)

    def test_only_confirmed_findings_affect_score(self):
        r = evaluate([
            {"rule_id": "REL-001", "status": "candidate"},
            {"rule_id": "DAX-003", "status": "confirmed"}
        ])
        self.assertEqual(len(r["findings"]), 1)
        self.assertEqual(r["findings"][0]["rule_id"], "DAX-003")

    def test_standard_fixture_reproduces_demo_score(self):
        order = json.loads((ROOT / "ops" / "test_order_standard.json").read_text())
        order["project_path"] = str(self.demo)
        r = process(order)
        self.assertEqual(r["assessment"]["score"], 78)

    def test_missing_scope_confirmation_is_rejected(self):
        order = json.loads((ROOT / "ops" / "test_order_standard.json").read_text())
        order["project_path"] = str(self.demo)
        order["scope_confirmed"] = False
        with self.assertRaises(ValueError):
            validate_order(order)

if __name__ == "__main__":
    unittest.main()
