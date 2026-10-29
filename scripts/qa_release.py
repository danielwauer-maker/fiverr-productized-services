#!/usr/bin/env python3
from pathlib import Path
import json, subprocess, sys

ROOT = Path(__file__).resolve().parents[1]
errors=[]
required=[
    "FIVERR_MASTER_STATE.md", "fiverr-current-state.json",
    "docs/FIVERR_PROFILE_COPY.md", "docs/FIVERR_HERO_GIG_COPY.md",
    "docs/FIVERR_VIDEO_SCRIPT.md", "docs/GIG_GRAPHICS_SYSTEM.md",
    "ops/ORDER_OPERATIONS_RUNBOOK.md", "ops/DELIVERY_TEMPLATES.md",
    "engine/assessment-engine-v1.json", "engine/analyzer_v1.py",
    "engine/process_order.py"
]
for rel in required:
    if not (ROOT/rel).exists(): errors.append(f"missing: {rel}")

state=json.loads((ROOT/"fiverr-current-state.json").read_text())
if state["report"]["before_score"] != 78 or state["report"]["after_score"] != 98:
    errors.append("demo score truth changed")

r=subprocess.run([sys.executable,"-m","unittest","discover","-s",str(ROOT/"tests"),"-v"],capture_output=True,text=True)
print(r.stdout); print(r.stderr)
if r.returncode: errors.append("unit tests failed")

if errors:
    print("QA FAIL")
    for e in errors: print("-",e)
    raise SystemExit(1)
print("QA PASS")
