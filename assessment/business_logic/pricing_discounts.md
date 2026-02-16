# Pricing, Discounts, and Business Logic Formulas

**Generated:** 2026-02-16
**Source:** Synthesized from query SQL analysis and table schemas
**Cross-references:** [Query Overview](../queries/_overview.md), [Process Flows](./process_flows.md), [Table: สินค้า](../tables/สินค้า.md), [Table: ข้อมูลสมาชิก](../tables/ข้อมูลสมาชิก.md)

## Overview

All pricing and discount logic in the Epic Gear database is implemented in **query SQL calculated columns** -- there is no VBA code-behind in any exported form or report. The system maintains two parallel pricing tracks: one for shop/wholesale customers with per-product discounts and bill-end discounts, and one for retail customers with simpler pricing plus a loyalty points system.

**Key finding:** Prices are stored as fixed values in the `สินค้า` (product) table, not calculated dynamically. Discounts are also stored per-product (shop discount) and per-order (bill-end discount percentage). There is no programmatic discount engine or pricing rules engine -- all values are entered manually.

---

## 1. Product Pricing Structure

The `สินค้า` table (186 products) stores multiple price columns:

| Column | Type | Purpose |
|:-------|:-----|:--------|
| `ราคา` | Long Integer | Retail price (VAT-inclusive, baht) |
| `ราคาก่อนแวท` | Single | Pre-VAT price (baht) |
| `ส่วนลดร้านค้า` | Double | Shop discount amount (baht, not percentage) |
| `ส่วนลดร้านค้าก่อนแวท` | Single | Shop discount amount pre-VAT (baht) |
| `ราคาร้านค้ารวมแวท` | Decimal(30,4) | Shop price including VAT (stored as binary, likely computed) |

**Key observations:**
- Shop discount (`ส่วนลดร้านค้า`) is a **fixed baht amount** per product, not a percentage
- Retail price (`ราคา`) is VAT-inclusive; pre-VAT price (`ราคาก่อนแวท`) is stored separately
- From sample data: `ราคา=65`, `ราคาก่อนแวท=60.7477` -- confirms `65 / 1.07 = 60.747...` (7% VAT)
- Many products have `ส่วนลดร้านค้า = 0` (no shop discount)

---

## 2. Shop/Wholesale Pricing (ร้านค้า)

**Source query:** `qry สินค้าในแต่ละออเดอร์ร้านค้า`

### Calculation Chain (VAT-inclusive track)

This is the pricing used on shop bills (`บิลร้านค้า`):

```
Step 1: Unit price after shop discount
  [ราคาหลังหักส่วนลดร้านค้า] = [ราคา] - [ส่วนลดร้านค้า]

Step 2: Line total after shop discount
  [ราคารวมหลังหักส่วนลดร้านค้า] = [ราคาหลังหักส่วนลดร้านค้า] * [จำนวน]

Step 3: Line total after bill-end discount
  [ราคารวมหลังหักส่วนลดท้ายบิล] = [ราคารวมหลังหักส่วนลดร้านค้า] * (1 - ([ส่วนลดท้ายบิล(%)] / 100))
```

### Calculation Chain (pre-VAT track)

This is the pricing used on tax invoices (`ใบกำกับภาษีร้านค้า`):

```
Step 1: Pre-VAT unit price after shop discount
  [ราคาก่อนแวทหลังหักส่วนลดร้านค้า] = [ราคาก่อนแวท] - [ส่วนลดร้านค้าก่อนแวท]

Step 2: Pre-VAT line total after shop discount
  [ราคารวมก่อนแวทหลังหักส่วนลดร้านค้า] = [ราคาก่อนแวทหลังหักส่วนลดร้านค้า] * [จำนวน]

Step 3: Pre-VAT line total after bill-end discount
  [ราคารวมก่อนแวทหลังหักส่วนลดท้ายบิล] = [ราคารวมก่อนแวทหลังหักส่วนลดร้านค้า] * (1 - ([ส่วนลดท้ายบิล(%)] / 100))

Step 4: VAT calculation (7%)
  [ภาษีมูลค่าเพิ่ม] = [ราคารวมก่อนแวทหลังหักส่วนลดท้ายบิล] * 0.07

Step 5: Net total including VAT
  [ราคาสุทธิรวมภาษีมูลค่าเพิ่ม] = [ราคารวมก่อนแวทหลังหักส่วนลดท้ายบิล] + [ภาษีมูลค่าเพิ่ม]
```

### Discount Types for Shop Channel

| Discount | Source | Type | Stored In |
|:---------|:-------|:-----|:----------|
| Per-product shop discount | `สินค้า.ส่วนลดร้านค้า` | Fixed baht amount | Product table |
| Bill-end discount | `รายละเอียดออเดอร์.ส่วนลดท้ายบิล(%)` | Percentage | Order header |

**Bill-end discount** is entered per order (stored as Double in `รายละเอียดออเดอร์`). From sample data, values range from 0% to 34%. This is likely negotiated per-shop or per-order.

### Shop Sales Summary Query

`qry ยอดขายร้านค้า` calculates order-level totals for date-range analysis:

```sql
Sum([ราคารวมหลังหักส่วนลดร้านค้า]) AS [SumOfราคารวมหลังหักส่วนลดร้านค้า]
Sum([ราคารวมหลังหักส่วนลดร้านค้า] * (1 - ([ส่วนลดท้ายบิล(%)] / 100))) AS Expr1
```

This shows both before and after bill-end discount totals, filtered by date range.

---

## 3. Retail Pricing (ปลีก)

**Source query:** `qry สินค้าในแต่ละออเดอร์ปลีก`

### Calculation Chain

Retail pricing is simpler -- no per-product discount and no bill-end discount:

```
Step 1: Line total (VAT-inclusive)
  [ราคารวม] = [ราคา] * [จำนวน]

Step 2: Pre-VAT line total
  [ราคารวมก่อนแวท] = [ราคาก่อนแวท] * [จำนวน]

Step 3: VAT calculation (7%)
  [ภาษีมูลค่าเพิ่มปลีก] = [ราคารวมก่อนแวท] * 0.07

Step 4: Net total including VAT
  [ราคาสุทธิปลีกรวมภาษีมูลค่าเพิ่ม] = [ราคารวมก่อนแวท] + [ภาษีมูลค่าเพิ่มปลีก]

Step 5: Loyalty points earned
  [คะแนน] = [ราคารวม] / 100
```

**Key difference from shop pricing:** No product discount, no bill-end discount. Retail customers pay full price but earn loyalty points.

---

## 4. VAT Calculation (7%)

Thailand's standard VAT rate of 7% is hardcoded in the query SQL:

| Context | Formula | Source Query |
|:--------|:--------|:------------|
| Shop orders | `[ราคารวมก่อนแวทหลังหักส่วนลดท้ายบิล] * 0.07` | `qry สินค้าในแต่ละออเดอร์ร้านค้า` |
| Retail orders | `[ราคารวมก่อนแวท] * 0.07` | `qry สินค้าในแต่ละออเดอร์ปลีก` |

**Note:** VAT is calculated on the **pre-VAT** price (after all discounts for shop channel). The system maintains dual price columns (with/without VAT) to support both VAT-inclusive bills and formal tax invoices.

**Tax invoice reports** that use these calculations:
- `ใบกำกับภาษีร้านค้า` / `ใบกำกับภาษีร้านค้า(สำเนา)` -- Shop tax invoice
- `ใบกำกับภาษีลูกค้าปลีก` / `ใบกำกับภาษีลูกค้าปลีก(สำเนา)` -- Retail tax invoice
- `รายงานภาษีขาย` -- Sales tax summary report
- `ตรวจภาษีขายเรียงตามเลขinv` -- Tax verification by invoice number

---

## 5. Loyalty Points System

### Points Accumulation

**Source query:** `qry สินค้าในแต่ละออเดอร์ปลีก`

```
Points per line item = [ราคารวม] / 100
```

**Rate:** 1 point per 100 baht spent (VAT-inclusive price). Points are calculated per order line item, not per order.

**Aggregation:** `qry คะแนนรวมลูกค้าแต่ละคน` sums all points across all orders for each member:

```sql
SELECT [หมายเลขสมาชิก], Sum([คะแนน]) AS [SumOfคะแนน]
FROM [qry สินค้าในแต่ละออเดอร์ปลีก]
GROUP BY [หมายเลขสมาชิก]
```

### Points Redemption

**Source query:** `qry คะแนนคงเหลือหลังจากใช้แล้ว`

The remaining points formula:

```
Remaining = [SumOfคะแนน] + [คะแนนคีย์มือเพิ่มให้] - [คะแนนที่ใช้ครั้งที่1] - [คะแนนที่ใช้ครั้งที่2] - [คะแนนที่ใช้ครั้งที่3]
```

| Component | Source | Description |
|:----------|:-------|:------------|
| `SumOfคะแนน` | `qry คะแนนรวมลูกค้าแต่ละคน` | Total points earned from purchases |
| `คะแนนคีย์มือเพิ่มให้` | `ข้อมูลสมาชิก` column | Manual points added by staff |
| `คะแนนที่ใช้ครั้งที่1` | `ข้อมูลสมาชิก` column | First redemption |
| `คะแนนที่ใช้ครั้งที่2` | `ข้อมูลสมาชิก` column | Second redemption |
| `คะแนนที่ใช้ครั้งที่3` | `ข้อมูลสมาชิก` column | Third redemption |

**Design observations:**
- Points redemption is tracked in **only 3 fixed columns** (`ครั้งที่1`, `ครั้งที่2`, `ครั้งที่3`) rather than a transaction log. This limits each customer to 3 lifetime redemptions.
- There is also a `คะแนนที่ลูกค้าใช้ไป` table (0 rows, 7 columns) which appears to be an unused or abandoned points usage log.
- The `คะแนนคีย์มือเพิ่มให้` field allows staff to manually add bonus points.
- Points are only earned on **retail** orders, not shop orders (shop channel query has no points calculation).

### Points Display in Real-Time

The remaining points are shown during retail order entry via:
- Subform `qry คะแนนรวมลูกค้าแต่ละคน subform` embedded in the order detail form
- Form `คะแนนคงเหลือหลังจากใช้แล้ว` (standalone form showing remaining points)
- Lookup combo in retail bill reports (`~sq_dบิลลูกค้าปลีก~sq_dคะแนนคงเหลือหลังจากใช้แล้ว`)

The points query is filtered by member number from the current retail order form:
```sql
WHERE [หมายเลขสมาชิก] = [Forms]![frm_salesorder_retail]![หมายเลขสมาชิก]
```

---

## 6. Stock Level Formula

**Source query:** `qry สต็อคสินค้า`

```
Current Stock = Nz([SumOfจำนวนรับเข้า], 0)   -- total received
              - Nz([SumOfจำนวน], 0)           -- total sold
              - Nz([SumOfจำนวนเบิก], 0)        -- total issued/withdrawn
```

Where:
- `SumOfจำนวนรับเข้า` = `Sum(จำนวนรับเข้า)` from `สินค้าในแต่ละใบรับเข้า` (514 receipt records)
- `SumOfจำนวน` = `Sum(จำนวน)` from `สินค้าในแต่ละออเดอร์` joined with `รายละเอียดออเดอร์` (7,073 order line items)
- `SumOfจำนวนเบิก` = `Sum(จำนวนเบิก)` from `สินค้าในแต่ละใบเบิก` (15,293 issue records)

**`Nz()` usage:** Handles NULL values for products with no receipts, no sales, or no issues, defaulting to 0.

**Stock is not stored** -- it is recalculated on every query. There is no running balance or stock snapshot table.

The stock form (`frm_สต็อคสินค้า`) and stock subforms (`frm_stck_fishingshop`, `frm_stck_retail`) display this calculated value during order entry so staff can see available stock before adding line items.

---

## 7. Inventory/Formula Logic (VBA-03)

**Finding: No raw-material-to-finished-product mapping found.**

The database treats all items in the `สินค้า` table as finished products. There is:
- No bill of materials (BOM) table
- No manufacturing or assembly queries
- No VBA code implementing formula/recipe calculations
- No distinction between raw materials and finished goods in the schema

The UNION query `qryรายงานสินค้าและวัตุดิบ` (literally "report of products and raw materials") combines receipts, issues, and sales into a single timeline, but does not implement any material conversion logic. Its name suggests the business may conceptually distinguish between products and raw materials, but the database treats them identically.

The goods issue (`เบิก`) flow with 15,293 records and 3,391 issue documents may represent internal material usage or transfers, but no query or form logic converts issued materials into different products.

---

## 8. Pricing Comparison: Shop vs. Retail

| Aspect | Shop (ร้านค้า) | Retail (ปลีก) |
|:-------|:--------------|:-------------|
| Base price | `สินค้า.ราคา` | `สินค้า.ราคา` |
| Per-product discount | Yes (`ส่วนลดร้านค้า`, fixed baht) | No |
| Bill-end discount | Yes (`ส่วนลดท้ายบิล(%)`, 0-34%) | No |
| VAT calculation | On pre-VAT after all discounts | On pre-VAT (no discounts to apply) |
| Loyalty points | No | Yes (1 pt per 100 baht) |
| Customer identifier | `รหัสร้านค้า` (shop code) | `เบอร์โทรศัพท์` (phone number) |
| Tax invoice | Shop name/address/TIN | Member name/address/TIN |

---

## 9. Payment Status Tracking

The `ธนาคาร` (bank) field in `รายละเอียดออเดอร์` serves as both bank identifier and payment status:

| Value | Meaning | Used In |
|:------|:--------|:--------|
| `"กสิกร"` | Kasikorn Bank -- paid via bank transfer | `qry รายละเอียดการโอนเงินร้านค้า`, `qryใส่เลขที่ใบกำกับ`, `qry วันที่และเวลาโอนเงินฯ` |
| `"ส่งของให้ก่อน"` | Goods shipped before payment (credit terms) | `qry_ร้านค้าส่งของให้ก่อน`, `qryลงยอดร้านค้า`, `qryใส่เลขที่ใบกำกับ` |
| `"รอโอน"` | Awaiting bank transfer | `qry_ร้านค้ารอโอน`, `qryใส่เลขที่ใบกำกับ` |
| `"เงินสด"` | Cash payment | (seen in sample data, no dedicated query) |

This is a **text field** (Short Text, 20 chars) used as a status enum. There is no separate payment status table or state machine.

---

## Summary of All Formulas

| Formula ID | Description | SQL Expression | Source Query |
|:-----------|:------------|:---------------|:------------|
| F-01 | Shop line price after discount | `[ราคา] - [ส่วนลดร้านค้า]` | `qry สินค้าในแต่ละออเดอร์ร้านค้า` |
| F-02 | Shop line total | `[ราคาหลังหักส่วนลดร้านค้า] * [จำนวน]` | `qry สินค้าในแต่ละออเดอร์ร้านค้า` |
| F-03 | Shop total after bill-end discount | `[ราคารวมฯ] * (1 - ([ส่วนลดท้ายบิล(%)] / 100))` | `qry สินค้าในแต่ละออเดอร์ร้านค้า` |
| F-04 | Shop VAT | `[ราคารวมก่อนแวทหลังหักส่วนลดท้ายบิล] * 0.07` | `qry สินค้าในแต่ละออเดอร์ร้านค้า` |
| F-05 | Shop net total | `[pre-VAT after discounts] + [VAT]` | `qry สินค้าในแต่ละออเดอร์ร้านค้า` |
| F-06 | Retail line total | `[ราคา] * [จำนวน]` | `qry สินค้าในแต่ละออเดอร์ปลีก` |
| F-07 | Retail VAT | `[ราคารวมก่อนแวท] * 0.07` | `qry สินค้าในแต่ละออเดอร์ปลีก` |
| F-08 | Retail net total | `[ราคารวมก่อนแวท] + [ภาษีมูลค่าเพิ่มปลีก]` | `qry สินค้าในแต่ละออเดอร์ปลีก` |
| F-09 | Points earned | `[ราคารวม] / 100` | `qry สินค้าในแต่ละออเดอร์ปลีก` |
| F-10 | Points remaining | `Sum + manual - use1 - use2 - use3` | `qry คะแนนคงเหลือหลังจากใช้แล้ว` |
| F-11 | Current stock | `Nz(received,0) - Nz(sold,0) - Nz(issued,0)` | `qry สต็อคสินค้า` |
