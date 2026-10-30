from __future__ import annotations

import json
import re
import shutil
import zipfile
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.datastructures import UploadFile

ROOT = Path(__file__).resolve().parents[1]
APP_DIR = ROOT / "app"
RUNTIME_DIR = ROOT / "local_runtime" / "orders"
RUNTIME_DIR.mkdir(parents=True, exist_ok=True)

import sys
sys.path.insert(0, str(ROOT / "engine"))
from run_delivery import run  # noqa: E402

app = FastAPI(title="Power BI Audit Center", docs_url=None, redoc_url=None)
app.mount("/static", StaticFiles(directory=str(APP_DIR / "static")), name="static")
templates = Jinja2Templates(directory=str(APP_DIR / "templates"))

PACKAGE_LABELS = {
    "basic": "Power BI Quick Audit — $80",
    "standard": "Power BI Health Audit — $150",
    "premium": "Complete Power BI Assessment — $250",
}


def sanitize_order_id(value: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9_-]+", "-", (value or "").strip()).strip("-")
    if len(cleaned) < 3:
        raise ValueError("Order ID must contain at least 3 letters/numbers.")
    return cleaned[:80]


def safe_extract_zip(zip_path: Path, destination: Path) -> None:
    destination = destination.resolve()
    with zipfile.ZipFile(zip_path) as archive:
        for member in archive.infolist():
            target = (destination / member.filename).resolve()
            if destination != target and destination not in target.parents:
                raise ValueError("ZIP contains an unsafe path and was rejected.")
        archive.extractall(destination)


def find_pbip_project(path: Path) -> Path:
    path = path.expanduser().resolve()
    if path.is_file() and path.suffix.lower() == ".pbip":
        return path
    if not path.exists():
        raise ValueError(f"Project path does not exist: {path}")
    pbips = sorted(path.rglob("*.pbip")) if path.is_dir() else []
    if len(pbips) == 1:
        return pbips[0]
    if len(pbips) > 1:
        raise ValueError("More than one .pbip file found. Please provide a ZIP/folder with one Power BI project.")
    if path.is_dir() and (list(path.rglob("*.tmdl")) or list(path.rglob("*.pbir"))):
        return path
    raise ValueError("No PBIP/PBIR/TMDL project was found.")


def order_paths(order_id: str) -> tuple[Path, Path, Path]:
    base = RUNTIME_DIR / sanitize_order_id(order_id)
    return base, base / "order.json", base / "delivery"


def load_json(path: Path, default=None):
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def order_view_context(order_id: str, message: str | None = None) -> dict:
    base, order_path, delivery = order_paths(order_id)
    order = load_json(order_path, {})
    result = load_json(delivery / "processed_assessment.json", {})
    manifest = load_json(delivery / "delivery_manifest.json", {})
    review_payload = load_json(delivery / "review_required.json", {"items": []}) or {"items": []}
    offer_path = delivery / "optimization_offer.md"
    offer = offer_path.read_text(encoding="utf-8") if offer_path.exists() else ""
    files = []
    if delivery.exists():
        for p in sorted(delivery.iterdir()):
            if p.is_file() and p.name not in {"processed_assessment.json", "review_required.json"}:
                files.append(p.name)
    return {
        "order": order,
        "result": result,
        "manifest": manifest,
        "review_items": review_payload.get("items", []),
        "offer": offer,
        "files": files,
        "message": message,
        "package_labels": PACKAGE_LABELS,
    }


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    recent = []
    for folder in sorted(RUNTIME_DIR.glob("*"), key=lambda p: p.stat().st_mtime, reverse=True)[:10]:
        order = load_json(folder / "order.json", {})
        if order:
            recent.append(order)
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"package_labels": PACKAGE_LABELS, "recent": recent},
    )


@app.post("/analyze")
async def analyze_order(request: Request):
    form = await request.form()
    try:
        order_id = sanitize_order_id(str(form.get("order_id", "")))
        package = str(form.get("package", "standard"))
        if package not in PACKAGE_LABELS:
            raise ValueError("Unknown package.")

        base, order_path, delivery = order_paths(order_id)
        if base.exists():
            shutil.rmtree(base)
        base.mkdir(parents=True, exist_ok=True)
        source_dir = base / "source"
        source_dir.mkdir()

        uploaded = form.get("project_zip")
        local_path = str(form.get("local_project_path", "")).strip()
        project_path: Path
        if isinstance(uploaded, UploadFile) and uploaded.filename:
            if not uploaded.filename.lower().endswith(".zip"):
                raise ValueError("Browser upload currently accepts a ZIP containing one PBIP project.")
            zip_path = base / "customer_project.zip"
            with zip_path.open("wb") as target:
                while chunk := await uploaded.read(1024 * 1024):
                    target.write(chunk)
            safe_extract_zip(zip_path, source_dir)
            zip_path.unlink(missing_ok=True)
            project_path = find_pbip_project(source_dir)
        elif local_path:
            project_path = find_pbip_project(Path(local_path))
        else:
            raise ValueError("Upload a PBIP ZIP or provide a local PBIP project path.")

        order = {
            "order_id": order_id,
            "package": package,
            "customer_name": str(form.get("customer_name", "Client")).strip() or "Client",
            "project_name": str(form.get("project_name", "Power BI Project")).strip() or "Power BI Project",
            "project_path": str(project_path),
            "business_goal": str(form.get("business_goal", "")).strip(),
            "primary_concern": str(form.get("primary_concern", "")).strip(),
            "known_problems": str(form.get("known_problems", "")).strip(),
            "scope_confirmed": True,
            "sensitive_data_confirmed": True,
            "auto_confirm_automatic": True,
            "confirmed_findings": [],
        }
        if len(order["business_goal"]) < 10:
            raise ValueError("Business goal is too short. Add one clear sentence about the report's purpose.")
        if len(order["primary_concern"]) < 3:
            raise ValueError("Add the customer's primary concern.")

        order_path.write_text(json.dumps(order, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        run(order_path, delivery, require_final=False)
        return RedirectResponse(f"/order/{order_id}", status_code=303)
    except Exception as exc:
        return templates.TemplateResponse(
            request=request,
            name="index.html",
            context={"package_labels": PACKAGE_LABELS, "recent": [], "error": str(exc)},
            status_code=400,
        )


@app.get("/order/{order_id}", response_class=HTMLResponse)
def view_order(request: Request, order_id: str, finalized: int = 0):
    context = order_view_context(order_id, "Final delivery generated." if finalized else None)
    return templates.TemplateResponse(request=request, name="order.html", context=context)


@app.post("/order/{order_id}/review")
async def save_review(request: Request, order_id: str):
    form = await request.form()
    base, order_path, delivery = order_paths(order_id)
    order = load_json(order_path)
    if not order:
        return RedirectResponse("/", status_code=303)
    review_payload = load_json(delivery / "review_required.json", {"items": []})
    decisions = {x["rule_id"]: x for x in order.get("confirmed_findings", [])}
    for item in review_payload.get("items", []):
        rid = item["rule_id"]
        decision = str(form.get(f"decision__{rid}", "")).strip()
        if decision not in {"confirmed", "rejected"}:
            continue
        decisions[rid] = {
            "rule_id": rid,
            "status": decision,
            "severity": str(form.get(f"severity__{rid}", item.get("default_severity", "medium"))),
            "impact": str(form.get(f"impact__{rid}", item.get("default_business_impact", "medium"))),
            "effort": str(form.get(f"effort__{rid}", item.get("default_effort", "medium"))),
            "notes": str(form.get(f"notes__{rid}", "")).strip(),
        }
    order["confirmed_findings"] = list(decisions.values())
    order_path.write_text(json.dumps(order, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    run(order_path, delivery, require_final=False)
    return RedirectResponse(f"/order/{order_id}", status_code=303)


@app.post("/order/{order_id}/finalize")
def finalize(order_id: str):
    _, order_path, delivery = order_paths(order_id)
    try:
        run(order_path, delivery, require_final=True)
        return RedirectResponse(f"/order/{order_id}?finalized=1", status_code=303)
    except SystemExit:
        return RedirectResponse(f"/order/{order_id}", status_code=303)


@app.get("/order/{order_id}/download/{filename}")
def download(order_id: str, filename: str):
    _, _, delivery = order_paths(order_id)
    safe_name = Path(filename).name
    path = (delivery / safe_name).resolve()
    if delivery.resolve() not in path.parents or not path.exists() or not path.is_file():
        return RedirectResponse(f"/order/{order_id}", status_code=303)
    return FileResponse(path, filename=safe_name)


@app.post("/order/{order_id}/delete")
def delete_order(order_id: str):
    base, _, _ = order_paths(order_id)
    if base.exists():
        shutil.rmtree(base)
    return RedirectResponse("/", status_code=303)
