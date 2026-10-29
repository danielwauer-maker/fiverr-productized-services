# Sprint 03 – Demo PBIP + Analyzer V1

**Status:** DONE (100%)  
**Date:** 2026-10-29

## Goal
Create a deterministic Power BI project fixture and an analyzer for public PBIP/PBIR/TMDL project files.

## Result
- Analyzer V1 extracts tables, columns, measures, relationships, report pages and visual counts.
- Static heuristics map evidence to assessment-rule IDs.
- Findings are emitted as **candidates**, not automatically as customer-facing confirmed issues.
- Reproducible demo baseline yields **78/100 – Good** after expert confirmation.
- PBIP/PBIR/TMDL is the preferred structured analysis format; PBIX can be converted to a local PBIP working copy when needed.

## Reproducibility
`scripts/build_demo_fixture.py` generates a compact test fixture for analyzer/CI validation.
