#!/usr/bin/env python3
"""Operational wrapper for a Power BI Health Assessment order.

Validates intake, runs Analyzer V1 and produces a conservative assessment.
Automatic rules may be confirmed automatically when enabled. Hybrid/manual
rules always remain in the expert review queue unless explicitly confirmed.
"""
from pathlib import Path
import argparse, json, sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from analyzer_v1 import analyze
from evaluate import evaluate

REQUIRED = [
    "order_id", "package", "project_path", "business_goal", "primary_concern",
    "scope_confirmed", "sensitive_data_confirmed"
]
PACKAGES = {"basic", "standard", "premium"}


def validate_order(order):
    missing = [k for k in REQUIRED if k not in order]
    if missing:
        raise ValueError(f"Missing required intake fields: {', '.join(missing)}")
    if order["package"] not in PACKAGES:
        raise ValueError("package must be basic, standard or premium")
    if order["scope_confirmed"] is not True:
        raise ValueError("scope_confirmed must be true")
    if order["sensitive_data_confirmed"] is not True:
        raise ValueError("sensitive_data_confirmed must be true")
    p = Path(order["project_path"])
    if not p.exists():
        raise ValueError(f"project_path does not exist: {p}")
    return p


def _explicit_decisions(order):
    return {f["rule_id"]: f for f in order.get("confirmed_findings", [])}


def _build_review(analysis, order):
    decisions = _explicit_decisions(order)
    confirmed = []
    review_queue = []
    rejected = []
    auto_confirm = order.get("auto_confirm_automatic", True)

    for candidate in analysis.get("candidate_findings", []):
        rule_id = candidate["rule_id"]
        decision = decisions.get(rule_id)
        if decision:
            status = decision.get("status")
            merged = {**candidate, **decision}
            if status == "confirmed":
                confirmed.append(merged)
            else:
                rejected.append(merged)
            continue

        if auto_confirm and candidate.get("detection_mode") == "automatic":
            confirmed.append({**candidate, "status": "confirmed", "confirmation_source": "automatic_rule"})
        else:
            review_queue.append({**candidate, "status": "review_required"})

    return confirmed, review_queue, rejected


def process(order):
    project_path = validate_order(order)
    analysis = analyze(project_path)
    confirmed, review_queue, rejected = _build_review(analysis, order)
    assessment = evaluate(confirmed)
    return {
        "order_id": order["order_id"],
        "package": order["package"],
        "customer_name": order.get("customer_name", "Client"),
        "project_name": order.get("project_name") or analysis["summary"].get("project", "Power BI Project"),
        "business_goal": order["business_goal"],
        "primary_concern": order["primary_concern"],
        "known_problems": order.get("known_problems", ""),
        "analysis": analysis,
        "assessment": assessment,
        "review": {
            "confirmed_count": len(confirmed),
            "review_required_count": len(review_queue),
            "rejected_count": len(rejected),
            "review_required": review_queue,
            "rejected": rejected
        },
        "guardrail": "Automatic rules may be auto-confirmed. Hybrid/manual findings require explicit expert confirmation before they affect the customer score."
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("order_json")
    ap.add_argument("-o", "--output", required=True)
    args = ap.parse_args()
    order_path = Path(args.order_json)
    order = json.loads(order_path.read_text(encoding="utf-8"))
    result = process(order)
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(out)

if __name__ == "__main__":
    main()
