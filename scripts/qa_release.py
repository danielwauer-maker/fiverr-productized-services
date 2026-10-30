#!/usr/bin/env python3
from pathlib import Path
import json, subprocess, sys

ROOT = Path(__file__).resolve().parents[1]
errors=[]
required=[
    "FIVERR_MASTER_STATE.md", "fiverr-current-state.json", "requirements.txt",
    "docs/FIVERR_PROFILE_COPY.md", "docs/FIVERR_HERO_GIG_COPY.md",
    "docs/FIVERR_VIDEO_SCRIPT.md", "docs/GIG_GRAPHICS_SYSTEM.md",
    "docs/AUTOMATED_DELIVERY_PIPELINE.md",
    "ops/ORDER_OPERATIONS_RUNBOOK.md", "ops/DELIVERY_TEMPLATES.md",
    "ops/order_intake.schema.json", "ops/order_intake.example.json",
    "engine/assessment-engine-v1.json", "engine/analyzer_v1.py",
    "engine/process_order.py", "engine/package_profiles.json",
    "engine/report_generator.py", "engine/run_delivery.py"
]
for rel in required:
    if not (ROOT/rel).exists(): errors.append(f"missing: {rel}")

state=json.loads((ROOT/"fiverr-current-state.json").read_text())
if state["report"]["before_score"] != 78 or state["report"]["after_score"] != 98:
    errors.append("demo score truth changed")
if state["hero_gig"]["packages"]["basic"]["price_usd"] != 80:
    errors.append("live Basic price truth is not $80")
if state["hero_gig"]["packages"]["standard"]["price_usd"] != 150:
    errors.append("live Standard price truth is not $150")
if state["hero_gig"]["packages"]["premium"]["price_usd"] != 250:
    errors.append("live Premium price truth is not $250")

r=subprocess.run([sys.executable,"-m","unittest","discover","-s",str(ROOT/"tests"),"-v"],capture_output=True,text=True)
print(r.stdout); print(r.stderr)
if r.returncode: errors.append("unit tests failed")

if errors:
    print("QA FAIL")
    for e in errors: print("-",e)
    raise SystemExit(1)
print("QA PASS")
