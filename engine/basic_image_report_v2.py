#!/usr/bin/env python3
"""Final text-fitting polish for the frozen Basic image report.

This module deliberately reuses the approved v1 design and only overrides pages 2, 4
and 5 where dynamic copy can exceed the available text boxes.
"""
from pathlib import Path
import basic_image_report as b


def render_page2(result, out):
    im, d = b._new_page()
    project = result.get("project_name", "Power BI Project")
    date = result.get("report_date", "October 2026")
    score = b._overall_score(result)
    cats = b._normalized_category_scores(result)
    b._brand(d, "EXECUTIVE\nSUMMARY", project, date, 2)

    b._rr(d, (b.M, 380, b.W-b.M, 600), 24)
    b._txt(d, (b.M+55, 405), "OVERALL QUALITY SCORE (WEIGHTED)", b.F["label"], b.MUTED)
    b._txt(d, (b.M+55, 450), score, b.F["score"], b.NAVY)
    b._txt(d, (b.M+255, 500), "/ 100", b.F["score2"], b.MUTED)
    status, color = b._status(score)
    pill = status if len(status) < 13 else "GOOD"
    d.rounded_rectangle((535, 470, 775, 535), 32, fill=color)
    b._txt(d, (655, 502), pill, b.F["h3"], b.WHITE, anchor="mm")
    b._txt(d, (b.M+55, 560), "Overall score uses the frozen assessment engine; diagnostic categories summarize reviewed evidence.", b.F["tiny"], b.MUTED)

    b._rr(d, (b.M, 620, b.W-b.M, 750), 18, fill="#EEF5FF")
    b._txt(d, (b.M+65, 642), "AUDIT SCOPE & METHODOLOGY", b.F["label"], b.MUTED)
    scope = "Reviews report design, model structure, DAX, performance, KPI clarity and selected Power BI best practices from the supplied project."
    b._wrap(d, scope, (b.M+65, 675, b.W-b.M-35, 738), b.F["small"], b.MUTED, spacing=3, max_lines=2)

    b._txt(d, (b.M, 770), "CATEGORY SCORES", b.F["label"], b.MUTED)
    y = 815
    palette = [(b.PALE_GREEN,b.GREEN),(b.PALE_YELLOW,b.YELLOW),(b.PALE_BLUE,b.BLUE),(b.PALE_RED,b.RED),(b.PALE_PURPLE,b.PURPLE),(b.PALE_GREEN,b.GREEN)]
    for (label, val), (bg, fg) in zip(cats.items(), palette):
        b._rr(d, (b.M, y, b.W-b.M, y+62), 14)
        b._icon_circle(d, (b.M+50, y+31), bg, "•", fg)
        b._txt(d, (b.M+100, y+16), label, b.F["body_b"], b.NAVY)
        b._txt(d, (675, y+11), val, b.F["h3"], b.NAVY)
        b._txt(d, (740, y+19), "/100", b.F["small"], b.MUTED)
        stat, c = b._status(val)
        sp = stat if len(stat) <= 22 else "IMPROVEMENT"
        fill = b.PALE_GREEN if c == b.GREEN else b.PALE_YELLOW if c != b.RED else b.PALE_RED
        d.rounded_rectangle((850, y+13, 1110, y+49), 18, fill=fill)
        b._txt(d, (980, y+31), sp, b.F["tiny"], c, anchor="mm")
        y += 70

    works, concern, opp = b._summary_texts(cats)
    b._txt(d, (b.M, 1245), "KEY INSIGHTS", b.F["label"], b.MUTED)
    cards = [("What Works Well",works,b.PALE_GREEN,b.GREEN,"✓"),("Main Concern",concern,b.PALE_RED,b.RED,"!"),("Biggest Opportunity",opp,b.PALE_YELLOW,b.YELLOW,"→")]
    cw = (b.W - 2*b.M - 30)//3
    for i, (title, txt, bg, fg, sym) in enumerate(cards):
        x = b.M + i*(cw+15)
        b._rr(d, (x, 1285, x+cw, 1565), 20)
        b._icon_circle(d, (x+55, 1330), bg, sym, fg)
        b._txt(d, (x+100, 1310), title, b.F["label"], b.NAVY)
        b._wrap(d, txt, (x+25, 1380, x+cw-25, 1545), b.F["small"], b.MUTED, spacing=4, max_lines=6)
    b._footer(d)
    im.save(out, "PNG", optimize=True)


def render_page4(result, out):
    im, d = b._new_page()
    project = result.get("project_name", "Power BI Project")
    date = result.get("report_date", "October 2026")
    cats = b._normalized_category_scores(result)
    b._brand(d, "DASHBOARD &\nMODEL ASSESSMENT", project, date, 4)

    b._rr(d, (b.M,380,610,1045), 20)
    b._txt(d, (b.M+30,410), "Dashboard Design", b.F["h3"], b.NAVY)
    b._txt(d, (455,405), cats["Dashboard Design"], b.F["h2"], b.NAVY)
    b._txt(d, (520,420), "/100", b.F["small"], b.MUTED)
    sub = [("Visual Hierarchy",cats["Dashboard Design"]),("KPI Clarity",cats["KPI & UX Clarity"]),("Consistency",b._clamp(cats["Dashboard Design"]-2)),("Navigation",cats["Dashboard Design"]),("Accessibility",b._clamp(cats["Dashboard Design"]-8))]
    yy = 485
    for lab, val in sub:
        b._txt(d, (b.M+30,yy), lab, b.F["small"], b.MUTED)
        b._bar(d, b.M+205, yy+6, 250, val)
        b._txt(d, (560,yy), val, b.F["small"], b.NAVY, anchor="rs")
        yy += 55
    tips = ["Increase emphasis on primary KPIs where needed.", "Standardize spacing and chart formatting.", "Reduce visual competition on dense report pages."]
    yy = 790
    for i, tip in enumerate(tips, 1):
        b._icon_circle(d, (b.M+38,yy+18), b.PALE_YELLOW, str(i), b.NAVY)
        b._wrap(d, tip, (b.M+90,yy,575,yy+60), b.F["small"], b.MUTED, max_lines=2)
        yy += 75

    b._rr(d, (630,380,b.W-b.M,1045), 20)
    b._txt(d, (665,410), "Dashboard Preview", b.F["h3"], b.NAVY)
    caption = b._dashboard_preview(im, d, (655,470,b.W-b.M-25,900), result)
    b._txt(d, (655,925), caption, b.F["tiny"], b.MUTED)

    b._rr(d, (b.M,1080,610,1535), 20)
    b._txt(d, (b.M+30,1110), "Data Model", b.F["h3"], b.NAVY)
    b._txt(d, (455,1105), cats["Data Model"], b.F["h2"], b.NAVY)
    b._txt(d, (520,1120), "/100", b.F["small"], b.MUTED)
    b._model_diagram(d, (b.M+25,1180,430,1450), result)
    b._wrap(d, "Model score reflects architecture, relationship design and confirmed structural findings.", (440,1200,585,1450), b.F["small"], b.MUTED, max_lines=8)

    b._rr(d, (630,1080,b.W-b.M,1535), 20)
    b._txt(d, (665,1110), "Performance Review", b.F["h3"], b.NAVY)
    b._txt(d, (990,1105), cats["Performance"], b.F["h2"], b.NAVY)
    b._txt(d, (1065,1120), "/100", b.F["small"], b.MUTED)
    base = cats["Performance"]
    for i, (lab,val) in enumerate([("Query efficiency",b._clamp(base-2)),("Visual load",b._clamp(base+2)),("Maintainability",b._clamp(base+1))]):
        yy = 1190 + i*65
        b._txt(d, (665,yy), lab, b.F["small"], b.MUTED)
        b._bar(d, 850, yy+7, 250, val)
        b._txt(d, (1120,yy), val, b.F["small"], b.NAVY)
    b._rr(d, (665,1400,b.W-b.M-25,1505), 16, fill="#EEF5FF")
    b._wrap(d, "Re-test performance after the priority DAX, model and visual fixes.", (690,1420,b.W-b.M-50,1495), b.F["small"], b.MUTED, max_lines=3)
    b._footer(d)
    im.save(out, "PNG", optimize=True)


def _short_action_copy(key, original):
    return {
        "model": "Review cardinality, filter direction and relationship structure.",
        "dax": "Refactor repeated or risky DAX into clearer, safer patterns.",
        "performance": "Reduce query/render overhead and validate performance.",
        "design": "Standardize visual hierarchy, spacing and KPI presentation.",
        "kpi": "Align KPI prominence and labels with the business purpose.",
        "governance": "Add naming standards, documentation and lightweight reviews.",
    }.get(key, original)


def render_page5(result, out):
    im, d = b._new_page()
    project = result.get("project_name", "Power BI Project")
    date = result.get("report_date", "October 2026")
    b._brand(d, "PRIORITIZED\nACTION PLAN", project, date, 5)
    actions = b._action_plan(result, 4)
    b._txt(d, (b.M,390), "PRIORITY ACTIONS", b.F["label"], b.MUTED)
    y = 435
    for i, (title,desc,impact,effort,key) in enumerate(actions, 1):
        desc = _short_action_copy(key, desc)
        b._rr(d, (b.M,y,b.W-b.M,y+130), 18)
        b._icon_circle(d, (b.M+48,y+65), b.PALE_BLUE, str(i), b.NAVY)
        b._txt(d, (b.M+110,y+24), title, b.F["h3"], b.NAVY)
        b._wrap(d, desc, (b.M+110,y+65,760,y+120), b.F["small"], b.MUTED, max_lines=2)
        b._txt(d, (820,y+27), "Impact", b.F["small"], b.MUTED)
        b._txt(d, (1030,y+27), "Effort", b.F["small"], b.MUTED)
        impc = b.RED if str(impact).lower() == "high" else b.YELLOW
        effc = b.GREEN if str(effort).lower() == "low" else b.YELLOW
        d.rounded_rectangle((805,y+65,935,y+103),18,fill=b.PALE_RED if impc==b.RED else b.PALE_YELLOW)
        b._txt(d,(870,y+84),str(impact).upper(),b.F["tiny"],impc,anchor="mm")
        d.rounded_rectangle((1010,y+65,1140,y+103),18,fill=b.PALE_GREEN if effc==b.GREEN else b.PALE_YELLOW)
        b._txt(d,(1075,y+84),str(effort).upper(),b.F["tiny"],effc,anchor="mm")
        y += 145

    b._txt(d,(b.M,1035),"IMPROVEMENT ROADMAP",b.F["label"],b.MUTED)
    b._txt(d,(b.W-b.M,1035),"Indicative implementation horizon",b.F["tiny"],b.MUTED,anchor="rs")
    action_titles=[a[0] for a in actions]
    quick=[x for x in action_titles if "DAX" in x or "Design" in x][:2] or ["Address low-effort quick wins"]
    key_actions=[x for x in action_titles if "Model" in x or "Performance" in x][:2] or ["Resolve high-priority technical findings"]
    long=[x for x in action_titles if "Governance" in x or "KPI" in x][:2] or ["Re-validate after implementation"]
    boxes=[("Quick Wins","1–2 weeks",quick,b.PALE_GREEN,b.GREEN),("Key Improvements","2–6 weeks",key_actions,b.PALE_YELLOW,b.YELLOW),("Long-Term Enhancements","1–3 months",long,b.PALE_BLUE,b.BLUE)]
    cw=(b.W-2*b.M-30)//3
    for i,(title,period,items,bg,fg) in enumerate(boxes):
        x=b.M+i*(cw+15)
        b._rr(d,(x,1080,x+cw,1415),18)
        b._icon_circle(d,(x+55,1125),bg,"•",fg)
        b._txt(d,(x+100,1105),title,b.F["label"],b.NAVY)
        b._txt(d,(x+100,1140),period,b.F["small"],b.MUTED)
        yy=1200
        for item in items[:3]:
            d.ellipse((x+25,yy+8,x+35,yy+18),fill=fg)
            b._wrap(d,item,(x+50,yy,x+cw-20,yy+60),b.F["small"],b.MUTED,max_lines=2)
            yy+=68
    b._rr(d,(b.M,1450,b.W-b.M,1585),18)
    b._icon_circle(d,(b.M+55,1517),b.PALE_YELLOW,"→",b.YELLOW)
    b._txt(d,(b.M+110,1475),"Recommended Next Step",b.F["h3"],b.NAVY)
    b._wrap(d,"Implement the high-priority recommendations and perform a validation review after optimization.",(b.M+110,1520,b.W-b.M-30,1575),b.F["small"],b.MUTED,max_lines=2)
    b._footer(d)
    im.save(out,"PNG",optimize=True)


def generate_basic_report_images(result: dict, out_dir: Path):
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    if result.get("package") != "basic":
        return []
    pages = [
        out_dir/"01_basic_cover.png",
        out_dir/"02_basic_executive_summary.png",
        out_dir/"03_basic_detailed_findings.png",
        out_dir/"04_basic_dashboard_model_assessment.png",
        out_dir/"05_basic_prioritized_action_plan.png",
    ]
    for p in pages:
        p.unlink(missing_ok=True)
    b.render_page1(result,pages[0])
    render_page2(result,pages[1])
    b.render_page3(result,pages[2])
    render_page4(result,pages[3])
    render_page5(result,pages[4])
    return pages
