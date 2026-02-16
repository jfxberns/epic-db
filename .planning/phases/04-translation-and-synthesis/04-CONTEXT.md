# Phase 4: Translation and Synthesis - Context

**Gathered:** 2026-02-16
**Status:** Ready for planning

<domain>
## Phase Boundary

Translate all Thai content to English and produce a single cross-referenced rebuild blueprint that stands alone as the complete specification for rebuilding the system. This phase consumes all outputs from Phases 1-3 (schema, queries, forms, reports, business logic) and produces the final deliverable. No new extraction or data gathering.

</domain>

<decisions>
## Implementation Decisions

### Translation conventions
- Translate Thai names to **business equivalents** (not literal) -- e.g., สินค้า → "products", not "goods"
- Maintain **Thai-to-English mapping** for every translated term -- the rebuild target is a bilingual app (English + Thai UI)
- Proper nouns (company name ริปรอย, brand names, person names): **transliterate** to romanized spelling only
- Already-English names in the database (frm_salesorder_fishingshop, qry stck subform2): **keep as-is**, do not normalize
- All translated names use **snake_case** convention everywhere
- Buddhist Era dates: **keep BE values as-is**, add a single explanation note (BE 2567 = CE 2024)
- Claude translates all terms using context and business domain knowledge -- no pre-locked term mappings

### Glossary format
- Three views of the same glossary in the document:
  1. **Domain-grouped sections** (Orders, Products, Inventory, Customers, Financial)
  2. **English alphabetical index**
  3. **Thai alphabetical index**
- Scope includes **everything**: database object names + UI labels + form captions + report headers + button text

### Blueprint organization
- Single comprehensive document with table of contents (not multi-file)
- Primary organization by **business domain**, with a component-type index/appendix for quick lookup
- Written for **both audiences**: executive summary and business process overview at top, technical detail (field types, SQL logic, form behavior) throughout
- Corrupt forms (frm_salesorder_fishingshop, frm_salesorder_retail, frm_stck_fishingshop, qry stck subform2): **document what can be inferred** from their subqueries and table relationships, flag as incomplete

### Rebuild assessment
- Effort estimates use **T-shirt sizes with hour ranges** (S = 2-4h, M = 4-8h, L = 1-2d, XL = 3-5d)
- **Include technology recommendations** for the rebuild stack
- Include a **phased rebuild plan** suggesting build sequence (foundation tables first, then core workflows, then reports)
- **Dedicated risk section** listing all risks, anti-patterns, and improvement opportunities found in the original system (not per-component)

### Cross-reference format
- **Both** Mermaid diagrams and markdown tables for component connections
- ER diagram: **layered approach** -- high-level overview diagram (tables + relationships) plus detailed per-domain diagrams showing fields
- **Named workflow documents** for each business process showing full component chains (e.g., "Shop Order Flow: form → query → tables → report")
- No special treatment for hub nodes -- all components shown equally

### Claude's Discretion
- Exact domain groupings for the business domain sections
- Which business processes warrant named workflow documentation
- How much can be inferred for the 4 corrupt forms
- Technology stack recommendations
- Internal document structure and section ordering
- Mermaid diagram styling and layout

</decisions>

<specifics>
## Specific Ideas

- The rebuild will be a bilingual app (English + Thai) -- every translated term needs its Thai original preserved for the bilingual UI
- Blueprint must be complete enough that a developer can rebuild without ever opening the .accdb file
- Three-view glossary (domain-grouped, English alpha, Thai alpha) for easy lookup from either language direction

</specifics>

<deferred>
## Deferred Ideas

None -- discussion stayed within phase scope

</deferred>

---

*Phase: 04-translation-and-synthesis*
*Context gathered: 2026-02-16*
