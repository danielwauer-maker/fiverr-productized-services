#!/usr/bin/env python3
"""Operational wrapper for a Power BI Health Assessment order.

Validates minimum intake, runs Analyzer V1, then evaluates only explicitly
confirmed findings supplied in the order JSON. It never auto-confirms
hybrid/manual findings.
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


def process(order):
    project_path = validate_order(order)
    analysis = analyze(project_path)
    confirmed = [f for f in order.get("confirmed_findings", []) if f.get("status") == "confirmed"]
    assessment = evaluate(confirmed)
    return {
        "order_id": order["order_id"],
        "package": order["package"],
        "business_goal": order["business_goal"],
        "primary_concern": order["primary_concern"],
        "analysis": analysis,
        "assessment": assessment,
        "guardrail": "Only explicitly confirmed findings affect the customer score."
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
