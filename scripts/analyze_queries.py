"""Analyze extracted query SQL and produce assessment documents.

Reads assessment/queries/_raw_queries.json (from extract_query_sql.py)
and produces:
  - assessment/queries/_overview.md (query catalogue with type classification)
  - assessment/queries/dependency_graph.md (dependency visualization)

Uses db_reader.py's get_user_tables() for table name reference set.

Usage:
    python scripts/analyze_queries.py
"""

import hashlib
import json
import re
import sys
from pathlib import Path

from tabulate import tabulate

# Project paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent
RAW_JSON = PROJECT_ROOT / "assessment" / "queries" / "_raw_queries.json"
OUTPUT_DIR = PROJECT_ROOT / "assessment" / "queries"

# Known user tables (from db_reader.py / Phase 1 inventory)
KNOWN_TABLES = {
    "ข้อมูลร้านค้า",
    "ข้อมูลสมาชิก",
    "คะแนนที่ลูกค้าใช้ไป",
    "รายละเอียดออเดอร์",
    "สินค้า",
    "สินค้าในแต่ละออเดอร์",
    "สินค้าในแต่ละใบรับเข้า",
    "สินค้าในแต่ละใบเบิก",
    "หัวใบรับเข้า",
    "หัวใบเบิก",
}

# Thai-to-English purpose annotations for common query name components
THAI_GLOSSARY = {
    "คะแนน": "points",
    "คงเหลือ": "remaining",
    "หลังจากใช้แล้ว": "after use",
    "รวม": "total",
    "ลูกค้า": "customer",
    "แต่ละคน": "per person",
    "จำนวน": "quantity",
    "ขาย": "sold/sales",
    "สินค้า": "product",
    "แต่ละตัว": "per item",
    "รับเข้า": "goods receipt/received",
    "ทุกตัว": "all items",
    "เบิก": "withdrawal/issued",
    "ดูยอดซื้อ": "view purchase total",
    "ร้านค้า": "shop",
    "แต่ละเจ้า": "per vendor",
    "ที่อยู่": "address",
    "เจาะจง": "specific/filter by",
    "โดยวันที่": "by date",
    "ปลีก": "retail",
    "ยอดขาย": "sales total",
    "ทั้งปี": "full year",
    "รายละเอียด": "details",
    "โอนเงิน": "bank transfer",
    "แต่ละออเดอร์": "per order",
    "วันที่และเวลา": "date and time",
    "เรียงตาม": "ordered by",
    "ใบกำกับ": "invoice",
    "สต็อค": "stock",
    "ในแต่ละออเดอร์": "per order",
    "หมายเลข": "number",
    "ออเดอร์": "order",
    "เลขที่": "number",
    "ใบรับเข้า": "goods receipt",
    "ใบเบิก": "goods issue",
    "รอโอน": "pending transfer",
    "ส่งของให้ก่อน": "ship first",
    "ขายดี": "best selling",
    "ย้อนหลัง": "lookback",
    "เดือน": "months",
    "กำหนด": "assign",
    "เลขที่inv": "invoice number",
    "ยอดเงิน": "amount",
    "รายงาน": "report",
    "วัตุดิบ": "raw materials",
    "ลงยอด": "post amount",
    "ใส่": "insert/assign",
    "ใบกำกับ": "invoice",
    "ระบุวันที่": "specify date",
    "ดูจำนวนรวม": "view combined quantity",
    "สั่ง": "order",
    "หลายออเดอร์": "multiple orders",
    "รวมกัน": "combined",
}


def load_queries() -> list[dict]:
    """Load raw queries from JSON."""
    with open(RAW_JSON, encoding="utf-8") as f:
        return json.load(f)


def classify_query_type(sql: str) -> dict:
    """Classify a query by its actual SQL content.

    Returns dict with: base_type, parameterized, parameter_prompts.
    """
    if not sql:
        return {"base_type": "UNKNOWN", "parameterized": False, "parameter_prompts": []}

    sql_norm = " ".join(sql.split())
    sql_upper = sql_norm.upper().strip()

    # Check for PARAMETERS declaration
    parameterized = sql_upper.startswith("PARAMETERS") or "PARAMETERS " in sql_upper
    parameter_prompts = []

    # Extract parameter prompt patterns [text] used as input values
    # These appear in WHERE clauses as field references not in brackets
    # that don't match known table/column patterns
    prompt_pattern = r'Between\s+\[([^\]]+)\]\s+And\s+\[([^\]]+)\]'
    for match in re.finditer(prompt_pattern, sql_norm, re.IGNORECASE):
        p1, p2 = match.group(1), match.group(2)
        # Simple heuristic: if it doesn't contain a dot, it might be a prompt
        if '.' not in p1 and not p1.startswith('Forms!'):
            parameter_prompts.append(p1)
        if '.' not in p2 and not p2.startswith('Forms!'):
            parameter_prompts.append(p2)

    # Also detect [Forms!...] references (form field references, not prompts but notable)
    form_refs = re.findall(r'\[Forms\]!\[([^\]]+)\]!\[([^\]]+)\]', sql_norm)

    # Detect base type from SQL content
    if "UNION" in sql_upper and ("SELECT" in sql_upper):
        # Check if it's a real UNION (has UNION keyword between SELECT blocks)
        if re.search(r'SELECT\b.*\bUNION\b.*\bSELECT\b', sql_upper, re.DOTALL):
            base_type = "UNION"
        else:
            base_type = "SELECT"
    elif "TRANSFORM" in sql_upper:
        base_type = "CROSSTAB"
    elif sql_upper.lstrip("PARAMETERS").strip().lstrip(";").strip().startswith("UPDATE"):
        base_type = "UPDATE"
    elif sql_upper.lstrip("PARAMETERS").strip().lstrip(";").strip().startswith("INSERT"):
        base_type = "INSERT"
    elif sql_upper.lstrip("PARAMETERS").strip().lstrip(";").strip().startswith("DELETE"):
        base_type = "DELETE"
    else:
        # After PARAMETERS declaration, look for the actual statement
        remaining = sql_upper
        if remaining.startswith("PARAMETERS"):
            # Skip to after the semicolon ending the PARAMETERS clause
            semi_pos = remaining.find(";")
            if semi_pos != -1:
                remaining = remaining[semi_pos + 1:].strip()

        if remaining.startswith("SELECT"):
            base_type = "SELECT"
        elif remaining.startswith("UPDATE"):
            base_type = "UPDATE"
        elif remaining.startswith("INSERT"):
            base_type = "INSERT"
        elif remaining.startswith("DELETE"):
            base_type = "DELETE"
        else:
            base_type = "SELECT"  # Default

    return {
        "base_type": base_type,
        "parameterized": parameterized,
        "parameter_prompts": parameter_prompts,
        "form_refs": form_refs if form_refs else [],
    }


def extract_references(sql: str, known_tables: set, known_queries: set) -> dict:
    """Extract table and query references from SQL text.

    Returns dict with: tables (set), queries (set).
    """
    if not sql:
        return {"tables": set(), "queries": set()}

    sql_norm = " ".join(sql.split())

    references = set()

    # Match bracket-quoted identifiers after FROM, JOIN, INTO, UPDATE keywords
    patterns = [
        r'\bFROM\s+\[([^\]]+)\]',
        r'\bJOIN\s+\[([^\]]+)\]',
        r'\bINTO\s+\[([^\]]+)\]',
        r'\bUPDATE\s+\[([^\]]+)\]',
        # Also match unbracketed identifiers
        r'\bFROM\s+([^\[\s,;()]+)',
        r'\bJOIN\s+([^\[\s,;()]+)',
        r'\bINTO\s+([^\[\s,;()]+)',
        r'\bUPDATE\s+([^\[\s,;()]+)',
    ]

    for pattern in patterns:
        for match in re.finditer(pattern, sql_norm, re.IGNORECASE):
            ref = match.group(1).strip()
            # Skip subquery aliases (they contain SELECT) and system refs
            if ref.upper().startswith("SELECT"):
                continue
            if ref.upper() in ("DISTINCTROW", "*", "DUAL"):
                continue
            references.add(ref)

    # Also extract references from embedded subqueries in FROM [SELECT ... FROM table ...]
    embedded_from_pattern = r'FROM\s+\[SELECT\b[^\]]*\bFROM\s+([^\]\s,;]+)'
    for match in re.finditer(embedded_from_pattern, sql_norm, re.IGNORECASE):
        ref = match.group(1).strip().strip('[]')
        references.add(ref)

    embedded_join_pattern = r'FROM\s+\[SELECT\b[^\]]*\bJOIN\s+([^\]\s,;]+)'
    for match in re.finditer(embedded_join_pattern, sql_norm, re.IGNORECASE):
        ref = match.group(1).strip().strip('[]')
        references.add(ref)

    tables = references & known_tables
    queries = references & known_queries

    return {"tables": tables, "queries": queries}


def generate_purpose(name: str, query_type: str, tables: set, queries: set, sql: str) -> str:
    """Generate a 1-line English purpose description for a query."""
    # For hidden subqueries, describe their role
    if name.startswith("~sq_c"):
        # Subform data source
        parts = name.split("~sq_c")
        form_hint = parts[1] if len(parts) > 1 else ""
        subform_hint = parts[2] if len(parts) > 2 else ""
        return f"Subform data source for {form_hint} -> {subform_hint}"

    if name.startswith("~sq_d"):
        # Report/form combo box data source
        parts = name.split("~sq_d")
        parent = parts[1] if len(parts) > 1 else ""
        child = parts[2] if len(parts) > 2 else ""
        return f"Lookup/combo data source: {parent} -> {child}"

    if name.startswith("~sq_r"):
        # Report record source
        parts = name.split("~sq_r")
        report = parts[1] if len(parts) > 1 else ""
        return f"Report record source for {report}"

    # For user queries, build purpose from name + context
    table_list = ", ".join(sorted(tables)) if tables else "calculated"
    query_list = ", ".join(sorted(queries)) if queries else ""

    # Heuristic purpose based on name patterns
    name_lower = name.lower()

    if "คะแนนคงเหลือ" in name:
        return f"Calculate remaining loyalty points after redemptions -- from {table_list}"
    elif "คะแนนรวม" in name:
        return f"Sum total loyalty points per customer -- from {table_list}"
    elif "จำนวนที่ขาย" in name and "ระบุวันที่" in name:
        return f"Quantity sold per product filtered by date range (parameterized) -- from {table_list}"
    elif "จำนวนที่ขาย" in name:
        return f"Total quantity sold per product across all orders -- from {table_list}"
    elif "จำนวนรับเข้ารวม" in name:
        return f"Total quantity received (goods receipt) per product -- from {table_list}"
    elif "จำนวนเบิกรวม" in name:
        return f"Total quantity issued (goods withdrawal) per product -- from {table_list}"
    elif "ดูยอดซื้อ" in name:
        return f"View purchase totals per shop vendor -- from {table_list}"
    elif "ที่อยู่เจาะจง" in name and "ปลีก" in name:
        return f"Retail customer addresses filtered by date range -- from {table_list}"
    elif "ที่อยู่เจาะจง" in name and "ร้านค้า" in name:
        return f"Shop addresses filtered by date range -- from {table_list}"
    elif "ยอดขายร้านค้า" in name:
        return f"Shop sales totals with pricing and discounts -- from {table_list}"
    elif "ยอดขายลูกค้าปลีก" in name:
        return f"Retail customer sales totals -- from {table_list}"
    elif "ยอดซื้อร้านค้าทั้งปี" in name:
        return f"Shop purchase totals for the full year -- from {table_list}"
    elif "รายละเอียดการโอนเงินร้านค้า" in name:
        return f"Shop bank transfer details with order and payment info -- from {table_list}"
    elif "รายละเอียดการโอนแต่ละออเดอร์ปลีก" in name:
        return f"Retail order bank transfer details -- from {table_list}"
    elif "วันที่และเวลาโอนเงิน" in name:
        return f"Transfer date/time sorted by invoice number -- from {table_list}"
    elif "สต็อคสินค้าในแต่ละออเดอร์ปลีก" in name:
        return f"Stock levels for products in retail orders -- from {table_list}"
    elif "สต็อคสินค้า" in name:
        return f"Current stock levels (received minus issued minus sold) -- from {table_list}"
    elif "สินค้าในแต่ละออเดอร์ปลีก" in name:
        return f"Product line items per retail order with pricing/VAT -- from {table_list}"
    elif "สินค้าในแต่ละออเดอร์ร้านค้า" in name:
        return f"Product line items per shop order with pricing/VAT/discounts -- from {table_list}"
    elif "เจาะจงหมายเลขออเดอร์ปลีก" in name:
        return f"Look up retail order by order number -- from {table_list}"
    elif "เจาะจงหมายเลขออเดอร์ร้านค้า" in name:
        return f"Look up shop order by order number -- from {table_list}"
    elif "เจาะจงเลขที่ใบรับเข้า" in name:
        return f"Look up specific goods receipt -- from {table_list}"
    elif "เจาะจงเลขที่ใบเบิก" in name:
        return f"Look up specific goods issue -- from {table_list}"
    elif "ร้านค้ารอโอน" in name:
        return f"Shops with pending bank transfers -- from {table_list}"
    elif "ร้านค้าส่งของให้ก่อน" in name:
        return f"Shops requiring advance shipment -- from {table_list}"
    elif "สินค้าที่ขายดี" in name and "3 เดือน" in name:
        return f"Best-selling products over last 3 months -- from {table_list}"
    elif "กำหนดเลขที่inv" in name:
        return f"Assign invoice number sequence -- from {table_list}"
    elif "ยอดเงินร้านค้า" in name:
        return f"Shop payment amounts with order and transfer details -- from {table_list}"
    elif "รายงานสินค้าและวัตุดิบ" in name:
        return f"UNION report combining products and raw materials -- from {table_list}"
    elif "ลงยอดร้านค้า" in name:
        return f"Post shop payment amounts -- from {table_list}"
    elif "ใส่เลขที่ใบกำกับ" in name:
        return f"Assign tax invoice number to orders -- from {table_list}"
    elif "ดูจำนวนรวม" in name and "หลายออเดอร์" in name:
        return f"View combined quantity of products across multiple orders -- from {table_list}"
    elif '"ซอง"' in name or '"ตัว"' in name:
        return f"Value list for product unit types (pack/piece/bead) -- from {table_list}"
    elif "ตรวจภาษีขาย" in name and "inv" in name:
        return f"Sales tax audit sorted by invoice number -- from {table_list}"
    elif "รายงานภาษีขาย" in name:
        return f"Sales tax report with VAT breakdown -- from {table_list}"
    else:
        # Generic fallback
        refs = table_list
        if query_list:
            refs += f" via {query_list}"
        return f"{query_type} query referencing {refs}"


def safe_id(name: str) -> str:
    """Convert Thai/special chars to safe Mermaid node ID."""
    h = hashlib.md5(name.encode("utf-8")).hexdigest()[:8]
    return f"n{h}"


def generate_overview(queries: list[dict], analyses: list[dict]) -> str:
    """Generate assessment/queries/_overview.md content."""
    lines = []
    lines.append("# Query Assessment Overview")
    lines.append("")
    lines.append("**Generated:** 2026-02-15")
    lines.append("**Source:** data/epic_db.accdb via Jackcess 4.0.8 / JPype1")
    lines.append("**Generator:** scripts/analyze_queries.py (rerun to regenerate)")
    lines.append("")

    # Separate user and hidden queries
    user_queries = [(q, a) for q, a in zip(queries, analyses) if not q["name"].startswith("~sq_")]
    hidden_queries = [(q, a) for q, a in zip(queries, analyses) if q["name"].startswith("~sq_")]

    # Summary
    lines.append("## Summary")
    lines.append("")
    lines.append(f"- **Total queries:** {len(queries)} ({len(user_queries)} user-visible, {len(hidden_queries)} hidden system)")

    # Type counts
    type_counts = {}
    for q, a in zip(queries, analyses):
        t = a["classification"]["base_type"]
        type_counts[t] = type_counts.get(t, 0) + 1

    type_rows = [[t, c] for t, c in sorted(type_counts.items(), key=lambda x: -x[1])]
    lines.append("")
    lines.append(tabulate(type_rows, headers=["Type", "Count"], tablefmt="pipe"))

    parameterized_count = sum(1 for _, a in zip(queries, analyses) if a["classification"]["parameterized"])
    form_ref_count = sum(1 for _, a in zip(queries, analyses) if a["classification"].get("form_refs"))
    lines.append("")
    lines.append(f"- **Parameterized queries (PARAMETERS keyword):** {parameterized_count}")
    lines.append(f"- **Queries referencing form controls:** {form_ref_count}")
    lines.append(f"- **Hidden system subqueries:** {len(hidden_queries)}")
    lines.append("")

    # Query Catalogue (user queries)
    lines.append("## Query Catalogue")
    lines.append("")
    lines.append("> Query type classification based on actual SQL content (not MSysObjects flags).")
    lines.append("")

    cat_rows = []
    for q, a in user_queries:
        cls = a["classification"]
        refs = a["references"]
        type_label = cls["base_type"]
        if cls["parameterized"]:
            type_label += " (P)"

        tables_str = ", ".join(sorted(refs["tables"])) if refs["tables"] else "-"
        queries_str = ", ".join(sorted(refs["queries"])) if refs["queries"] else "-"
        form_ref_str = "Yes" if cls.get("form_refs") else "No"

        cat_rows.append([
            q["name"],
            type_label,
            tables_str,
            queries_str,
            form_ref_str,
            a["purpose"],
        ])

    lines.append(tabulate(
        cat_rows,
        headers=["Name", "Type", "Tables Referenced", "Queries Referenced", "Form Refs", "Purpose"],
        tablefmt="pipe",
    ))
    lines.append("")

    # Hidden Subqueries section
    lines.append("## Hidden System Subqueries")
    lines.append("")
    lines.append("> These are auto-generated queries (`~sq_*` prefix) created by Access for subforms,")
    lines.append("> combo boxes, and report record sources. They are not visible in the query list")
    lines.append("> but are essential data sources for forms and reports.")
    lines.append("")

    # Group hidden queries by prefix type
    sq_c = [(q, a) for q, a in hidden_queries if q["name"].startswith("~sq_c")]
    sq_d = [(q, a) for q, a in hidden_queries if q["name"].startswith("~sq_d")]
    sq_r = [(q, a) for q, a in hidden_queries if q["name"].startswith("~sq_r")]

    lines.append(f"- **`~sq_c*` (subform control sources):** {len(sq_c)}")
    lines.append(f"- **`~sq_d*` (lookup/combo data sources):** {len(sq_d)}")
    lines.append(f"- **`~sq_r*` (report record sources):** {len(sq_r)}")
    lines.append("")

    hidden_rows = []
    for q, a in hidden_queries:
        cls = a["classification"]
        refs = a["references"]
        type_label = cls["base_type"]
        if cls["parameterized"]:
            type_label += " (P)"
        tables_str = ", ".join(sorted(refs["tables"])) if refs["tables"] else "-"

        hidden_rows.append([
            q["name"],
            type_label,
            tables_str,
            a["purpose"],
        ])

    lines.append(tabulate(
        hidden_rows,
        headers=["Name", "Type", "Tables Referenced", "Purpose"],
        tablefmt="pipe",
    ))
    lines.append("")

    # Query Type Distribution (detailed)
    lines.append("## Query Type Distribution")
    lines.append("")
    lines.append("### User Queries")
    lines.append("")
    user_type_counts = {}
    for q, a in user_queries:
        t = a["classification"]["base_type"]
        user_type_counts[t] = user_type_counts.get(t, 0) + 1
    user_type_rows = [[t, c] for t, c in sorted(user_type_counts.items(), key=lambda x: -x[1])]
    lines.append(tabulate(user_type_rows, headers=["Type", "Count"], tablefmt="pipe"))
    lines.append("")

    lines.append("### All Queries (including hidden)")
    lines.append("")
    all_type_rows = [[t, c] for t, c in sorted(type_counts.items(), key=lambda x: -x[1])]
    lines.append(tabulate(all_type_rows, headers=["Type", "Count"], tablefmt="pipe"))
    lines.append("")

    # Parameterized queries detail
    lines.append("## Parameterized and Form-Referencing Queries")
    lines.append("")
    lines.append("> Queries with PARAMETERS keyword or [Forms]!... references require runtime input.")
    lines.append("> These represent user interaction points in the Access application.")
    lines.append("")

    param_rows = []
    for q, a in zip(queries, analyses):
        cls = a["classification"]
        if cls["parameterized"] or cls.get("form_refs"):
            params = "PARAMETERS" if cls["parameterized"] else "-"
            form_refs_str = ", ".join(f"{f[0]}!{f[1]}" for f in cls.get("form_refs", []))
            if not form_refs_str:
                form_refs_str = "-"
            prompts = ", ".join(cls.get("parameter_prompts", []))
            if not prompts:
                prompts = "-"
            param_rows.append([q["name"][:60], params, form_refs_str[:60], prompts])

    if param_rows:
        lines.append(tabulate(
            param_rows,
            headers=["Query Name", "Has PARAMETERS", "Form References", "Input Prompts"],
            tablefmt="pipe",
        ))
    lines.append("")

    return "\n".join(lines)


def generate_dependency_graph(queries: list[dict], analyses: list[dict]) -> str:
    """Generate assessment/queries/dependency_graph.md content."""
    lines = []
    lines.append("# Query Dependency Graph")
    lines.append("")
    lines.append("**Generated:** 2026-02-15")
    lines.append("**Source:** data/epic_db.accdb via Jackcess 4.0.8 / JPype1")
    lines.append("**Generator:** scripts/analyze_queries.py (rerun to regenerate)")
    lines.append("")

    # Build full dependency data
    user_queries = [(q, a) for q, a in zip(queries, analyses) if not q["name"].startswith("~sq_")]

    # Mermaid graph (user queries only for readability)
    lines.append("## Dependency Diagram")
    lines.append("")
    lines.append("> Tables shown as rectangles, queries as rounded boxes.")
    lines.append("> Arrows show data flow: source -> consumer.")
    lines.append("")
    lines.append("```mermaid")
    lines.append("graph LR")
    lines.append("")

    # Collect all nodes and edges
    table_nodes = set()
    query_nodes = set()
    edges = []

    for q, a in user_queries:
        refs = a["references"]
        qname = q["name"]
        qid = safe_id(qname)
        query_nodes.add((qid, qname))

        for table in refs["tables"]:
            tid = safe_id(table)
            table_nodes.add((tid, table))
            edges.append((tid, qid))

        for qref in refs["queries"]:
            refid = safe_id(qref)
            query_nodes.add((refid, qref))
            edges.append((refid, qid))

    # Define nodes with shapes
    lines.append("    %% Tables (rectangles)")
    for tid, tname in sorted(table_nodes):
        # Escape quotes in names
        safe_name = tname.replace('"', "'")
        lines.append(f'    {tid}["{safe_name}"]')

    lines.append("")
    lines.append("    %% Queries (rounded)")
    for qid, qname in sorted(query_nodes):
        safe_name = qname.replace('"', "'")
        lines.append(f'    {qid}("{safe_name}")')

    lines.append("")
    lines.append("    %% Edges")
    for src, dst in sorted(set(edges)):
        lines.append(f"    {src} --> {dst}")

    lines.append("")
    lines.append("    %% Styling")
    lines.append("    classDef tableStyle fill:#e1f5fe,stroke:#01579b")
    lines.append("    classDef queryStyle fill:#f3e5f5,stroke:#4a148c")
    if table_nodes:
        table_ids = ",".join(tid for tid, _ in sorted(table_nodes))
        lines.append(f"    class {table_ids} tableStyle")
    if query_nodes:
        query_ids = ",".join(qid for qid, _ in sorted(query_nodes))
        lines.append(f"    class {query_ids} queryStyle")

    lines.append("```")
    lines.append("")

    # Dependency table
    lines.append("## Dependency Table")
    lines.append("")

    # Build reverse dependency map (who depends on this query)
    all_query_names = {q["name"] for q in queries}
    depended_on_by = {q["name"]: set() for q in queries}
    for q, a in zip(queries, analyses):
        for qref in a["references"]["queries"]:
            if qref in depended_on_by:
                depended_on_by[qref].add(q["name"])

    dep_rows = []
    for q, a in user_queries:
        refs = a["references"]
        tables_str = ", ".join(sorted(refs["tables"])) if refs["tables"] else "-"
        queries_str = ", ".join(sorted(refs["queries"])) if refs["queries"] else "-"
        dep_by = depended_on_by.get(q["name"], set())
        # Filter to user-visible dependents only
        dep_by_user = {d for d in dep_by if not d.startswith("~sq_")}
        dep_by_str = ", ".join(sorted(dep_by_user)) if dep_by_user else "-"

        dep_rows.append([
            q["name"],
            tables_str,
            queries_str,
            dep_by_str,
        ])

    lines.append(tabulate(
        dep_rows,
        headers=["Query Name", "Depends On (Tables)", "Depends On (Queries)", "Depended On By (Queries)"],
        tablefmt="pipe",
    ))
    lines.append("")

    # Orphan queries
    lines.append("## Orphan Queries")
    lines.append("")
    lines.append("> Queries that reference no known table or query. May be parameter-only or value-list queries.")
    lines.append("")

    orphans = []
    for q, a in user_queries:
        refs = a["references"]
        if not refs["tables"] and not refs["queries"]:
            orphans.append(q["name"])

    if orphans:
        for o in orphans:
            lines.append(f"- `{o}`")
    else:
        lines.append("None -- all user queries reference at least one known table or query.")
    lines.append("")

    # Hub tables
    lines.append("## Hub Tables")
    lines.append("")
    lines.append("> Tables referenced by the most queries (core data tables).")
    lines.append("")

    table_ref_counts = {}
    for q, a in zip(queries, analyses):
        for table in a["references"]["tables"]:
            table_ref_counts[table] = table_ref_counts.get(table, 0) + 1

    hub_rows = [[t, c] for t, c in sorted(table_ref_counts.items(), key=lambda x: -x[1])]
    if hub_rows:
        lines.append(tabulate(hub_rows, headers=["Table", "Referenced By N Queries"], tablefmt="pipe"))
    lines.append("")

    # Hub queries (most referenced by other queries)
    lines.append("## Hub Queries")
    lines.append("")
    lines.append("> Queries referenced by the most other queries (data pipeline nodes).")
    lines.append("")

    query_ref_counts = {}
    for qname, deps in depended_on_by.items():
        if deps:
            query_ref_counts[qname] = len(deps)

    hub_q_rows = [[q, c] for q, c in sorted(query_ref_counts.items(), key=lambda x: -x[1])]
    if hub_q_rows:
        lines.append(tabulate(hub_q_rows, headers=["Query", "Referenced By N Queries"], tablefmt="pipe"))
    else:
        lines.append("None -- no query is referenced by another user query.")
    lines.append("")

    return "\n".join(lines)


def main():
    """Main analysis pipeline."""
    print("Loading raw queries...", file=sys.stderr)
    queries = load_queries()
    print(f"Loaded {len(queries)} queries.", file=sys.stderr)

    # Build reference sets
    known_query_names = {q["name"] for q in queries}

    # Analyze each query
    analyses = []
    for q in queries:
        sql = q["sql"] or ""
        classification = classify_query_type(sql)
        references = extract_references(sql, KNOWN_TABLES, known_query_names)
        purpose = generate_purpose(
            q["name"],
            classification["base_type"],
            references["tables"],
            references["queries"],
            sql,
        )
        analyses.append({
            "classification": classification,
            "references": references,
            "purpose": purpose,
        })

    print("Analysis complete.", file=sys.stderr)

    # Generate documents
    overview_content = generate_overview(queries, analyses)
    dep_graph_content = generate_dependency_graph(queries, analyses)

    # Write files
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    overview_path = OUTPUT_DIR / "_overview.md"
    with open(overview_path, "w", encoding="utf-8") as f:
        f.write(overview_content)
    print(f"Wrote: {overview_path}", file=sys.stderr)

    dep_path = OUTPUT_DIR / "dependency_graph.md"
    with open(dep_path, "w", encoding="utf-8") as f:
        f.write(dep_graph_content)
    print(f"Wrote: {dep_path}", file=sys.stderr)

    # Summary
    user_count = sum(1 for q in queries if not q["name"].startswith("~sq_"))
    hidden_count = sum(1 for q in queries if q["name"].startswith("~sq_"))
    print(f"\nDone: {user_count} user queries, {hidden_count} hidden queries documented.", file=sys.stderr)


if __name__ == "__main__":
    main()
