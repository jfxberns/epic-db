"""Assessment document generator for forms, reports, and navigation.

Reads SaveAsText exports via parse_saveastext.py, loads query data
from Plan 03-01, and generates:
  - assessment/forms/_overview.md       -- Form catalogue
  - assessment/forms/navigation.md      -- Form navigation workflow
  - assessment/reports/_overview.md     -- Report catalogue
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from tabulate import tabulate

from scripts.parse_saveastext import parse_form, parse_report

# Paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent
FORMS_DIR = PROJECT_ROOT / "windows" / "export" / "forms"
REPORTS_DIR = PROJECT_ROOT / "windows" / "export" / "reports"
QUERIES_JSON = PROJECT_ROOT / "assessment" / "queries" / "_raw_queries.json"
SUBQUERIES_DIR = PROJECT_ROOT / "windows" / "export" / "queries_sql" / "subqueries"

# Output paths
FORMS_OVERVIEW = PROJECT_ROOT / "assessment" / "forms" / "_overview.md"
FORMS_NAV = PROJECT_ROOT / "assessment" / "forms" / "navigation.md"
REPORTS_OVERVIEW = PROJECT_ROOT / "assessment" / "reports" / "_overview.md"

# Corrupt forms that could not be exported
CORRUPT_FORMS = [
    "frm_salesorder_fishingshop",
    "frm_salesorder_retail",
    "frm_stck_fishingshop",
    "qry stck subform2",
]


def load_queries() -> dict:
    """Load query data from raw JSON."""
    if not QUERIES_JSON.exists():
        return {}
    with open(QUERIES_JSON, "r", encoding="utf-8") as f:
        data = json.load(f)
    return {q["name"]: q for q in data}


def load_subquery_sql() -> dict[str, str]:
    """Load SQL from subquery files for corrupt form partial data."""
    sqls = {}
    if not SUBQUERIES_DIR.exists():
        return sqls
    for f in SUBQUERIES_DIR.glob("*.sql"):
        raw = f.read_bytes()
        for enc in ("utf-16-le", "utf-16", "utf-8-sig", "utf-8"):
            try:
                text = raw.decode(enc)
                sqls[f.stem] = text.strip()
                break
            except (UnicodeDecodeError, UnicodeError):
                continue
    return sqls


def get_record_source_display(rs: str) -> str:
    """Clean up record source for display."""
    if not rs:
        return "(none)"
    # If it's a simple table/query name, return as-is
    if not rs.upper().startswith("SELECT"):
        return rs.strip()
    # For SQL, return a truncated version
    clean = " ".join(rs.split())
    if len(clean) > 120:
        return clean[:117] + "..."
    return clean


def extract_record_source_refs(rs: str) -> list[str]:
    """Extract table/query names referenced in a RecordSource."""
    if not rs:
        return []
    # Match [table name] or bare table names after FROM/JOIN
    refs = re.findall(r"\[([^\]]+)\]", rs)
    # Also match after FROM/JOIN for unbracketed names
    for match in re.finditer(r"(?:FROM|JOIN)\s+(\w[\w\s]*?)(?:\s+(?:ON|WHERE|ORDER|GROUP|LEFT|RIGHT|INNER|AS|;)|\s*$)", rs, re.IGNORECASE):
        name = match.group(1).strip()
        if name and name not in refs:
            refs.append(name)
    # Remove duplicates preserving order, remove field names
    seen = set()
    result = []
    for r in refs:
        if r not in seen and not r.startswith("qry ") and "." in r:
            continue  # Skip field references like [table].[field]
        if r not in seen:
            seen.add(r)
            result.append(r)
    return result


def has_code_behind(parsed: dict) -> bool:
    """Check if a form/report has VBA code-behind."""
    return len(parsed.get("code_behind", "").strip()) > 0


def count_by_type(controls: list) -> dict[str, int]:
    """Count controls by type."""
    types = {}
    for c in controls:
        t = c.get("type", "Unknown")
        types[t] = types.get(t, 0) + 1
    return types


def get_events(controls: list) -> list[tuple[str, str, str]]:
    """Get all event handlers from controls. Returns [(control_name, event, value)]."""
    events = []
    for c in controls:
        name = c.get("properties", {}).get("Name", "?")
        for evt, val in c.get("events", {}).items():
            events.append((name, evt, val))
    return events


def get_subforms(controls: list) -> list[tuple[str, str]]:
    """Get subform references. Returns [(control_name, source_object)]."""
    subforms = []
    for c in controls:
        if c.get("type") == "Subform":
            name = c.get("properties", {}).get("Name", "?")
            source = c.get("properties", {}).get("SourceObject", "")
            subforms.append((name, source))
    return subforms


def get_data_bindings(controls: list) -> list[tuple[str, str, str]]:
    """Get controls with data bindings. Returns [(name, type, control_source)]."""
    bindings = []
    for c in controls:
        src = c.get("properties", {}).get("ControlSource", "")
        if src:
            name = c.get("properties", {}).get("Name", "?")
            ctype = c.get("type", "?")
            bindings.append((name, ctype, src))
    return bindings


def get_calculated_fields(controls: list) -> list[tuple[str, str]]:
    """Get controls with calculated expressions (ControlSource starting with '=')."""
    calcs = []
    for c in controls:
        src = c.get("properties", {}).get("ControlSource", "")
        if src.startswith("="):
            name = c.get("properties", {}).get("Name", "?")
            calcs.append((name, src))
    return calcs


# ── Form catalogue generation ────────────────────────────────────

def generate_forms_overview(forms: list[dict], queries: dict) -> str:
    """Generate the form catalogue markdown."""
    lines = []
    lines.append("# Form Catalogue")
    lines.append("")
    lines.append(f"**Generated:** 2026-02-16")
    lines.append(f"**Source:** windows/export/forms/ via SaveAsText exports")
    lines.append(f"**Generator:** scripts/extract_forms_reports.py (rerun to regenerate)")
    lines.append("")

    # Summary
    forms_with_code = sum(1 for f in forms if has_code_behind(f))
    forms_with_subforms = sum(1 for f in forms if get_subforms(f.get("all_controls", [])))
    total_controls = sum(len(f.get("all_controls", [])) for f in forms)

    lines.append("## Summary")
    lines.append("")
    lines.append(f"- **Exported forms:** {len(forms)}")
    lines.append(f"- **Corrupt/unexportable forms:** {len(CORRUPT_FORMS)} (see Gaps section)")
    lines.append(f"- **Forms with code-behind:** {forms_with_code}")
    lines.append(f"- **Forms with subforms:** {forms_with_subforms}")
    lines.append(f"- **Total controls across all forms:** {total_controls}")
    lines.append("")

    # Catalogue table
    lines.append("## Form Catalogue")
    lines.append("")
    table_data = []
    for f in forms:
        name = f.get("filename", "").replace(".txt", "")
        props = f.get("properties", {})
        rs = get_record_source_display(props.get("RecordSource", ""))
        ctrls = f.get("all_controls", [])
        ctrl_count = len(ctrls)
        has_code = "Yes" if has_code_behind(f) else "No"
        has_sf = "Yes" if get_subforms(ctrls) else "No"
        events = get_events(ctrls)
        key_events = ", ".join(sorted(set(e[1] for e in events)))[:60] if events else "-"

        table_data.append([
            name,
            rs[:80] + ("..." if len(rs) > 80 else ""),
            ctrl_count,
            has_code,
            has_sf,
            key_events,
        ])

    headers = ["Name", "Record Source", "Controls", "Code-Behind?", "Subforms?", "Key Events"]
    lines.append(tabulate(table_data, headers=headers, tablefmt="pipe"))
    lines.append("")

    # Per-form detail sections
    lines.append("## Form Details")
    lines.append("")

    for f in forms:
        name = f.get("filename", "").replace(".txt", "")
        props = f.get("properties", {})
        rs = props.get("RecordSource", "")
        ctrls = f.get("all_controls", [])

        lines.append(f"### {name}")
        lines.append("")

        # Purpose (inferred)
        purpose = _infer_form_purpose(name, rs, ctrls)
        lines.append(f"**Purpose:** {purpose}")
        lines.append("")

        # Record Source
        lines.append(f"**Record Source:** `{get_record_source_display(rs)}`")
        lines.append("")

        # Control summary
        type_counts = count_by_type(ctrls)
        if type_counts:
            lines.append("**Controls:**")
            lines.append("")
            ctrl_table = [[t, c] for t, c in sorted(type_counts.items())]
            lines.append(tabulate(ctrl_table, headers=["Type", "Count"], tablefmt="pipe"))
            lines.append("")

        # Data bindings
        bindings = get_data_bindings(ctrls)
        if bindings:
            lines.append("**Data Bindings:**")
            lines.append("")
            bind_table = [[n, t, s] for n, t, s in bindings]
            lines.append(tabulate(bind_table, headers=["Name", "Type", "Control Source"], tablefmt="pipe"))
            lines.append("")

        # Events
        events = get_events(ctrls)
        if events:
            lines.append("**Event Handlers:**")
            lines.append("")
            evt_table = [[n, e, v] for n, e, v in events]
            lines.append(tabulate(evt_table, headers=["Control", "Event", "Handler"], tablefmt="pipe"))
            lines.append("")

        # Subforms
        subforms = get_subforms(ctrls)
        if subforms:
            lines.append("**Subforms:**")
            lines.append("")
            for sf_name, sf_source in subforms:
                lines.append(f"- **{sf_name}** -> `{sf_source}`")
            lines.append("")

        # Code-behind
        code = f.get("code_behind", "").strip()
        if code:
            procs = f.get("vba_procedures", [])
            lines.append("**VBA Code-Behind:**")
            lines.append("")
            if procs:
                lines.append(f"Procedures: {len(procs)}")
                for p in procs:
                    lines.append(f"- `{p['scope']} {p['kind']} {p['name']}` (control: {p['control']}, event: {p['event']})")
                lines.append("")
            lines.append("```vba")
            lines.append(code)
            lines.append("```")
            lines.append("")

        lines.append("---")
        lines.append("")

    # Corrupt forms gap documentation
    lines.append("## Gaps: Corrupt VBA Forms (Not Exportable)")
    lines.append("")
    lines.append("The following 4 forms could not be exported due to a corrupt VBA project in the database.")
    lines.append("Partial data is available from their associated subquery SQL files.")
    lines.append("")

    subquery_sqls = load_subquery_sql()
    for corrupt_name in CORRUPT_FORMS:
        lines.append(f"### {corrupt_name}")
        lines.append("")
        lines.append(f"**Status:** Export failed -- corrupt VBA project")
        lines.append("")

        # Find related subqueries
        related_sqs = []
        for sq_name, sq_sql in subquery_sqls.items():
            if corrupt_name.replace(" ", "_") in sq_name or corrupt_name.replace("_", " ") in sq_name:
                related_sqs.append((sq_name, sq_sql))

        if related_sqs:
            lines.append("**Related Subquery SQL (partial reconstruction data):**")
            lines.append("")
            for sq_name, sq_sql in related_sqs:
                lines.append(f"**`{sq_name}`:**")
                lines.append("```sql")
                lines.append(sq_sql)
                lines.append("```")
                lines.append("")
        else:
            lines.append("No related subquery SQL found.")
            lines.append("")

        lines.append("---")
        lines.append("")

    return "\n".join(lines)


def _infer_form_purpose(name: str, record_source: str, controls: list) -> str:
    """Infer form purpose from name, record source, and controls."""
    name_lower = name.lower()

    # Known form names
    if "สต็อค" in name or "stck" in name_lower:
        return "Stock/inventory tracking form -- displays current stock levels calculated from receipts, issues, and sales"
    if "คะแนน" in name and "คงเหลือ" in name:
        return "Loyalty points remaining -- displays accumulated points after redemptions for each customer"
    if "คะแนน" in name and "subform" in name_lower:
        return "Customer loyalty points subform -- shows total points per customer (embedded in order forms)"
    if "ออเดอร์" in name and "Subform" in name:
        return "Order line items subform -- shows products within each order with pricing and quantities"
    if "ใบรับเข้า" in name and "Subform" in name:
        return "Goods receipt line items subform -- shows products received in each receipt document"
    if "ใบเบิก" in name and "Subform" in name:
        return "Goods issue line items subform -- shows products issued/withdrawn in each issue document"
    if "เลขที่ออเดอร์" in name or "ออเดอร์" in name and "ชื่อร้าน" in name:
        return "Order lookup form -- search for orders by shop name with order details"
    if "salesorder" in name_lower and "fishingshop" in name_lower:
        return "Sales order entry form for fishing shop channel (CORRUPT -- not exported)"
    if "salesorder" in name_lower and "retail" in name_lower:
        return "Sales order entry form for retail customer channel (CORRUPT -- not exported)"

    # Generic inference from record source
    if record_source:
        return f"Data form bound to: {get_record_source_display(record_source)[:80]}"
    return "Purpose unclear -- no record source"


# ── Navigation generation ────────────────────────────────────────

def generate_navigation(forms: list[dict]) -> str:
    """Generate the form navigation workflow document."""
    lines = []
    lines.append("# Form Navigation Workflow")
    lines.append("")
    lines.append(f"**Generated:** 2026-02-16")
    lines.append(f"**Source:** windows/export/forms/ via SaveAsText exports")
    lines.append("")

    lines.append("## Overview")
    lines.append("")
    lines.append("This document maps the navigation relationships between forms, showing")
    lines.append("which forms embed which subforms. Since no main navigation form (menu)")
    lines.append("was found in the exported set, relationships are derived from subform")
    lines.append("references and query data source connections.")
    lines.append("")
    lines.append("**Note:** The 4 corrupt VBA forms (frm_salesorder_fishingshop,")
    lines.append("frm_salesorder_retail, frm_stck_fishingshop, qry stck subform2) would")
    lines.append("likely have been the primary data entry forms. Their subform SQL")
    lines.append("references are documented from the exported subquery files.")
    lines.append("")

    # Build subform relationships
    lines.append("## Subform Relationships")
    lines.append("")

    relationships = []
    for f in forms:
        name = f.get("filename", "").replace(".txt", "")
        ctrls = f.get("all_controls", [])
        subforms = get_subforms(ctrls)
        for sf_name, sf_source in subforms:
            relationships.append((name, sf_name, sf_source))

    if relationships:
        table_data = [[parent, sf, target] for parent, sf, target in relationships]
        lines.append(tabulate(table_data, headers=["Parent Form", "Subform Control", "Source Object"], tablefmt="pipe"))
        lines.append("")
    else:
        lines.append("No subform relationships found in the 7 exported forms.")
        lines.append("")

    # Build inferred navigation from corrupt forms via subquery names
    lines.append("## Inferred Navigation from Corrupt Forms")
    lines.append("")
    lines.append("The subquery naming convention `~sq_c{parent}~sq_c{child}` reveals the")
    lines.append("subform nesting structure of the corrupt forms:")
    lines.append("")

    subquery_sqls = load_subquery_sql()
    corrupt_relationships = []
    for sq_name in sorted(subquery_sqls.keys()):
        if sq_name.startswith("_tilde_sq_c"):
            # Parse parent~child from name
            # Format: _tilde_sq_c{parent}_tilde_sq_c{child}
            parts = sq_name.replace("_tilde_sq_c", "", 1).split("_tilde_sq_c")
            if len(parts) == 2:
                parent = parts[0]
                child = parts[1]
                corrupt_relationships.append((parent, child))

    if corrupt_relationships:
        table_data = [[p, c] for p, c in corrupt_relationships]
        lines.append(tabulate(table_data, headers=["Parent Form/Query", "Child Subform"], tablefmt="pipe"))
        lines.append("")

    # Build combined navigation tree
    lines.append("## Combined Navigation Tree")
    lines.append("")
    lines.append("Based on both exported subform references and subquery naming analysis:")
    lines.append("")
    lines.append("```")

    # Build tree structure
    all_relationships = []
    for parent, sf, target in relationships:
        all_relationships.append((parent, target))
    for parent, child in corrupt_relationships:
        all_relationships.append((parent, child))

    # Find roots (parents that are not children)
    children_set = {c for _, c in all_relationships}
    parents_set = {p for p, _ in all_relationships}
    roots = parents_set - children_set

    def _print_tree(node: str, indent: int, visited: set) -> list[str]:
        tree_lines = []
        prefix = "  " * indent + ("|- " if indent > 0 else "")
        tree_lines.append(f"{prefix}{node}")
        if node in visited:
            return tree_lines
        visited.add(node)
        children = [c for p, c in all_relationships if p == node]
        for child in children:
            tree_lines.extend(_print_tree(child, indent + 1, visited))
        return tree_lines

    visited = set()
    for root in sorted(roots):
        tree_lines = _print_tree(root, 0, visited)
        for tl in tree_lines:
            lines.append(tl)

    # Show orphan forms (not in any relationship)
    all_form_names = {f.get("filename", "").replace(".txt", "") for f in forms}
    all_in_nav = parents_set | children_set
    orphans = all_form_names - all_in_nav
    if orphans:
        lines.append("")
        lines.append("(standalone forms -- not embedded in any navigation):")
        for o in sorted(orphans):
            lines.append(f"  {o}")

    lines.append("```")
    lines.append("")

    # Mermaid diagram
    lines.append("## Navigation Diagram")
    lines.append("")
    lines.append("```mermaid")
    lines.append("graph TD")

    # Generate node IDs
    node_ids = {}
    counter = 0
    for p, c in all_relationships:
        for n in (p, c):
            if n not in node_ids:
                node_ids[n] = f"N{counter}"
                counter += 1

    # Add orphans
    for o in orphans:
        if o not in node_ids:
            node_ids[o] = f"N{counter}"
            counter += 1

    # Node definitions
    for name, nid in sorted(node_ids.items(), key=lambda x: x[1]):
        # Mark corrupt forms
        if any(name.replace("_", " ") == c.replace("_", " ") or name == c for c in CORRUPT_FORMS):
            lines.append(f'    {nid}["{name}<br/>(CORRUPT)"]')
        elif name in orphans:
            lines.append(f'    {nid}["{name}<br/>(standalone)"]')
        else:
            lines.append(f'    {nid}["{name}"]')

    # Edges
    for p, c in all_relationships:
        if p in node_ids and c in node_ids:
            lines.append(f"    {node_ids[p]} --> {node_ids[c]}")

    # Style corrupt forms
    corrupt_ids = []
    for name, nid in node_ids.items():
        if any(name.replace("_", " ") == c.replace("_", " ") or name == c for c in CORRUPT_FORMS):
            corrupt_ids.append(nid)
    if corrupt_ids:
        lines.append(f"    style {','.join(corrupt_ids)} fill:#ff9999,stroke:#cc0000")

    lines.append("```")
    lines.append("")

    return "\n".join(lines)


# ── Report catalogue generation ──────────────────────────────────

def generate_reports_overview(reports: list[dict], queries: dict) -> str:
    """Generate the report catalogue markdown."""
    lines = []
    lines.append("# Report Catalogue")
    lines.append("")
    lines.append(f"**Generated:** 2026-02-16")
    lines.append(f"**Source:** windows/export/reports/ via SaveAsText exports")
    lines.append(f"**Generator:** scripts/extract_forms_reports.py (rerun to regenerate)")
    lines.append("")

    # Summary
    reports_with_code = sum(1 for r in reports if has_code_behind(r))
    reports_with_subreports = sum(1 for r in reports if get_subforms(r.get("all_controls", [])))
    total_controls = sum(len(r.get("all_controls", [])) for r in reports)

    lines.append("## Summary")
    lines.append("")
    lines.append(f"- **Exported reports:** {len(reports)}")
    lines.append(f"- **Reports with code-behind:** {reports_with_code}")
    lines.append(f"- **Reports with subreports:** {reports_with_subreports}")
    lines.append(f"- **Total controls across all reports:** {total_controls}")
    lines.append("")

    # Catalogue table
    lines.append("## Report Catalogue")
    lines.append("")
    table_data = []
    for r in reports:
        name = r.get("filename", "").replace(".txt", "")
        props = r.get("properties", {})
        rs = get_record_source_display(props.get("RecordSource", ""))
        ctrls = r.get("all_controls", [])
        ctrl_count = len(ctrls)
        has_code = "Yes" if has_code_behind(r) else "No"
        output_type = _infer_report_type(name, rs)

        table_data.append([
            name,
            rs[:80] + ("..." if len(rs) > 80 else ""),
            ctrl_count,
            has_code,
            output_type,
        ])

    headers = ["Name", "Record Source", "Controls", "Code-Behind?", "Output Type"]
    lines.append(tabulate(table_data, headers=headers, tablefmt="pipe"))
    lines.append("")

    # Per-report details
    lines.append("## Report Details")
    lines.append("")

    for r in reports:
        name = r.get("filename", "").replace(".txt", "")
        props = r.get("properties", {})
        rs = props.get("RecordSource", "")
        ctrls = r.get("all_controls", [])

        lines.append(f"### {name}")
        lines.append("")

        # Purpose
        purpose = _infer_report_purpose(name, rs)
        lines.append(f"**Purpose:** {purpose}")
        lines.append("")

        # Record Source
        lines.append(f"**Record Source:** `{get_record_source_display(rs)}`")
        lines.append("")

        # Key fields displayed
        bindings = get_data_bindings(ctrls)
        if bindings:
            lines.append("**Key Fields Displayed:**")
            lines.append("")
            bind_table = [[n, t, s] for n, t, s in bindings]
            lines.append(tabulate(bind_table, headers=["Name", "Type", "Control Source"], tablefmt="pipe"))
            lines.append("")

        # Calculated fields
        calcs = get_calculated_fields(ctrls)
        if calcs:
            lines.append("**Calculated Fields:**")
            lines.append("")
            for calc_name, expr in calcs:
                lines.append(f"- **{calc_name}:** `{expr}`")
            lines.append("")

        # Grouping/sorting
        sections = r.get("sections", [])
        group_sections = [s for s in sections if "GroupHeader" in s.get("name", "") or "GroupFooter" in s.get("name", "")]
        if group_sections:
            lines.append("**Grouping:**")
            lines.append("")
            for gs in group_sections:
                lines.append(f"- Section: {gs['name']}")
            lines.append("")

        # Subreports
        subforms = get_subforms(ctrls)
        if subforms:
            lines.append("**Subreports:**")
            lines.append("")
            for sf_name, sf_source in subforms:
                lines.append(f"- **{sf_name}** -> `{sf_source}`")
            lines.append("")

        lines.append("---")
        lines.append("")

    return "\n".join(lines)


def _infer_report_type(name: str, record_source: str) -> str:
    """Infer report output type from name and record source."""
    name_lower = name.lower()
    if "ภาษี" in name or "inv" in name_lower:
        return "Tax/invoice report"
    if "ที่อยู่" in name:
        return "Address label/list"
    if "เบิก" in name or "ใบเบิก" in name:
        return "Goods issue document"
    if "ใบรับเข้า" in name:
        return "Goods receipt document"
    if "พัสดุ" in name:
        return "Shipping notification"
    if "โอนเงิน" in name:
        return "Bank transfer report"
    if "rpt" in name_lower:
        return "Print report"
    if "subreport" in name_lower:
        return "Subreport (embedded)"
    return "Report"


def _infer_report_purpose(name: str, record_source: str) -> str:
    """Infer report purpose."""
    if "ภาษีขาย" in name and "inv" in name.lower():
        return "Sales tax verification report sorted by invoice number -- cross-references order details with bank transfers and invoice data"
    if "รายงานภาษีขาย" in name:
        return "Sales tax report -- lists order details with bank transfer info, dates, and amounts for tax reporting"
    if "ปรินท์ใบเบิกสินค้า" in name:
        return "Print goods issue document -- shows items in a specific withdrawal with product details"
    if "rptดูเลขทีใบเบิก" in name:
        return "View goods issue numbers -- lists all withdrawal documents with dates and destinations"
    if "rptทำที่อยู่เบิกสินค้า" in name:
        return "Goods issue address labels -- formats shipping addresses for goods withdrawal orders"
    if "rptรายละเอียดการโอนเงิน" in name:
        return "Bank transfer details per order -- shows payment transfer information for each order"
    if "พัสดุ" in name and "ร้านค้า" in name:
        return "Shop shipping notification -- provides tracking and address info for shop channel orders"
    if "พัสดุ" in name and "ปลีก" in name:
        return "Retail customer shipping notification -- provides tracking and address info for retail orders"
    if "ปริ้นท์ที่อยู่ลูกค้าปลีก" in name:
        return "Print retail customer addresses -- formatted address labels for retail order shipments"
    if "ใบรับเข้าสินค้า" in name:
        return "Goods receipt details -- shows items received in each goods receipt document"
    if "เจาะจงหมายเลขออเดอร์" in name:
        return "Order-specific detail subreport -- shows line items for a particular order number"

    if record_source:
        return f"Report bound to: {get_record_source_display(record_source)[:80]}"
    return "Purpose unclear"


# ── Main ─────────────────────────────────────────────────────────

def main():
    """Generate all assessment documents."""
    print("Loading query data...")
    queries = load_queries()
    print(f"  Loaded {len(queries)} queries")

    print("Parsing forms...")
    forms = []
    for f in sorted(FORMS_DIR.glob("*.txt")):
        parsed = parse_form(f)
        forms.append(parsed)
        print(f"  {f.stem}: {len(parsed.get('all_controls', []))} controls")

    print("Parsing reports...")
    reports = []
    for f in sorted(REPORTS_DIR.glob("*.txt")):
        parsed = parse_report(f)
        reports.append(parsed)
        print(f"  {f.stem}: {len(parsed.get('all_controls', []))} controls")

    # Create output directories
    FORMS_OVERVIEW.parent.mkdir(parents=True, exist_ok=True)
    REPORTS_OVERVIEW.parent.mkdir(parents=True, exist_ok=True)

    # Generate form catalogue
    print("Generating form catalogue...")
    forms_md = generate_forms_overview(forms, queries)
    FORMS_OVERVIEW.write_text(forms_md, encoding="utf-8")
    print(f"  Written: {FORMS_OVERVIEW}")

    # Generate navigation
    print("Generating navigation workflow...")
    nav_md = generate_navigation(forms)
    FORMS_NAV.write_text(nav_md, encoding="utf-8")
    print(f"  Written: {FORMS_NAV}")

    # Generate report catalogue
    print("Generating report catalogue...")
    reports_md = generate_reports_overview(reports, queries)
    REPORTS_OVERVIEW.write_text(reports_md, encoding="utf-8")
    print(f"  Written: {REPORTS_OVERVIEW}")

    print("Done!")


if __name__ == "__main__":
    main()
