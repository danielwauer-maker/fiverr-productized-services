# Automated Fiverr Delivery Pipeline V1

## Goal
Turn a manually downloaded customer PBIP/PBIR/TMDL project into a repeatable Power BI assessment delivery with minimal expert time.

## Operator workflow
1. Download the customer project from Fiverr and store it locally outside the repository.
2. Create an order JSON from `ops/order_intake.example.json`.
3. Run:
   `python engine/run_delivery.py orders/ORDER-001.json --out deliveries/ORDER-001`
4. If `review_required.json` exists, review only those candidate findings. Add each decision to `confirmed_findings` in the order JSON as `confirmed` or `rejected`.
5. Run again with:
   `python engine/run_delivery.py orders/ORDER-001.json --out deliveries/ORDER-001 --require-final`
6. Send the final PDF plus the generated `fiverr_delivery_message.txt` through Fiverr.
7. Review `optimization_offer.md`, adjust scope/price if needed, and send a Fiverr custom offer only when the customer wants implementation.

## Outputs
- `processed_assessment.json` – complete machine-readable result
- `review_required.json` – internal-only expert review queue
- `Power_BI_Health_Assessment_<ORDER>.pdf` – final customer report
- `DRAFT_Power_BI_Health_Assessment_<ORDER>.pdf` – draft when expert review remains
- `fiverr_delivery_message.txt` – ready-to-paste delivery message
- `optimization_offer.md` – internal custom-offer draft
- `delivery_manifest.json` – score, readiness and offer range

## Package behavior
### Basic – Power BI Quick Audit – $80
Focused diagnostic. Up to five prioritized confirmed findings. Short report. No implementation included.

### Standard – Power BI Health Audit – $150
Full Health Score, category overview, up to twelve prioritized confirmed findings, priority matrix/roadmap and 30-minute consultation.

### Premium – Complete Power BI Assessment – $250
Deep assessment with up to twenty prioritized confirmed findings, category overview, optimization blueprint, roadmap and 60-minute consultation.

## Safety / quality guardrail
Only findings from rules marked `automatic` may be auto-confirmed. Hybrid/manual candidates never affect the customer score unless Daniel explicitly confirms them. This rule must not be weakened to save delivery time.

## PBIX handling
Analyzer V1 works on PBIP/PBIR/TMDL static project files. For a PBIX order, create a local PBIP working copy in Power BI Desktop before running the pipeline. Do not upload customer files to GitHub.

## Commercial boundary
The assessment sells diagnosis, prioritization and next steps. Implementation is a separate custom Fiverr offer. The generated optimization offer is a draft and must be scope-checked before sending.

## Data handling
Customer files, extracted model metadata, order JSON files and generated reports are local delivery artifacts and must not be committed to this repository. Delete local customer data according to the agreed retention policy after delivery/revision windows are closed.
