# Epic DB Object Inventory

**Generated:** 2026-02-14
**Source:** data/epic_db.accdb (Access 2010 format)
**Generator:** scripts/inventory.py (rerun to regenerate)

## Summary

| Object Type   |   Count |
|:--------------|--------:|
| Tables        |      10 |
| Queries       |      32 |
| Forms         |      17 |
| Reports       |      25 |
| Macros        |       0 |
| Modules       |       0 |

**Total: 84 objects**

Additionally: 12 relationship(s) detected

## Tables (10)

| Name                   |   Row Count |   Columns |
|:-----------------------|------------:|----------:|
| ข้อมูลร้านค้า          |         735 |        25 |
| ข้อมูลสมาชิก           |        2150 |        16 |
| คะแนนที่ลูกค้าใช้ไป    |           0 |         7 |
| รายละเอียดออเดอร์      |         509 |        16 |
| สินค้า                 |         186 |         9 |
| สินค้าในแต่ละออเดอร์   |        7073 |         4 |
| สินค้าในแต่ละใบรับเข้า |         514 |         5 |
| สินค้าในแต่ละใบเบิก    |       15293 |         5 |
| หัวใบรับเข้า           |         165 |         9 |
| หัวใบเบิก              |        3391 |        10 |

## Queries (32)

| Name                                     | Type   |
|:-----------------------------------------|:-------|
| "ซอง";"ตัว";"เม็ด"                       | SELECT |
| qry คะแนนคงเหลือหลังจากใช้แล้ว           | SELECT |
| qry คะแนนรวมลูกค้าแต่ละคน                | SELECT |
| qry จำนวนที่ขายของสินค้าแต่ละตัว         | SELECT |
| qry จำนวนรับเข้ารวม ของสินค้าทุกตัว      | SELECT |
| qry จำนวนเบิกรวม ของสินค้าทุกตัว         | SELECT |
| qry ดูยอดซื้อร้านค้าแต่ละเจ้า            | SELECT |
| qry ที่อยู่เจาะจงโดยวันที่ (ปลีก)        | SELECT |
| qry ที่อยู่เจาะจงโดยวันที่ (ร้านค้า)     | SELECT |
| qry ยอดขายร้านค้า                        | SELECT |
| qry ยอดขายลูกค้าปลีก                     | SELECT |
| qry ยอดซื้อร้านค้าทั้งปี                 | SELECT |
| qry รายละเอียดการโอนเงินร้านค้า          | SELECT |
| qry รายละเอียดการโอนแต่ละออเดอร์ปลีก     | SELECT |
| qry วันที่และเวลาโอนเงินเรียงตามใบกำกับ  | SELECT |
| qry สต็อคสินค้า                          | SELECT |
| qry สต็อคสินค้าในแต่ละออเดอร์ปลีก        | SELECT |
| qry สินค้าในแต่ละออเดอร์ปลีก             | SELECT |
| qry สินค้าในแต่ละออเดอร์ร้านค้า          | SELECT |
| qry เจาะจงหมายเลขออเดอร์ปลีก             | SELECT |
| qry เจาะจงหมายเลขออเดอร์ร้านค้า          | SELECT |
| qry เจาะจงเลขที่ใบรับเข้า                | SELECT |
| qry เจาะจงเลขที่ใบเบิก                   | SELECT |
| qry_ร้านค้ารอโอน                         | SELECT |
| qry_สินค้าที่ขายดีย้อนหลัง 3 เดือน       | SELECT |
| qryกำหนดเลขที่inv                        | SELECT |
| qryยอดเงินร้านค้า                        | SELECT |
| qryรายงานสินค้าและวัตุดิบ                | UNION  |
| qryลงยอดร้านค้า                          | SELECT |
| qryใส่เลขที่ใบกำกับ                      | SELECT |
| จำนวนที่ขายของสินค้าแต่ละตัว(ระบุวันที่) | SELECT |
| ดูจำนวนรวมสินค้าที่สั่งหลายออเดอร์รวมกัน | SELECT |

> Query type classification source: MSysObjects Flags (MSysQueries not accessible)
> Note: MSysQueries system table was not accessible. Query types are inferred from MSysObjects Flags field. Flags=0 is classified as SELECT by convention, but some queries (especially those with names suggesting UPDATE/INSERT operations) may have different actual types. Precise classification requires MSysQueries or Windows with Access.

## Forms (17)

| Name                                    |
|:----------------------------------------|
| frm รับเข้าสินค้า                       |
| frm เบิกสินค้า                          |
| frm_salesorder_fishingshop              |
| frm_salesorder_retail                   |
| frm_stck_fishingshop                    |
| frm_สต็อคสินค้า                         |
| frmข้อมูลสมาชิก                         |
| qry stck subform2                       |
| qry คะแนนรวมลูกค้าแต่ละคน subform       |
| qry สินค้าในแต่ละออเดอร์ Subform        |
| qry สินค้าในแต่ละออเดอร์ Subform1       |
| qry สินค้าในแต่ละออเดอร์ร้านค้า subform |
| คะแนนคงเหลือหลังจากใช้แล้ว              |
| สินค้าในแต่ละใบรับเข้า Subform          |
| สินค้าในแต่ละใบเบิก Subform             |
| หน้าหลัก                                |
| หาเลขที่ออเดอร์ถ้ารู้ชื่อร้าน           |

> Note: Form content (layouts, controls, VBA code-behind) requires Windows with Microsoft Access for extraction via `Application.SaveAsText`.

## Reports (25)

| Name                                         |
|:---------------------------------------------|
| Copy of ใบกำกับภาษีร้านค้า                   |
| pdf แจ้งยอด                                  |
| qry เจาะจงหมายเลขออเดอร์ subreport           |
| rptดูเลขทีใบเบิก                             |
| rptทำที่อยู่เบิกสินค้า                       |
| rptรายละเอียดการโอนเงินของแต่ละเลขที่ออเดอร์ |
| ข้อมูลสำหรับแจ้งเลขพัสดุร้านค้า              |
| ข้อมูลสำหรับแจ้งเลขพัสดุลูกค้าปลีก           |
| ตรวจภาษีขาย                                  |
| ตรวจภาษีขายเรียงตามเลขinv                    |
| บิลร้านค้า                                   |
| บิลลูกค้าปลีก                                |
| ปรินท์ใบเบิกสินค้า                           |
| ปริ้นท์ที่อยู่                               |
| ปริ้นท์ที่อยู่ลูกค้าปลีก                     |
| รายงานภาษีขาย                                |
| รายละเอียดการโอน                             |
| รายละเอียดใบรับเข้าสินค้า                    |
| ใบกำกับภาษีร้านค้า                           |
| ใบกำกับภาษีร้านค้า(สำเนา)                    |
| ใบกำกับภาษีลูกค้าปลีก                        |
| ใบกำกับภาษีลูกค้าปลีก(สำเนา)                 |
| ใบจัดสินค้าร้านค้า                           |
| ใบตรวจบิลร้านค้า                             |
| ใบส่งของร้านค้า                              |

> Note: Report content (layouts, data sources, grouping/sorting) requires Windows with Microsoft Access for extraction via `Application.SaveAsText`.

## Modules (0)

*None found*

## Macros (0)

*None found*

## Relationships (12)

The following table-to-table relationships were detected in MSysObjects (Type=8). The Name field contains concatenated table names indicating a relationship between two tables.

| Relationship (Table Pair)                         |
|:--------------------------------------------------|
| qry คะแนนคงเหลือหลังจากใช้แล้รายละเอียดออเดอร์    |
| qry คะแนนรวมลูกค้าแต่ละคนqry สินค้าในแต่ละออเดอร์ |
| qry สต็อคสินค้าสินค้า                             |
| ข้อมูลร้านค้ารายละเอียดออเดอร์                    |
| ข้อมูลสมาชิกรายละเอียดออเดอร์                     |
| จำนวนที่ขายของสินค้าแต่ละตัวสินค้า                |
| รายละเอียดออเดอร์สินค้าในแต่ละออเดอร์             |
| สินค้าสินค้าในแต่ละออเดอร์                        |
| สินค้าสินค้าในแต่ละใบรับเข้า                      |
| สินค้าสินค้าในแต่ละใบเบิก                         |
| หัวใบรับเข้าสินค้าในแต่ละใบรับเข้า                |
| หัวใบเบิกสินค้าในแต่ละใบเบิก                      |

## Windows Assessment

**Windows environment IS NEEDED** for full content extraction.

This database contains 17 forms, 25 reports whose content (layouts, controls, VBA code, definitions) cannot be extracted on macOS.

**What macOS can do:** List names for all object types (shown above), extract table schemas and data, enumerate query names and types.

**What requires Windows:** Form layouts and controls, report definitions and data sources, VBA module code, macro step definitions. These are stored as binary blobs requiring Microsoft Access COM Object Model (`Application.SaveAsText`).

**Recommendation:** Proceed with macOS for Phase 1 (inventory) and Phase 2 (schema/query extraction). Set up a Windows environment with Microsoft Access for Phase 3 (Logic + Interface extraction).

## Cross-Validation

- Tables in MSysObjects but NOT in catalog (system/internal, f_* prefix): 2 entries (expected -- these are internal Access tables)
- Catalog vs MSysObjects user tables: MATCH
- All tables parsed successfully (no row_count=-1 errors)
- Total object count: 84 (matches MSysObjects user object count)
