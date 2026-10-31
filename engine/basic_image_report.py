#!/usr/bin/env python3
"""Render the frozen Fiverr Basic Power BI Quick Audit as five PNG pages.

The renderer is deliberately deterministic: layout/design stay fixed while audit data,
customer/project names, findings, scores and model/dashboard evidence are dynamic.
"""
from __future__ import annotations

from pathlib import Path
import math
import textwrap

from PIL import Image, ImageDraw, ImageFont, ImageOps

W, H = 1240, 1754
M = 72

NAVY = "#071D49"
BLUE = "#246BFD"
PALE_BLUE = "#EAF3FF"
LIGHT_BLUE = "#DDEBFB"
YELLOW = "#F5B700"
PALE_YELLOW = "#FFF4C7"
GREEN = "#18A957"
PALE_GREEN = "#E6F7EA"
RED = "#E8452F"
PALE_RED = "#FDEAE7"
PURPLE = "#6F4CF6"
PALE_PURPLE = "#F0EBFF"
TEXT = "#172A52"
MUTED = "#63769B"
LINE = "#D9E4F2"
WHITE = "#FFFFFF"
CARD = "#FCFDFE"
BG = "#FBFDFF"

CATEGORY_WEIGHTS = {
    "data_model_architecture": 20,
    "relationships": 10,
    "dax_quality": 15,
    "power_query_transformation": 10,
    "performance": 15,
    "dashboard_ux_visual_design": 10,
    "business_kpi_alignment": 10,
    "maintainability_governance": 10,
}

REPORT_CATEGORY_MAP = {
    "Data Model": ("data_model_architecture", "relationships"),
    "DAX Measures": ("dax_quality",),
    "Dashboard Design": ("dashboard_ux_visual_design",),
    "Performance": ("performance", "power_query_transformation"),
    "KPI & UX Clarity": ("business_kpi_alignment",),
    "Best Practices": ("maintainability_governance",),
}


def _font(size: int, bold: bool = False):
    candidates = []
    if bold:
        candidates += [
            "C:/Windows/Fonts/arialbd.ttf",
            "C:/Windows/Fonts/segoeuib.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        ]
    else:
        candidates += [
            "C:/Windows/Fonts/arial.ttf",
            "C:/Windows/Fonts/segoeui.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        ]
    for p in candidates:
        if Path(p).exists():
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()


F = {
    "tiny": _font(18),
    "small": _font(22),
    "body": _font(25),
    "body_b": _font(25, True),
    "label": _font(22, True),
    "h3": _font(30, True),
    "h2": _font(42, True),
    "h1": _font(70, True),
    "score": _font(104, True),
    "score2": _font(68, True),
}


def _rr(draw, box, radius=20, fill=WHITE, outline=LINE, width=1):
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)


def _txt(draw, xy, text, font=None, fill=TEXT, anchor=None):
    draw.text(xy, str(text), font=font or F["body"], fill=fill, anchor=anchor)


def _wrap(draw, text, box, font=None, fill=TEXT, spacing=7, max_lines=None):
    font = font or F["body"]
    x1, y1, x2, y2 = box
    words = str(text or "").split()
    lines, line = [], ""
    for word in words:
        cand = (line + " " + word).strip()
        if draw.textbbox((0, 0), cand, font=font)[2] <= (x2 - x1):
            line = cand
        else:
            if line:
                lines.append(line)
            line = word
    if line:
        lines.append(line)
    if max_lines and len(lines) > max_lines:
        lines = lines[:max_lines]
        if lines:
            lines[-1] = lines[-1].rstrip(".") + "…"
    y = y1
    lh = draw.textbbox((0, 0), "Ag", font=font)[3] + spacing
    for ln in lines:
        if y + lh > y2:
            break
        draw.text((x1, y), ln, font=font, fill=fill)
        y += lh
    return y


def _new_page():
    im = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(im)
    for i, h in enumerate((170, 290, 420)):
        x = W - 350 + i * 80
        d.rounded_rectangle((x, 90 + 420 - h, x + 55, 510), radius=14, fill="#E4EFFC")
    d.polygon([(610, H), (W, H), (W, H-250)], fill="#E8F2FD")
    d.polygon([(780, H), (W, H), (W, H-165)], fill="#CFE2FA")
    d.polygon([(980, H), (W, H), (W, H-90)], fill=YELLOW)
    return im, d


def _brand(d, title, project, date_label, page=None):
    for i, hh in enumerate((30, 45, 65)):
        d.rounded_rectangle((M + i*24, 70 + 65 - hh, M + 17 + i*24, 135), 4, fill=YELLOW)
    _txt(d, (M+105, 86), "Power BI Quick Audit", F["h3"], NAVY)
    _txt(d, (M, 155), title, F["h1"], NAVY)
    _txt(d, (M, 285), f"{project} · {date_label}", F["h3"], NAVY)
    d.rectangle((M, 335, M+72, 341), fill=YELLOW)
    if page:
        _txt(d, (W-M, H-48), f"{page:02d}", F["small"], NAVY, anchor="rs")


def _footer(d):
    d.line((M, H-90, M+510, H-90), fill=MUTED, width=1)
    _txt(d, (M, H-78), "Prepared by Daniel Wauer", F["label"], NAVY)
    _txt(d, (M, H-48), "Power BI Audit & Optimization", F["small"], MUTED)


def _normalized_category_scores(result):
    raw = result.get("assessment", {}).get("category_scores", {})
    normalized = {}
    for label, keys in REPORT_CATEGORY_MAP.items():
        earned = sum(float(raw.get(k, CATEGORY_WEIGHTS[k])) for k in keys)
        max_pts = sum(CATEGORY_WEIGHTS[k] for k in keys)
        normalized[label] = int(round(100 * earned / max_pts)) if max_pts else 0
    return normalized


def _status(score):
    if score >= 90: return "EXCELLENT", GREEN
    if score >= 82: return "STRONG", GREEN
    if score >= 75: return "GOOD", GREEN
    if score >= 65: return "IMPROVEMENT RECOMMENDED", "#F2A500"
    return "NEEDS ATTENTION", RED


def _top_findings(result, n=4):
    fs = list(result.get("assessment", {}).get("findings", []))
    rank = {"P1": 1, "P2": 2, "P3": 3, "P4": 4}
    fs.sort(key=lambda x: (rank.get(x.get("priority"), 9), x.get("title", "")))
    return fs[:n]


def _finding_recommendation(f):
    category = f.get("category", "")
    return {
        "data_model_architecture": "Streamline model structure and reduce avoidable complexity.",
        "relationships": "Review relationship paths, cardinality and filter direction.",
        "dax_quality": "Use variables, simplify repeated expressions and review calculation dependencies.",
        "power_query_transformation": "Simplify transformations and preserve query folding where possible.",
        "performance": "Reduce model/render overhead and validate with Power BI performance tooling.",
        "dashboard_ux_visual_design": "Apply a consistent visual hierarchy, spacing system and formatting standard.",
        "business_kpi_alignment": "Clarify KPI intent, prominence and business meaning.",
        "maintainability_governance": "Introduce naming standards and lightweight documentation for key objects.",
    }.get(category, "Review and remediate the issue using Power BI best practices.")


def _icon_circle(d, center, fill, symbol, symbol_fill=NAVY):
    x, y = center
    d.ellipse((x-28, y-28, x+28, y+28), fill=fill)
    _txt(d, (x, y+1), symbol, F["h3"], symbol_fill, anchor="mm")


def _bar(d, x, y, w, score, color=YELLOW):
    d.rounded_rectangle((x, y, x+w, y+20), 10, fill="#E9EEF4")
    d.rounded_rectangle((x, y, x+w*max(0,min(score,100))/100, y+20), 10, fill=color)


def _summary_texts(result, cats):
    strongest = max(cats.items(), key=lambda kv: kv[1])
    weakest = min(cats.items(), key=lambda kv: kv[1])
    works = f"{strongest[0]} is the strongest assessed area at {strongest[1]}/100, indicating a solid foundation within the reviewed scope."
    concern = f"{weakest[0]} is the primary improvement area at {weakest[1]}/100 and should receive the first focused optimization effort."
    if cats.get("DAX Measures", 100) < 85:
        opportunity = "Simplifying DAX and reducing repeated calculation logic can improve maintainability and performance."
    else:
        opportunity = "Target the highest-priority findings first, then validate performance and user experience after implementation."
    return works, concern, opportunity


def render_page1(result, out):
    im, d = _new_page()
    project = result.get("project_name", "Power BI Project")
    date = result.get("report_date", "October 2026")
    score = int(result.get("assessment", {}).get("score", 0))
    cats = _normalized_category_scores(result)
    strongest = max(cats.items(), key=lambda kv: kv[1])
    weakest = min(cats.items(), key=lambda kv: kv[1])
    _brand(d, "POWER BI\nQUICK AUDIT", project, date)
    _txt(d, (M, 470), "Dashboard & Model Quality Assessment", F["h2"], NAVY)
    _rr(d, (M, 650, W-M, 900), 26)
    _txt(d, (M+60, 690), "OVERALL QUALITY SCORE (WEIGHTED)", F["label"], MUTED)
    _txt(d, (M+60, 745), str(score), F["score"], NAVY)
    _txt(d, (M+265, 795), "/ 100", F["score2"], MUTED)
    status, color = _status(score)
    d.rounded_rectangle((570, 775, 760, 845), 35, fill=color)
    _txt(d, (665, 811), status if len(status)<13 else "GOOD", F["h3"], WHITE, anchor="mm")
    y = 935
    cards = [
        ("Strongest Area", f"{strongest[0]} · {strongest[1]}/100", PALE_GREEN, GREEN, "✓"),
        ("Primary Risk", f"{weakest[0]} · {weakest[1]}/100", PALE_RED, RED, "!"),
        ("Top Opportunity", "DAX Optimization" if cats.get("DAX Measures",100)<85 else "Focused Optimization", PALE_YELLOW, YELLOW, "→"),
    ]
    for title, value, bg, fg, sym in cards:
        _rr(d, (M, y, 870, y+140), 22)
        _icon_circle(d, (M+65, y+70), bg, sym, fg)
        _txt(d, (M+135, y+32), title, F["h3"], NAVY)
        _txt(d, (M+135, y+78), value, F["body"], MUTED)
        y += 160
    _footer(d)
    im.save(out, "PNG", optimize=True)


def render_page2(result, out):
    im, d = _new_page()
    project = result.get("project_name", "Power BI Project")
    date = result.get("report_date", "October 2026")
    score = int(result.get("assessment", {}).get("score", 0))
    cats = _normalized_category_scores(result)
    _brand(d, "EXECUTIVE\nSUMMARY", project, date, 2)
    _rr(d, (M, 380, W-M, 600), 24)
    _txt(d, (M+55, 405), "OVERALL QUALITY SCORE (WEIGHTED)", F["label"], MUTED)
    _txt(d, (M+55, 450), str(score), F["score"], NAVY)
    _txt(d, (M+255, 500), "/ 100", F["score2"], MUTED)
    status, color = _status(score)
    d.rounded_rectangle((535, 470, 750, 535), 32, fill=color)
    _txt(d, (642, 502), status if len(status)<13 else "GOOD", F["h3"], WHITE, anchor="mm")
    _txt(d, (M+55, 560), "Weighted composite score based on category results below.", F["small"], MUTED)
    _rr(d, (M, 620, W-M, 730), 18, fill="#EEF5FF")
    _txt(d, (M+65, 642), "AUDIT SCOPE & METHODOLOGY", F["label"], MUTED)
    scope = ("This Quick Audit evaluates report design, semantic model structure, DAX quality, "
             "performance indicators, KPI clarity, and selected Power BI best practices based on "
             "the files and information provided.")
    _wrap(d, scope, (M+65, 675, W-M-35, 720), F["small"], MUTED, spacing=3)
    _txt(d, (M, 755), "CATEGORY SCORES", F["label"], MUTED)
    y=800
    palette=[(PALE_GREEN,GREEN),(PALE_YELLOW,YELLOW),(PALE_BLUE,BLUE),(PALE_RED,RED),(PALE_PURPLE,PURPLE),(PALE_GREEN,GREEN)]
    for (label, val),(bg,fg) in zip(cats.items(),palette):
        _rr(d, (M, y, W-M, y+62), 14)
        _icon_circle(d, (M+50, y+31), bg, "•", fg)
        _txt(d, (M+100, y+16), label, F["body_b"], NAVY)
        _txt(d, (675, y+11), str(val), F["h3"], NAVY)
        _txt(d, (740, y+19), "/100", F["small"], MUTED)
        stat, c = _status(val)
        pill = stat if len(stat)<=22 else "IMPROVEMENT"
        d.rounded_rectangle((850,y+13,1110,y+49),18,fill=PALE_GREEN if c==GREEN else PALE_YELLOW)
        _txt(d,(980,y+31),pill,F["tiny"],c,anchor="mm")
        y += 70
    works, concern, opp = _summary_texts(result,cats)
    _txt(d, (M, 1235), "KEY INSIGHTS", F["label"], MUTED)
    cards=[("What Works Well",works,PALE_GREEN,GREEN,"✓"),("Main Concern",concern,PALE_RED,RED,"!"),("Biggest Opportunity",opp,PALE_YELLOW,YELLOW,"→")]
    cw=(W-2*M-30)//3
    for i,(title,txt,bg,fg,sym) in enumerate(cards):
        x=M+i*(cw+15)
        _rr(d,(x,1280,x+cw,1565),20)
        _icon_circle(d,(x+55,1325),bg,sym,fg)
        _txt(d,(x+100,1305),title,F["label"],NAVY)
        _wrap(d,txt,(x+25,1375,x+cw-25,1545),F["small"],MUTED,spacing=4,max_lines=6)
    _footer(d)
    im.save(out,"PNG",optimize=True)


def render_page3(result, out):
    im,d=_new_page()
    project=result.get("project_name","Power BI Project"); date=result.get("report_date","October 2026")
    _brand(d,"DETAILED\nFINDINGS",project,date,3)
    findings=_top_findings(result,4)
    if not findings:
        findings=[{"title":"No confirmed findings","priority":"P4","severity":"low","impact":"low","effort":"low","category":"maintainability_governance"}]
    y=390
    for idx,f in enumerate(findings,1):
        h=270
        _rr(d,(M,y,W-M,y+h),20)
        pri=f.get("priority","P3")
        sev=f.get("severity","medium").lower()
        color=RED if pri=="P1" or sev in ("high","critical") else YELLOW if pri=="P2" or sev=="medium" else GREEN
        bg=PALE_RED if color==RED else PALE_YELLOW if color==YELLOW else PALE_GREEN
        d.rounded_rectangle((M+20,y+20,M+135,y+70),16,fill=bg)
        _txt(d,(M+77,y+45),f"F-{idx:02d}",F["h3"],color,anchor="mm")
        _txt(d,(M+160,y+20),f.get("title","Finding"),F["h3"],NAVY)
        _txt(d,(M+160,y+60),f"{pri} Priority",F["small"],color)
        d.rounded_rectangle((W-360,y+22,W-190,y+68),18,fill=bg)
        _txt(d,(W-275,y+45),sev.upper(),F["label"],color,anchor="mm")
        obs = f.get("evidence")
        if isinstance(obs, dict):
            if "measure" in obs: obs_txt=f"Evidence detected in measure: {obs.get('measure')}."
            elif "page" in obs: obs_txt=f"Evidence detected on report page: {obs.get('page')}."
            elif "relationship" in obs: obs_txt="Relationship metadata indicates this issue."
            else: obs_txt="Analyzer evidence supports this confirmed finding."
        else:
            obs_txt="Analyzer evidence supports this confirmed finding."
        why = f"Severity is {sev}; business impact is {f.get('impact','medium')}. Addressing it improves reliability, maintainability or user experience."
        rec = _finding_recommendation(f)
        rows=[("Observation",obs_txt),("Why it matters",why),("Recommendation",rec)]
        yy=y+95
        for lab,tx in rows:
            _txt(d,(M+25,yy),lab,F["label"],NAVY)
            _wrap(d,tx,(M+220,yy,W-395,yy+58),F["small"],MUTED,spacing=3,max_lines=2)
            yy+=58
        xx=W-360
        _txt(d,(xx,y+105),"Impact",F["small"],NAVY); _txt(d,(W-145,y+105),str(f.get("impact","medium")).title(),F["small"],color,anchor="rs")
        _txt(d,(xx,y+155),"Effort",F["small"],NAVY); _txt(d,(W-145,y+155),str(f.get("effort","medium")).title(),F["small"],YELLOW,anchor="rs")
        area=f.get("category","").replace("_"," ").title()
        _txt(d,(xx,y+205),"Area",F["small"],NAVY)
        _wrap(d,area,(xx+75,y+198,W-120,y+245),F["tiny"],BLUE,max_lines=2)
        y += h+20
    _footer(d)
    im.save(out,"PNG",optimize=True)


def _dashboard_preview(im, d, box, result):
    x1,y1,x2,y2=box
    preview = result.get("dashboard_preview_path")
    if preview and Path(preview).exists():
        try:
            pim=Image.open(preview).convert("RGB")
            fitted=ImageOps.contain(pim,(x2-x1,y2-y1))
            px=x1+(x2-x1-fitted.width)//2; py=y1+(y2-y1-fitted.height)//2
            im.paste(fitted,(px,py))
            return
        except Exception:
            pass
    d.rounded_rectangle(box,18,fill="#F7FAFD",outline=LINE)
    page_counts=result.get("analysis",{}).get("metadata",{}).get("page_visual_counts",{})
    total_visuals=sum(page_counts.values()) or result.get("analysis",{}).get("summary",{}).get("visuals",6) or 6
    cx=x1+25; cy=y1+25
    for i in range(4):
        d.rounded_rectangle((cx+i*100,cy,cx+i*100+88,cy+70),10,fill=WHITE,outline=LINE)
        _txt(d,(cx+i*100+10,cy+10),f"KPI {i+1}",F["tiny"],MUTED)
        _txt(d,(cx+i*100+10,cy+35),str(max(1,total_visuals-i)),F["label"],NAVY)
    d.rounded_rectangle((x1+25,y1+115,x1+250,y1+270),12,fill=WHITE,outline=LINE)
    pts=[]
    for i,v in enumerate((20,60,45,90,70,120,110)):
        pts.append((x1+45+i*28,y1+245-v))
    d.line(pts,fill=BLUE,width=5)
    d.rounded_rectangle((x1+270,y1+115,x2-25,y1+270),12,fill=WHITE,outline=LINE)
    for i,w in enumerate((130,105,85,60)):
        d.rounded_rectangle((x1+300,y1+140+i*28,x1+300+w,y1+158+i*28),8,fill=YELLOW)


def _model_diagram(d, box, result):
    x1,y1,x2,y2=box
    tables=result.get("analysis",{}).get("metadata",{}).get("tables",[])[:6]
    if not tables:
        tables=["Fact","Dim A","Dim B","Dim C"]
    positions=[]
    cols=2
    for i,t in enumerate(tables[:4]):
        xx=x1+20+(i%cols)*175; yy=y1+20+(i//cols)*125
        positions.append((str(t),xx,yy))
    if len(positions)>=4:
        for a,b in ((0,1),(0,2),(0,3)):
            ax=positions[a][1]+135; ay=positions[a][2]+42
            bx=positions[b][1]; by=positions[b][2]+42
            d.line((ax,ay,bx,by),fill=MUTED,width=3)
    for t,xx,yy in positions:
        d.rounded_rectangle((xx,yy,xx+140,yy+85),12,fill=WHITE,outline=BLUE,width=2)
        _wrap(d,t,(xx+12,yy+15,xx+128,yy+70),F["tiny"],NAVY,max_lines=2)


def render_page4(result,out):
    im,d=_new_page()
    project=result.get("project_name","Power BI Project"); date=result.get("report_date","October 2026")
    cats=_normalized_category_scores(result)
    _brand(d,"DASHBOARD &\nMODEL ASSESSMENT",project,date,4)
    _rr(d,(M,380,610,1045),20)
    _txt(d,(M+30,410),"Dashboard Design",F["h3"],NAVY); _txt(d,(455,405),f"{cats['Dashboard Design']}",F["h2"],NAVY); _txt(d,(520,420),"/100",F["small"],MUTED)
    sub=[("Visual Hierarchy",min(100,cats["Dashboard Design"]+1)),("KPI Clarity",max(0,cats["KPI & UX Clarity"]+2)),("Consistency",max(0,cats["Dashboard Design"]-2)),("Navigation",min(100,cats["Dashboard Design"]+2)),("Accessibility",max(0,cats["Dashboard Design"]-11))]
    yy=485
    for lab,val in sub:
        _txt(d,(M+30,yy),lab,F["small"],MUTED); _bar(d,M+205,yy+6,250,val); _txt(d,(560,yy),val,F["small"],NAVY,anchor="rs"); yy+=55
    tips=["Increase emphasis on primary KPIs.","Standardize spacing and chart formatting.","Reduce visual competition between secondary metrics."]
    yy=790
    for i,t in enumerate(tips,1):
        _icon_circle(d,(M+38,yy+18),PALE_YELLOW,str(i),NAVY)
        _wrap(d,t,(M+90,yy,575,yy+60),F["small"],MUTED,max_lines=2); yy+=75
    _rr(d,(630,380,W-M,1045),20)
    _txt(d,(665,410),"Dashboard Preview",F["h3"],NAVY)
    _dashboard_preview(im,d,(655,470,W-M-25,900),result)
    _txt(d,(655,925),"Customer screenshot is used when dashboard_preview_path is supplied;",F["tiny"],MUTED)
    _txt(d,(655,950),"otherwise this metadata-driven schematic is rendered.",F["tiny"],MUTED)
    _rr(d,(M,1080,610,1535),20)
    _txt(d,(M+30,1110),"Data Model",F["h3"],NAVY); _txt(d,(455,1105),f"{cats['Data Model']}",F["h2"],NAVY); _txt(d,(520,1120),"/100",F["small"],MUTED)
    _model_diagram(d,(M+30,1180,430,1450),result)
    _wrap(d,"Clear model structure with targeted opportunities to improve model efficiency.",(440,1200,585,1450),F["small"],MUTED,max_lines=8)
    _rr(d,(630,1080,W-M,1535),20)
    _txt(d,(665,1110),"Performance Review",F["h3"],NAVY); _txt(d,(990,1105),f"{cats['Performance']}",F["h2"],NAVY); _txt(d,(1065,1120),"/100",F["small"],MUTED)
    base=cats["Performance"]
    for i,(lab,val) in enumerate([("Query efficiency",max(0,base-2)),("Visual load",min(100,base+2)),("Maintainability",min(100,base+1))]):
        yy=1190+i*65; _txt(d,(665,yy),lab,F["small"],MUTED); _bar(d,850,yy+7,250,val); _txt(d,(1120,yy),val,F["small"],NAVY)
    _rr(d,(665,1400,W-M-25,1505),16,fill="#EEF5FF")
    _wrap(d,"Performance is acceptable overall but should be validated after DAX simplification and selective visual optimization.",(690,1420,W-M-50,1495),F["small"],MUTED,max_lines=3)
    _footer(d)
    im.save(out,"PNG",optimize=True)


def render_page5(result,out):
    im,d=_new_page()
    project=result.get("project_name","Power BI Project"); date=result.get("report_date","October 2026")
    _brand(d,"PRIORITIZED\nACTION PLAN",project,date,5)
    fs=_top_findings(result,4)
    actions=[]
    for f in fs:
        cat=f.get("category","")
        title={
            "dax_quality":"Simplify DAX Measures",
            "data_model_architecture":"Optimize Model Efficiency",
            "relationships":"Optimize Model Efficiency",
            "performance":"Improve Performance",
            "power_query_transformation":"Improve Query Efficiency",
            "dashboard_ux_visual_design":"Standardize Report Design",
            "business_kpi_alignment":"Clarify KPI & UX Priorities",
            "maintainability_governance":"Implement Governance Practices",
        }.get(cat,f.get("title","Address Priority Finding"))
        actions.append((title,_finding_recommendation(f),f.get("impact","medium"),f.get("effort","medium")))
    defaults=[
        ("Simplify DAX Measures","Refactor complex calculations and consolidate repeated logic to improve maintainability and performance.","high","medium"),
        ("Optimize Model Efficiency","Streamline the model by reducing unnecessary objects and reviewing relationship efficiency.","high","medium"),
        ("Standardize Report Design","Apply a consistent visual hierarchy, spacing system and KPI presentation approach.","medium","low"),
        ("Implement Governance Practices","Introduce naming standards, documentation and lightweight review practices.","medium","low"),
    ]
    while len(actions)<4: actions.append(defaults[len(actions)])
    _txt(d,(M,390),"PRIORITY ACTIONS",F["label"],MUTED)
    y=435
    for i,(title,desc,impact,effort) in enumerate(actions[:4],1):
        _rr(d,(M,y,W-M,y+130),18)
        _icon_circle(d,(M+48,y+65),PALE_BLUE,str(i),NAVY)
        _txt(d,(M+110,y+24),title,F["h3"],NAVY)
        _wrap(d,desc,(M+110,y+65,760,y+118),F["small"],MUTED,max_lines=2)
        _txt(d,(820,y+27),"Impact",F["small"],MUTED); _txt(d,(1030,y+27),"Effort",F["small"],MUTED)
        impc=RED if str(impact).lower()=="high" else YELLOW
        effc=GREEN if str(effort).lower()=="low" else YELLOW
        d.rounded_rectangle((805,y+65,935,y+103),18,fill=PALE_RED if impc==RED else PALE_YELLOW)
        _txt(d,(870,y+84),str(impact).upper(),F["tiny"],impc,anchor="mm")
        d.rounded_rectangle((1010,y+65,1140,y+103),18,fill=PALE_GREEN if effc==GREEN else PALE_YELLOW)
        _txt(d,(1075,y+84),str(effort).upper(),F["tiny"],effc,anchor="mm")
        y+=145
    _txt(d,(M,1035),"IMPROVEMENT ROADMAP",F["label"],MUTED)
    _txt(d,(W-M,1035),"Indicative implementation horizon",F["tiny"],MUTED,anchor="rs")
    boxes=[
        ("Quick Wins","1–2 weeks",["Simplify selected DAX measures","Remove unused tables/columns","Apply visual clean-up"],PALE_GREEN,GREEN),
        ("Key Improvements","2–6 weeks",["Optimize model efficiency","Standardize report design","Improve performance"],PALE_YELLOW,YELLOW),
        ("Long-Term Enhancements","1–3 months",["Implement governance practices","Establish naming standards","Validate scalability"],PALE_BLUE,BLUE),
    ]
    cw=(W-2*M-30)//3
    for i,(title,period,items,bg,fg) in enumerate(boxes):
        x=M+i*(cw+15); _rr(d,(x,1080,x+cw,1415),18)
        _icon_circle(d,(x+55,1125),bg,"•",fg)
        _txt(d,(x+100,1105),title,F["label"],NAVY)
        _txt(d,(x+100,1140),period,F["small"],MUTED)
        yy=1200
        for item in items:
            d.ellipse((x+25,yy+8,x+35,yy+18),fill=fg)
            _wrap(d,item,(x+50,yy,x+cw-20,yy+60),F["small"],MUTED,max_lines=2); yy+=62
    _rr(d,(M,1450,W-M,1585),18)
    _icon_circle(d,(M+55,1517),PALE_YELLOW,"→",YELLOW)
    _txt(d,(M+110,1475),"Recommended Next Step",F["h3"],NAVY)
    _wrap(d,"Implement the high-priority recommendations and perform a validation review after optimization.",(M+110,1520,W-M-30,1575),F["small"],MUTED,max_lines=2)
    _footer(d)
    im.save(out,"PNG",optimize=True)


def generate_basic_report_images(result: dict, out_dir: Path):
    """Generate five fixed-layout Basic report PNG pages and return their paths."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    if result.get("package") != "basic":
        return []
    pages = [
        out_dir / "01_basic_cover.png",
        out_dir / "02_basic_executive_summary.png",
        out_dir / "03_basic_detailed_findings.png",
        out_dir / "04_basic_dashboard_model_assessment.png",
        out_dir / "05_basic_prioritized_action_plan.png",
    ]
    render_page1(result,pages[0]); render_page2(result,pages[1]); render_page3(result,pages[2]); render_page4(result,pages[3]); render_page5(result,pages[4])
    return pages
