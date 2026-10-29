# Case Study – Power BI Health Assessment

## Challenge
A fictional sales and budget Power BI solution was intentionally built with realistic modeling, DAX and report-density issues. The purpose was to validate whether the assessment product can identify, prioritize and verify meaningful improvements.

## Starting Point
**Power BI Health Score: 78/100 – Good**

The solution worked, but contained avoidable risks:
- bidirectional filter propagation
- many-to-many relationship without explicit design rationale
- missing dedicated Date dimension
- semantic-model snowflaking
- unsafe / unclear DAX patterns
- excessive visual density on the Executive page
- inconsistent naming / documentation

## Assessment
The solution was reviewed across eight weighted areas: Data Model Architecture, Relationships, DAX Quality, Power Query / Transformation, Performance, Dashboard UX & Visual Design, Business & KPI Alignment, and Maintainability & Governance.

Findings were classified by Severity, Business Impact, Implementation Effort and Priority.

## Optimization
The highest-value findings were remediated first. Relationship direction was simplified, the many-to-many pattern removed, a Date dimension introduced, DAX expressions standardized and visual density reduced from 16 to 9 visuals on the Executive page.

## Verified Result
The optimized PBIP project was re-run through the same analyzer and scoring process.

**Power BI Health Score: 98/100 – Excellent**

**Improvement: +20 points**

Only one deliberately retained governance/documentation item remained.

## Outcome
The case demonstrates the intended customer value of the service: **not just finding technical issues, but showing what matters first, how to improve it and whether the changes actually improved the solution.**

This case uses fictional demo data and contains no customer information.
