#!/usr/bin/env python3
"""Builds small reproducible PBIP-like fixtures for analyzer tests and demos."""
from pathlib import Path
import json, shutil


def write(path: Path, text: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding='utf-8')


def build(root: Path, optimized=False):
    if root.exists(): shutil.rmtree(root)
    model=root/'Demo.SemanticModel'/'definition'
    report=root/'Demo.Report'/'definition'/'pages'
    write(root/'Demo.pbip', '{"version":"1.0","artifacts":[{"report":{"path":"Demo.Report"}}]}')
    if optimized:
        write(model/'Date.tmdl', "table Date\n\tcolumn Date\n")
        write(model/'DimCustomer.tmdl', "table DimCustomer\n\tcolumn CustomerKey\n")
        write(model/'DimProduct.tmdl', "table DimProduct\n\tcolumn ProductKey\n")
        write(model/'FactSales.tmdl', "table FactSales\n\tcolumn OrderDate\n\tcolumn CustomerKey\n\tcolumn ProductKey\n")
        write(model/'Measures.tmdl', "table Measures\n\tmeasure Revenue = SUM(FactSales[Revenue])\n\tmeasure Margin = DIVIDE([Profit],[Revenue])\n")
        rel="""relationship r1\n\tfromColumn: FactSales.CustomerKey\n\ttoColumn: DimCustomer.CustomerKey\n\tfromCardinality: many\n\ttoCardinality: one\n\tcrossFilteringBehavior: oneDirection\n\nrelationship r2\n\tfromColumn: FactSales.ProductKey\n\ttoColumn: DimProduct.ProductKey\n\tfromCardinality: many\n\ttoCardinality: one\n\tcrossFilteringBehavior: oneDirection\n\nrelationship r3\n\tfromColumn: FactSales.OrderDate\n\ttoColumn: Date.Date\n\tfromCardinality: many\n\ttoCardinality: one\n\tcrossFilteringBehavior: oneDirection\n"""
        write(model/'relationships.tmdl', rel)
        visual_count=9
    else:
        write(model/'DimCustomer.tmdl', "table DimCustomer\n\tcolumn CustomerKey\n")
        write(model/'DimProduct.tmdl', "table DimProduct\n\tcolumn ProductKey\n")
        write(model/'DimCategory.tmdl', "table DimCategory\n\tcolumn CategoryKey\n")
        write(model/'FactSales.tmdl', "table FactSales\n\tcolumn OrderDate\n\tcolumn CustomerKey\n\tcolumn ProductKey\n")
        write(model/'Budget.tmdl', "table Budget\n\tcolumn ProductKey\n")
        write(model/'Measures.tmdl', """table Measures\n\tmeasure Revenue = SUM(FactSales[Revenue])\n\tmeasure Margin = [Profit] / [Revenue]\n\tmeasure Selected Region = IF(HASONEVALUE(DimCustomer[Region]), VALUES(DimCustomer[Region]), \"Multiple\")\n\tmeasure Orders = COUNT(FactSales[OrderId])\n\tmeasure Iterated Revenue = SUMX(FactSales, FactSales[Quantity] * FactSales[Price])\n""")
        rel="""relationship r1\n\tfromColumn: FactSales.CustomerKey\n\ttoColumn: DimCustomer.CustomerKey\n\tfromCardinality: many\n\ttoCardinality: one\n\tcrossFilteringBehavior: bothDirections\n\nrelationship r2\n\tfromColumn: Budget.ProductKey\n\ttoColumn: FactSales.ProductKey\n\tfromCardinality: many\n\ttoCardinality: many\n\tcrossFilteringBehavior: bothDirections\n\nrelationship r3\n\tfromColumn: DimProduct.CategoryKey\n\ttoColumn: DimCategory.CategoryKey\n\tfromCardinality: many\n\ttoCardinality: one\n\tcrossFilteringBehavior: oneDirection\n"""
        write(model/'relationships.tmdl', rel)
        visual_count=16
    page=report/'Executive'
    write(page/'page.json', json.dumps({'name':'Executive','displayName':'Executive'}))
    for i in range(visual_count):
        write(page/'visuals'/f'v{i+1}.json', json.dumps({'visualType':'card','queryFields':[]}))
    return root

if __name__=='__main__':
    base=Path(__file__).resolve().parents[1]/'demo_generated'
    build(base/'PowerBI_Audit_Demo', optimized=False)
    build(base/'PowerBI_Audit_Demo_Optimized', optimized=True)
    print(base)
