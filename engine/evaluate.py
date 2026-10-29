"""Reference evaluator for Fiverr Power BI Health Assessment Engine V1."""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ENGINE = json.loads((HERE / "assessment-engine-v1.json").read_text(encoding="utf-8"))
ALL_RULES=[]
for rule_file in sorted((HERE / "rules").glob("*.json")):
    ALL_RULES.extend(json.loads(rule_file.read_text(encoding="utf-8")))
RULES = {r["id"]: r for r in ALL_RULES}


def priority(severity: str, impact: str, effort: str) -> str:
    s = ENGINE["classification"]["numeric_maps"]["severity"][severity]
    i = ENGINE["classification"]["numeric_maps"]["business_impact"][impact]
    e_bonus = {"low": 2, "medium": 1, "high": 0}[effort]
    if severity == "critical": return "P1"
    score = s * 2 + i * 2 + e_bonus
    if score >= 10: return "P1"
    if score >= 7: return "P2"
    if score >= 5: return "P3"
    return "P4"


def evaluate(findings):
    cat = dict(ENGINE["score"]["category_weights"])
    enriched=[]
    for f in findings:
        if f.get("status", "confirmed") != "confirmed":
            continue
        r=RULES[f["rule_id"]]
        severity=f.get("severity",r["default_severity"])
        impact=f.get("impact",r["default_business_impact"])
        effort=f.get("effort",r["default_effort"])
        cat[r["category"]] = max(0, cat[r["category"]] - r["score_deduction"])
        enriched.append({**f,"title":r["title"],"category":r["category"],
                         "severity":severity,"impact":impact,"effort":effort,
                         "priority":priority(severity,impact,effort),
                         "score_deduction":r["score_deduction"]})
    total=sum(cat.values())
    band=next(b["label"] for b in ENGINE["score"]["bands"] if b["min"] <= total <= b["max"])
    return {"score":total,"band":band,"category_scores":cat,"findings":enriched}
