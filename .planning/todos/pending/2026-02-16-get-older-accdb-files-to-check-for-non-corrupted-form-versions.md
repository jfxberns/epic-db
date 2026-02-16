---
created: 2026-02-16T15:42:01.427Z
title: Get older accdb files to check for non-corrupted form versions
area: database
files:
  - data/epic_db.accdb
---

## Problem

The 4 corrupt forms in epic_db.accdb (`frm_salesorder_fishingshop`, `frm_salesorder_retail`, `frm_stck_fishingshop`, `qry stck subform2`) have corrupt VBA project streams that prevent SaveAsText export. These are the primary order entry forms — confirmed live and actively used (system subqueries reference them, reports filter by their open form fields, no alternative order forms exist).

The corruption is in the VBA container, not the form design itself. Older backup copies of the .accdb file may have pre-corruption versions of these forms where SaveAsText would succeed, giving us exact control layouts, event handlers, and data bindings instead of inference from subquery SQL.

## Solution

1. Ask the business if they have older backups of the Access database (.accdb or .mdb files) — could be on old machines, USB drives, cloud backups, or IT archives
2. Try SaveAsText export on each older copy's versions of the 4 corrupt forms
3. If any version exports cleanly, extract the full form definition (controls, layout, event handlers)
4. Compare with current inferences in BLUEPRINT.md to fill gaps (especially the LOW-confidence `qry stck subform2`)
