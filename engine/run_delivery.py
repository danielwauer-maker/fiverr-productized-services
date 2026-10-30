#!/usr/bin/env python3
"""One-command local delivery pipeline for Fiverr Power BI assessment orders.

Usage:
  python engine/run_delivery.py orders/ORDER-001.json --out deliveries/ORDER-001

Outputs:
- processed_assessment.json
- review_required.json (only when expert review remains)
- package-specific PDF report (DRAFT_ prefix until review is cleared)
- Fiverr delivery message
- optimization offer draft
- delivery manifest
"""
from pathlib import Path
import argparse, json, sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from process_order import process
from report_generator import generate_deliverables


def run(order_path: Path, out_dir: Path, require_final: bool = False):
    order = json.loads(order_path.read_text(encoding="utf-8"))
    result = process(order)
    out_dir.mkdir(parents=True, exist_ok=True)

    processed = out_dir / "processed_assessment.json"
    processed.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    review_items = result.get("review", {}).get("review_required", [])
    review_path = out_dir / "review_required.json"
    if review_items:
        review_payload = {
            "order_id": result["order_id"],
            "instructions": "Review each item. Add a matching entry to confirmed_findings in the order JSON with status confirmed or rejected, then rerun the pipeline.",
            "items": review_items,
        }
        review_path.write_text(json.dumps(review_payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    elif review_path.exists():
        review_path.unlink()

    manifest = generate_deliverables(result, out_dir)
    if require_final and not manifest["final_ready"]:
        raise SystemExit(f"Final delivery blocked: {manifest['review_required']} finding(s) still require expert review. See {review_path}")

    print(json.dumps(manifest, indent=2, ensure_ascii=False))
    return manifest


def main():
    ap = argparse.ArgumentParser(description="Run complete Fiverr Power BI assessment delivery pipeline")
    ap.add_argument("order_json", type=Path)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--require-final", action="store_true", help="Fail instead of producing a draft when review items remain")
    args = ap.parse_args()
    run(args.order_json, args.out, args.require_final)


if __name__ == "__main__":
    main()
