# Order Operations Runbook V1

## Goal
Process every Power BI Health Assessment consistently, safely and with minimal buyer back-and-forth.

## 1. Pre-order / scope gate
1. Confirm selected package.
2. Confirm approximate pages, tables and measures.
3. Confirm the buyer's primary question and business goal.
4. Reject or custom-scope projects that exceed package limits.
5. Never request passwords, tenant secrets or authentication tokens.

## 2. Intake gate
Required before analysis:
- project file or agreed evidence set
- business/report goal
- primary concern
- known symptoms, if any
- scope confirmation
- confirmation that credentials/secrets/unnecessary personal data were removed

If any required item is missing, send the clarification template and do not start the technical review.

## 3. Working copy
- Preserve the customer's original file unchanged.
- For PBIX, create a local PBIP working copy when structured static analysis is needed.
- Store customer work in a per-order working directory; do not mix orders.

## 4. Automated analysis
Run Analyzer V1 against PBIP/PBIR/TMDL. Automated output is **candidate evidence**, not automatically a customer-facing finding.

## 5. Expert validation
For every candidate:
- confirm or reject it;
- adjust severity/impact/effort only when evidence supports the change;
- add a concise explanation of why it matters;
- identify exceptions where a pattern is intentional.

Manual review must cover categories that cannot be reliably inferred statically: Power Query behavior, KPI/business alignment, visual storytelling, accessibility, governance context and real performance timings when relevant.

## 6. Scoring
Only **confirmed** findings affect the 0–100 Health Score. Rejected candidates never reduce the score.

## 7. Report assembly
Standard report target: 8–12 pages.
Premium target: 12–18 pages with deeper optimization sequencing.

Customer-facing priorities:
1. overall Health Score
2. top risks
3. quick wins
4. remediation order
5. next steps

Do not overwhelm the buyer with the full internal rule library.

## 8. Quality gate before delivery
- Buyer/project name correct
- no demo/customer mix-up
- all scores reconcile
- findings have evidence and priority
- no candidate is presented as confirmed accidentally
- no credentials/secrets appear in screenshots or report
- report opens correctly
- scope and revision boundary restated in delivery note

## 9. Delivery
Deliver the PDF assessment plus a concise summary message. Implementation is not included unless it is explicitly part of a custom offer.

## 10. Revision handling
A revision covers factual corrections or clarification of the delivered assessment. A modified Power BI file is a new Re-Validation scope.

## 11. Post-delivery
Record:
- package
- actual minutes spent
- number of candidates / confirmed findings
- revision requested? yes/no
- buyer questions
- reusable automation opportunity
- review outcome when available

Use this data to optimize pricing and automation after real orders.
