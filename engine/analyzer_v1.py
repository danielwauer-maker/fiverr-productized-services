#!/usr/bin/env python3
"""Power BI PBIP/PBIR/TMDL Analyzer V1.
Produces candidate findings mapped to Assessment Engine rule IDs.
It intentionally does not auto-confirm hybrid/manual rules.
"""
from pathlib import Path
import argparse, json, re

HERE=Path(__file__).resolve().parent
ENGINE=json.loads((HERE/'assessment-engine-v1.json').read_text(encoding='utf-8'))
ALL_RULES=[]
for rule_file in sorted((HERE/'rules').glob('*.json')):
    ALL_RULES.extend(json.loads(rule_file.read_text(encoding='utf-8')))
RULES={r['id']:r for r in ALL_RULES}

TABLE_RE=re.compile(r'^\s*table\s+[\'\"]?([^\'\"\n]+?)[\'\"]?\s*$',re.M)
MEASURE_RE=re.compile(r'^\s*measure\s+[\'\"]?([^=\'\"\n]+?)[\'\"]?\s*=\s*(.+)$',re.M)
COLUMN_RE=re.compile(r'^\s*column\s+[\'\"]?([^=\'\"\n]+?)[\'\"]?(?:\s*=\s*(.+))?$',re.M)
REL_BLOCK_RE=re.compile(r'^relationship\s+([^\n]+)\n(.*?)(?=^relationship\s+|\Z)',re.M|re.S)

def prop(block,name):
    m=re.search(rf'^\s*{re.escape(name)}:\s*(.+?)\s*$',block,re.M)
    return m.group(1).strip() if m else None

def candidate(rule_id,evidence,confidence='medium'):
    r=RULES[rule_id]
    return {'rule_id':rule_id,'status':'candidate','detection_mode':r['detection_mode'],
            'title':r['title'],'confidence':confidence,'evidence':evidence,
            'default_severity':r['default_severity'],'default_business_impact':r['default_business_impact'],
            'default_effort':r['default_effort'],'score_deduction_if_confirmed':r['score_deduction'],
            'review_note':r['review_note']}

def find_project(path:Path):
    path=path.resolve()
    if path.is_file() and path.suffix.lower()=='.pbip': return path.parent
    if path.is_dir(): return path
    raise SystemExit('Provide a PBIP file or PBIP project directory.')

def analyze(path:Path):
    project=find_project(path)
    tmdls=list(project.rglob('*.tmdl'))
    jsons=list(project.rglob('*.json'))
    tables=[]; measures=[]; columns=[]; relationships=[]
    for f in tmdls:
        text=f.read_text(encoding='utf-8',errors='ignore')
        if f.name.lower().startswith('relationship'):
            for name,block in REL_BLOCK_RE.findall(text):
                relationships.append({'name':name.strip(),'fromColumn':prop(block,'fromColumn'),'toColumn':prop(block,'toColumn'),
                    'fromCardinality':prop(block,'fromCardinality'),'toCardinality':prop(block,'toCardinality'),
                    'crossFilteringBehavior':prop(block,'crossFilteringBehavior'),'isActive':prop(block,'isActive')})
            continue
        tm=TABLE_RE.search(text)
        table=tm.group(1).strip() if tm else f.stem
        tables.append(table)
        for name,expr in MEASURE_RE.findall(text): measures.append({'table':table,'name':name.strip(),'expression':expr.strip()})
        for name,expr in COLUMN_RE.findall(text): columns.append({'table':table,'name':name.strip(),'calculated':bool(expr.strip()),'expression':expr.strip() or None})
    pages=[]; visuals=[]
    for f in jsons:
        try: obj=json.loads(f.read_text(encoding='utf-8'))
        except Exception: continue
        if f.name=='page.json': pages.append({'path':str(f.relative_to(project)),'name':obj.get('displayName') or obj.get('name')})
        if 'visualType' in obj: visuals.append({'path':str(f.relative_to(project)),'page':f.parent.parent.name,'visualType':obj.get('visualType'),'fields':obj.get('queryFields',[])})
    findings=[]
    for r in relationships:
        if (r.get('crossFilteringBehavior') or '').lower() in ('bothdirections','both','bidirectional'):
            findings.append(candidate('REL-001',{'relationship':r},'high'))
        fc=(r.get('fromCardinality') or '').lower(); tc=(r.get('toCardinality') or '').lower()
        if fc=='many' and tc=='many': findings.append(candidate('REL-002',{'relationship':r},'high'))
    for m in measures:
        e=m['expression']; upper=e.upper()
        if '/' in e and 'DIVIDE(' not in upper: findings.append(candidate('DAX-003',{'measure':m['name'],'expression':e},'medium'))
        if 'HASONEVALUE(' in upper and 'VALUES(' in upper: findings.append(candidate('DAX-004',{'measure':m['name'],'expression':e},'high'))
        if re.search(r'\bCOUNT\s*\(',upper): findings.append(candidate('DAX-005',{'measure':m['name'],'expression':e},'medium'))
        if ('ISBLANK(' in upper and re.search(r'\b0\b',e)) or 'COALESCE(' in upper: findings.append(candidate('DAX-006',{'measure':m['name'],'expression':e},'medium'))
        if re.search(r'\b(SUMX|AVERAGEX|FILTER)\s*\(',upper): findings.append(candidate('DAX-007',{'measure':m['name'],'expression':e},'low'))
        if upper.count('IF(')>=3: findings.append(candidate('DAX-008',{'measure':m['name'],'expression':e},'high'))
    date_like=[t for t in tables if re.search(r'(^|\b)(date|calendar|datum|kalender)(\b|$)',t,re.I)]
    date_cols=[c for c in columns if re.search(r'date|datum',c['name'],re.I)]
    if date_cols and not date_like: findings.append(candidate('DMA-003',{'date_columns':[f"{c['table']}.{c['name']}" for c in date_cols],'date_dimension_detected':False},'medium'))
    dimdim=[]
    for r in relationships:
        a=(r.get('fromColumn') or '').split('.')[0]; b=(r.get('toColumn') or '').split('.')[0]
        if a.lower().startswith('dim') and b.lower().startswith('dim'): dimdim.append(r['name'])
    if dimdim: findings.append(candidate('DMA-004',{'dimension_to_dimension_relationships':dimdim},'medium'))
    counts={}
    for v in visuals: counts[v['page']]=counts.get(v['page'],0)+1
    for page,count in counts.items():
        if count>12: findings.append(candidate('PERF-001',{'page':page,'visual_count':count,'threshold_v1':12},'high'))
    bad_names=[]
    for m in measures:
        if re.search(r'copy|test|tmp|debug',m['name'],re.I): bad_names.append(m['name'])
    if bad_names: findings.append(candidate('GOV-001',{'suspicious_measure_names':bad_names},'medium'))
    if measures: findings.append(candidate('GOV-003',{'measure_count':len(measures),'description_metadata_detected':False},'low'))
    summary={'project':project.name,'tables':len(tables),'columns':len(columns),'measures':len(measures),'relationships':len(relationships),'pages':len(pages),'visuals':len(visuals)}
    return {'analyzer_version':'1.0.0','source_format':'PBIP/PBIR/TMDL','summary':summary,'metadata':{'tables':tables,'measures':measures,'relationships':relationships,'page_visual_counts':counts},'candidate_findings':findings,
            'delivery_guardrail':'Candidate findings are NOT customer-facing confirmed findings. Hybrid/manual findings require expert validation before scoring/delivery.'}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('path'); ap.add_argument('-o','--output')
    a=ap.parse_args(); result=analyze(Path(a.path)); text=json.dumps(result,indent=2,ensure_ascii=False)
    if a.output: Path(a.output).write_text(text,encoding='utf-8')
    else: print(text)
if __name__=='__main__': main()
