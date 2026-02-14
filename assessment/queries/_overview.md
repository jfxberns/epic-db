# Query Assessment Overview

**Generated:** 2026-02-15
**Source:** data/epic_db.accdb via Jackcess 4.0.8 / JPype1
**Generator:** scripts/analyze_queries.py (rerun to regenerate)

## Summary

- **Total queries:** 62 (33 user-visible, 29 hidden system)

| Type   |   Count |
|:-------|--------:|
| SELECT |      61 |
| UNION  |       1 |

- **Parameterized queries (PARAMETERS keyword):** 7
- **Queries referencing form controls:** 10
- **Hidden system subqueries:** 29

## Query Catalogue

> Query type classification based on actual SQL content (not MSysObjects flags).

| Name                                     | Type   | Tables Referenced                                                                            | Queries Referenced                                                    | Form Refs   | Purpose                                                                                                                                                |
|:-----------------------------------------|:-------|:---------------------------------------------------------------------------------------------|:----------------------------------------------------------------------|:------------|:-------------------------------------------------------------------------------------------------------------------------------------------------------|
| "ซอง";"ตัว";"เม็ด"                       | SELECT | สินค้า                                                                                       | -                                                                     | No          | Value list for product unit types (pack/piece/bead) -- from สินค้า                                                                                     |
| qry คะแนนคงเหลือหลังจากใช้แล้ว           | SELECT | ข้อมูลสมาชิก                                                                                 | qry คะแนนรวมลูกค้าแต่ละคน                                             | Yes         | Calculate remaining loyalty points after redemptions -- from ข้อมูลสมาชิก                                                                              |
| qry คะแนนรวมลูกค้าแต่ละคน                | SELECT | -                                                                                            | qry สินค้าในแต่ละออเดอร์ปลีก                                          | No          | Sum total loyalty points per customer -- from calculated                                                                                               |
| qry จำนวนที่ขายของสินค้าแต่ละตัว         | SELECT | รายละเอียดออเดอร์, สินค้าในแต่ละออเดอร์                                                      | -                                                                     | No          | Total quantity sold per product across all orders -- from รายละเอียดออเดอร์, สินค้าในแต่ละออเดอร์                                                      |
| qry จำนวนเบิกรวม ของสินค้าทุกตัว         | SELECT | สินค้า, สินค้าในแต่ละใบเบิก                                                                  | -                                                                     | No          | Total quantity issued (goods withdrawal) per product -- from สินค้า, สินค้าในแต่ละใบเบิก                                                               |
| qry จำนวนรับเข้ารวม ของสินค้าทุกตัว      | SELECT | สินค้า, สินค้าในแต่ละใบรับเข้า                                                               | -                                                                     | No          | Total quantity received (goods receipt) per product -- from สินค้า, สินค้าในแต่ละใบรับเข้า                                                             |
| qry เจาะจงเลขที่ใบเบิก                   | SELECT | สินค้าในแต่ละใบเบิก, หัวใบเบิก                                                               | -                                                                     | Yes         | Look up specific goods issue -- from สินค้าในแต่ละใบเบิก, หัวใบเบิก                                                                                    |
| qry เจาะจงเลขที่ใบรับเข้า                | SELECT | สินค้าในแต่ละใบรับเข้า, หัวใบรับเข้า                                                         | -                                                                     | Yes         | Look up specific goods receipt -- from สินค้าในแต่ละใบรับเข้า, หัวใบรับเข้า                                                                            |
| qry เจาะจงหมายเลขออเดอร์ปลีก             | SELECT | ข้อมูลสมาชิก, สินค้าในแต่ละออเดอร์                                                           | -                                                                     | Yes         | Look up retail order by order number -- from ข้อมูลสมาชิก, สินค้าในแต่ละออเดอร์                                                                        |
| qry เจาะจงหมายเลขออเดอร์ร้านค้า          | SELECT | รายละเอียดออเดอร์, สินค้า, สินค้าในแต่ละออเดอร์                                              | -                                                                     | Yes         | Look up shop order by order number -- from รายละเอียดออเดอร์, สินค้า, สินค้าในแต่ละออเดอร์                                                             |
| qry ดูยอดซื้อร้านค้าแต่ละเจ้า            | SELECT | รายละเอียดออเดอร์                                                                            | qry สินค้าในแต่ละออเดอร์ร้านค้า                                       | No          | View purchase totals per shop vendor -- from รายละเอียดออเดอร์                                                                                         |
| qry ที่อยู่เจาะจงโดยวันที่ (ปลีก)        | SELECT | ข้อมูลสมาชิก, รายละเอียดออเดอร์                                                              | -                                                                     | No          | Retail customer addresses filtered by date range -- from ข้อมูลสมาชิก, รายละเอียดออเดอร์                                                               |
| qry ที่อยู่เจาะจงโดยวันที่ (ร้านค้า)     | SELECT | ข้อมูลสมาชิก, รายละเอียดออเดอร์                                                              | -                                                                     | No          | Shop addresses filtered by date range -- from ข้อมูลสมาชิก, รายละเอียดออเดอร์                                                                          |
| qry ยอดขายร้านค้า                        | SELECT | -                                                                                            | qry สินค้าในแต่ละออเดอร์ร้านค้า                                       | No          | Shop sales totals with pricing and discounts -- from calculated                                                                                        |
| qry ยอดขายลูกค้าปลีก                     | SELECT | รายละเอียดออเดอร์                                                                            | qry สินค้าในแต่ละออเดอร์ปลีก                                          | No          | Retail customer sales totals -- from รายละเอียดออเดอร์                                                                                                 |
| qry ยอดซื้อร้านค้าทั้งปี                 | SELECT | รายละเอียดออเดอร์                                                                            | qry สินค้าในแต่ละออเดอร์ร้านค้า                                       | No          | Shop purchase totals for the full year -- from รายละเอียดออเดอร์                                                                                       |
| qry รายละเอียดการโอนเงินร้านค้า          | SELECT | ข้อมูลสมาชิก                                                                                 | qry สินค้าในแต่ละออเดอร์ปลีก, qry สินค้าในแต่ละออเดอร์ร้านค้า         | No          | Shop bank transfer details with order and payment info -- from ข้อมูลสมาชิก                                                                            |
| qry รายละเอียดการโอนแต่ละออเดอร์ปลีก     | SELECT | รายละเอียดออเดอร์                                                                            | qry สินค้าในแต่ละออเดอร์ร้านค้า                                       | No          | Retail order bank transfer details -- from รายละเอียดออเดอร์                                                                                           |
| qry วันที่และเวลาโอนเงินเรียงตามใบกำกับ  | SELECT | รายละเอียดออเดอร์                                                                            | -                                                                     | No          | Transfer date/time sorted by invoice number -- from รายละเอียดออเดอร์                                                                                  |
| qry สต็อคสินค้า                          | SELECT | สินค้า                                                                                       | qry จำนวนรับเข้ารวม ของสินค้าทุกตัว, qry จำนวนเบิกรวม ของสินค้าทุกตัว | No          | Current stock levels (received minus issued minus sold) -- from สินค้า                                                                                 |
| qry สต็อคสินค้าในแต่ละออเดอร์ปลีก        | SELECT | -                                                                                            | qry สต็อคสินค้า, qry สินค้าในแต่ละออเดอร์ปลีก                         | No          | Stock levels for products in retail orders -- from calculated                                                                                          |
| qry สินค้าในแต่ละออเดอร์ปลีก             | SELECT | รายละเอียดออเดอร์, สินค้าในแต่ละออเดอร์                                                      | -                                                                     | No          | Product line items per retail order with pricing/VAT -- from รายละเอียดออเดอร์, สินค้าในแต่ละออเดอร์                                                   |
| qry สินค้าในแต่ละออเดอร์ร้านค้า          | SELECT | ข้อมูลร้านค้า, สินค้าในแต่ละออเดอร์                                                          | -                                                                     | No          | Product line items per shop order with pricing/VAT/discounts -- from ข้อมูลร้านค้า, สินค้าในแต่ละออเดอร์                                               |
| qry_ร้านค้ารอโอน                         | SELECT | รายละเอียดออเดอร์                                                                            | qry สินค้าในแต่ละออเดอร์ร้านค้า                                       | No          | Shops with pending bank transfers -- from รายละเอียดออเดอร์                                                                                            |
| qry_ร้านค้าส่งของให้ก่อน                 | SELECT | รายละเอียดออเดอร์                                                                            | qry สินค้าในแต่ละออเดอร์ร้านค้า                                       | No          | Shops requiring advance shipment -- from รายละเอียดออเดอร์                                                                                             |
| qry_สินค้าที่ขายดีย้อนหลัง 3 เดือน       | SELECT | รายละเอียดออเดอร์, สินค้าในแต่ละออเดอร์                                                      | -                                                                     | No          | Best-selling products over last 3 months -- from รายละเอียดออเดอร์, สินค้าในแต่ละออเดอร์                                                               |
| qryกำหนดเลขที่inv                        | SELECT | รายละเอียดออเดอร์                                                                            | -                                                                     | No          | Assign invoice number sequence -- from รายละเอียดออเดอร์                                                                                               |
| qryยอดเงินร้านค้า                        | SELECT | รายละเอียดออเดอร์                                                                            | qry สินค้าในแต่ละออเดอร์ร้านค้า                                       | No          | Shop payment amounts with order and transfer details -- from รายละเอียดออเดอร์                                                                         |
| qryรายงานสินค้าและวัตุดิบ                | UNION  | รายละเอียดออเดอร์, สินค้า, สินค้าในแต่ละออเดอร์, สินค้าในแต่ละใบรับเข้า, สินค้าในแต่ละใบเบิก | -                                                                     | No          | UNION report combining products and raw materials -- from รายละเอียดออเดอร์, สินค้า, สินค้าในแต่ละออเดอร์, สินค้าในแต่ละใบรับเข้า, สินค้าในแต่ละใบเบิก |
| qryลงยอดร้านค้า                          | SELECT | ข้อมูลร้านค้า, รายละเอียดออเดอร์                                                             | -                                                                     | No          | Post shop payment amounts -- from ข้อมูลร้านค้า, รายละเอียดออเดอร์                                                                                     |
| qryใส่เลขที่ใบกำกับ                      | SELECT | ข้อมูลสมาชิก, รายละเอียดออเดอร์                                                              | -                                                                     | No          | Assign tax invoice number to orders -- from ข้อมูลสมาชิก, รายละเอียดออเดอร์                                                                            |
| จำนวนที่ขายของสินค้าแต่ละตัว(ระบุวันที่) | SELECT | ข้อมูลร้านค้า, สินค้าในแต่ละออเดอร์                                                          | -                                                                     | No          | Quantity sold per product filtered by date range (parameterized) -- from ข้อมูลร้านค้า, สินค้าในแต่ละออเดอร์                                           |
| ดูจำนวนรวมสินค้าที่สั่งหลายออเดอร์รวมกัน | SELECT | สินค้าในแต่ละออเดอร์                                                                         | -                                                                     | No          | View combined quantity of products across multiple orders -- from สินค้าในแต่ละออเดอร์                                                                 |

## Hidden System Subqueries

> These are auto-generated queries (`~sq_*` prefix) created by Access for subforms,
> combo boxes, and report record sources. They are not visible in the query list
> but are essential data sources for forms and reports.

- **`~sq_c*` (subform control sources):** 8
- **`~sq_d*` (lookup/combo data sources):** 14
- **`~sq_r*` (report record sources):** 7

| Name                                                             | Type       | Tables Referenced                               | Purpose                                                                            |
|:-----------------------------------------------------------------|:-----------|:------------------------------------------------|:-----------------------------------------------------------------------------------|
| ~sq_cfrm เบิกสินค้า~sq_cสินค้าในแต่ละใบเบิก Subform              | SELECT (P) | สินค้า, สินค้าในแต่ละใบเบิก                     | Subform data source for frm เบิกสินค้า -> สินค้าในแต่ละใบเบิก Subform              |
| ~sq_cfrm รับเข้าสินค้า~sq_cสินค้าในแต่ละใบรับเข้า Subform        | SELECT (P) | สินค้า, สินค้าในแต่ละใบรับเข้า                  | Subform data source for frm รับเข้าสินค้า -> สินค้าในแต่ละใบรับเข้า Subform        |
| ~sq_cfrm_salesorder_fishingshop~sq_cfrm_stck_fishingshop         | SELECT (P) | -                                               | Subform data source for frm_salesorder_fishingshop -> frm_stck_fishingshop         |
| ~sq_cfrm_salesorder_retail~sq_cfrm_stck_retail                   | SELECT (P) | -                                               | Subform data source for frm_salesorder_retail -> frm_stck_retail                   |
| ~sq_cfrm_salesorder_retail~sq_cqry สินค้าในแต่ละออเดอร์ Subform1 | SELECT (P) | -                                               | Subform data source for frm_salesorder_retail -> qry สินค้าในแต่ละออเดอร์ Subform1 |
| ~sq_cqry สินค้าในแต่ละออเดอร์ Subform~sq_cสินค้า                 | SELECT     | สินค้า                                          | Subform data source for qry สินค้าในแต่ละออเดอร์ Subform -> สินค้า                 |
| ~sq_cรายละเอียดออเดอร์~sq_cqry คะแนนรวมลูกค้าแต่ละคน subform     | SELECT (P) | -                                               | Subform data source for รายละเอียดออเดอร์ -> qry คะแนนรวมลูกค้าแต่ละคน subform     |
| ~sq_cรายละเอียดออเดอร์1~sq_cChild24                              | SELECT (P) | สินค้าในแต่ละออเดอร์                            | Subform data source for รายละเอียดออเดอร์1 -> Child24                              |
| ~sq_dCopy of ใบกำกับภาษีร้านค้า~sq_dสินค้า                       | SELECT     | สินค้า                                          | Lookup/combo data source: Copy of ใบกำกับภาษีร้านค้า -> สินค้า                     |
| ~sq_dpdf แจ้งยอด~sq_dสินค้า                                      | SELECT     | สินค้า                                          | Lookup/combo data source: pdf แจ้งยอด -> สินค้า                                    |
| ~sq_dqry เจาะจงหมายเลขออเดอร์ subreport~sq_dสินค้า               | SELECT     | สินค้า                                          | Lookup/combo data source: qry เจาะจงหมายเลขออเดอร์ subreport -> สินค้า             |
| ~sq_dบิลร้านค้า~sq_dสินค้า                                       | SELECT     | สินค้า                                          | Lookup/combo data source: บิลร้านค้า -> สินค้า                                     |
| ~sq_dบิลร้านค้า1~sq_dสินค้า                                      | SELECT     | สินค้า                                          | Lookup/combo data source: บิลร้านค้า1 -> สินค้า                                    |
| ~sq_dบิลร้านค้า3~sq_dสินค้า                                      | SELECT     | สินค้า                                          | Lookup/combo data source: บิลร้านค้า3 -> สินค้า                                    |
| ~sq_dบิลลูกค้าปลีก~sq_dคะแนนคงเหลือหลังจากใช้แล้ว                | SELECT     | -                                               | Lookup/combo data source: บิลลูกค้าปลีก -> คะแนนคงเหลือหลังจากใช้แล้ว              |
| ~sq_dบิลลูกค้าปลีก~sq_dสินค้า                                    | SELECT     | สินค้า                                          | Lookup/combo data source: บิลลูกค้าปลีก -> สินค้า                                  |
| ~sq_dใบกำกับภาษีร้านค้า(สำเนา)~sq_dสินค้า                        | SELECT     | สินค้า                                          | Lookup/combo data source: ใบกำกับภาษีร้านค้า(สำเนา) -> สินค้า                      |
| ~sq_dใบกำกับภาษีลูกค้าปลีก(สำเนา)~sq_dสินค้า                     | SELECT     | สินค้า                                          | Lookup/combo data source: ใบกำกับภาษีลูกค้าปลีก(สำเนา) -> สินค้า                   |
| ~sq_dใบกำกับภาษีลูกค้าปลีก~sq_dคะแนนคงเหลือหลังจากใช้แล้ว        | SELECT     | -                                               | Lookup/combo data source: ใบกำกับภาษีลูกค้าปลีก -> คะแนนคงเหลือหลังจากใช้แล้ว      |
| ~sq_dใบกำกับภาษีลูกค้าปลีก~sq_dสินค้า                            | SELECT     | สินค้า                                          | Lookup/combo data source: ใบกำกับภาษีลูกค้าปลีก -> สินค้า                          |
| ~sq_dใบส่งของร้านค้า~sq_dสินค้า                                  | SELECT     | สินค้า                                          | Lookup/combo data source: ใบส่งของร้านค้า -> สินค้า                                |
| ~sq_dปรินท์ใบเบิกสินค้า~sq_dสินค้า                               | SELECT     | สินค้า                                          | Lookup/combo data source: ปรินท์ใบเบิกสินค้า -> สินค้า                             |
| ~sq_rCopy of ใบกำกับภาษีร้านค้า                                  | SELECT     | รายละเอียดออเดอร์, สินค้า, สินค้าในแต่ละออเดอร์ | Report record source for Copy of ใบกำกับภาษีร้านค้า                                |
| ~sq_rpdf แจ้งยอด                                                 | SELECT     | รายละเอียดออเดอร์, สินค้า, สินค้าในแต่ละออเดอร์ | Report record source for pdf แจ้งยอด                                               |
| ~sq_rตรวจภาษีขายเรียงตามเลขinv                                   | SELECT     | ข้อมูลร้านค้า, ข้อมูลสมาชิก                     | Report record source for ตรวจภาษีขายเรียงตามเลขinv                                 |
| ~sq_rบิลร้านค้า                                                  | SELECT     | รายละเอียดออเดอร์, สินค้า, สินค้าในแต่ละออเดอร์ | Report record source for บิลร้านค้า                                                |
| ~sq_rใบกำกับภาษีร้านค้า(สำเนา)                                   | SELECT     | รายละเอียดออเดอร์, สินค้า, สินค้าในแต่ละออเดอร์ | Report record source for ใบกำกับภาษีร้านค้า(สำเนา)                                 |
| ~sq_rใบส่งของร้านค้า                                             | SELECT     | รายละเอียดออเดอร์, สินค้า, สินค้าในแต่ละออเดอร์ | Report record source for ใบส่งของร้านค้า                                           |
| ~sq_rรายงานภาษีขาย                                               | SELECT     | ข้อมูลร้านค้า, ข้อมูลสมาชิก                     | Report record source for รายงานภาษีขาย                                             |

## Query Type Distribution

### User Queries

| Type   |   Count |
|:-------|--------:|
| SELECT |      32 |
| UNION  |       1 |

### All Queries (including hidden)

| Type   |   Count |
|:-------|--------:|
| SELECT |      61 |
| UNION  |       1 |

## Parameterized and Form-Referencing Queries

> Queries with PARAMETERS keyword or [Forms]!... references require runtime input.
> These represent user interaction points in the Access application.

| Query Name                                                   | Has PARAMETERS   | Form References                          | Input Prompts   |
|:-------------------------------------------------------------|:-----------------|:-----------------------------------------|:----------------|
| ~sq_cfrm เบิกสินค้า~sq_cสินค้าในแต่ละใบเบิก Subform          | PARAMETERS       | -                                        | -               |
| ~sq_cfrm รับเข้าสินค้า~sq_cสินค้าในแต่ละใบรับเข้า Subform    | PARAMETERS       | -                                        | -               |
| ~sq_cfrm_salesorder_fishingshop~sq_cfrm_stck_fishingshop     | PARAMETERS       | -                                        | -               |
| ~sq_cfrm_salesorder_retail~sq_cfrm_stck_retail               | PARAMETERS       | -                                        | -               |
| ~sq_cfrm_salesorder_retail~sq_cqry สินค้าในแต่ละออเดอร์ Subf | PARAMETERS       | -                                        | -               |
| ~sq_cรายละเอียดออเดอร์~sq_cqry คะแนนรวมลูกค้าแต่ละคน subform | PARAMETERS       | -                                        | -               |
| ~sq_cรายละเอียดออเดอร์1~sq_cChild24                          | PARAMETERS       | -                                        | -               |
| ~sq_rCopy of ใบกำกับภาษีร้านค้า                              | -                | frm_salesorder_fishingshop!เลขที่ออเดอร์ | -               |
| ~sq_rpdf แจ้งยอด                                             | -                | frm_salesorder_fishingshop!เลขที่ออเดอร์ | -               |
| ~sq_rบิลร้านค้า                                              | -                | frm_salesorder_fishingshop!เลขที่ออเดอร์ | -               |
| ~sq_rใบกำกับภาษีร้านค้า(สำเนา)                               | -                | frm_salesorder_fishingshop!เลขที่ออเดอร์ | -               |
| ~sq_rใบส่งของร้านค้า                                         | -                | frm_salesorder_fishingshop!เลขที่ออเดอร์ | -               |
| qry คะแนนคงเหลือหลังจากใช้แล้ว                               | -                | frm_salesorder_retail!หมายเลขสมาชิก      | -               |
| qry เจาะจงเลขที่ใบเบิก                                       | -                | frm เบิกสินค้า!เลขที่ใบเบิก              | -               |
| qry เจาะจงเลขที่ใบรับเข้า                                    | -                | frm รับเข้าสินค้า!เลขที่ใบรับเข้า        | -               |
| qry เจาะจงหมายเลขออเดอร์ปลีก                                 | -                | frm_salesorder_retail!เลขที่ออเดอร์      | -               |
| qry เจาะจงหมายเลขออเดอร์ร้านค้า                              | -                | frm_salesorder_fishingshop!เลขที่ออเดอร์ | -               |
