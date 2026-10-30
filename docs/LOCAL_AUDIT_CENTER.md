# Power BI Audit Center — Local Operator App

## Goal
Provide a simple local UI for Fiverr Power BI Health Assessment delivery. Customer files stay on the operator's computer. The app wraps the existing analyzer, expert-review guardrails and package-specific report generator.

## Windows start
Double-click `start_audit_center.bat`.

On first use the launcher creates `.venv`, installs `requirements.txt`, starts the app and opens:

`http://127.0.0.1:8000`

The server binds only to localhost (`127.0.0.1`). It is not exposed to the network.

## Customer project input
Preferred: save/export the customer PBIX as PBIP in Power BI Desktop, ZIP the complete PBIP project folder, then upload the ZIP in the app.

Alternative: enter a local path to a `.pbip` file or PBIP/PBIR/TMDL project folder.

PBIX is intentionally not parsed directly in V1. Convert it locally to PBIP first.

## Operator workflow
1. Create a new assessment and enter Fiverr Order ID, package, customer/project information, business goal, primary concern and known problems.
2. Upload one PBIP ZIP or provide one local PBIP project path.
3. Click **Analyze project**.
4. Review the Health Score, project metrics and confirmed automatic findings.
5. For each item under **Expert review**, choose Confirm or Reject. Adjust severity, business impact and effort only when customer context justifies it.
6. Click **Save decisions & rerun audit**.
7. When no review items remain, click **Generate final delivery**.
8. Download the final PDF and Fiverr delivery message.
9. Review `optimization_offer.md` before sending any custom Fiverr implementation offer.
10. Optionally delete the local order from the app after delivery/retention needs are satisfied.

## Local storage
Runtime data is stored under:

`local_runtime/orders/<ORDER-ID>/`

This directory is ignored by Git and must never be committed. It can contain customer project files and generated delivery artifacts.

## Safety guardrails
- ZIP extraction blocks path traversal.
- Only one PBIP project per uploaded ZIP is accepted.
- Automatic rules can be auto-confirmed according to the assessment engine policy.
- Hybrid/manual candidate findings remain in the operator review queue.
- Final delivery mode remains blocked while unresolved review findings exist.
- Customer data is never uploaded by the app; there are no cloud/API calls in the UI workflow.

## Package behavior
- Basic: Power BI Quick Audit — $80
- Standard: Power BI Health Audit — $150
- Premium: Complete Power BI Assessment — $250

Implementation is not included in the audit. The generated optimization offer is an internal draft and requires scope/price review before it is sent to the customer.
