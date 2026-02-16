# Form Catalogue

**Generated:** 2026-02-16
**Source:** windows/export/forms/ via SaveAsText exports
**Generator:** scripts/extract_forms_reports.py (rerun to regenerate)

## Summary

- **Exported forms:** 7
- **Corrupt/unexportable forms:** 4 (see Gaps section)
- **Forms with code-behind:** 0
- **Forms with subforms:** 0
- **Total controls across all forms:** 58

## Form Catalogue

| Name                              | Record Source                                                                       |   Controls | Code-Behind?   | Subforms?   | Key Events   |
|:----------------------------------|:------------------------------------------------------------------------------------|-----------:|:---------------|:------------|:-------------|
| frm_สต็อคสินค้า                   | SELECT [qry สต็อคสินค้า].[รหัสสินค้า], [qry สต็อคสินค้า].[หน่วยนับ], [qry สต็อคส... |         15 | No             | No          | -            |
| qry คะแนนรวมลูกค้าแต่ละคน subform | qry คะแนนรวมลูกค้าแต่ละคน                                                           |          4 | No             | No          | -            |
| qry สินค้าในแต่ละออเดอร์ Subform  | qry สินค้าในแต่ละออเดอร์ปลีก                                                        |         11 | No             | No          | -            |
| คะแนนคงเหลือหลังจากใช้แล้ว        | SELECT [qry คะแนนคงเหลือหลังจากใช้แล้ว].[หมายเลขสมาชิก], [qry คะแนนคงเหลือหลังจา... |          4 | No             | No          | -            |
| สินค้าในแต่ละใบรับเข้า Subform    | SELECT [สินค้าในแต่ละใบรับเข้า].[สินค้า], [สินค้าในแต่ละใบรับเข้า].[จำนวนรับเข้า... |          8 | No             | No          | -            |
| สินค้าในแต่ละใบเบิก Subform       | SELECT [สินค้าในแต่ละใบเบิก].*, [สินค้า].[หน่วยนับ], [สินค้าในแต่ละใบเบิก].[หมาย... |          8 | No             | No          | -            |
| หาเลขที่ออเดอร์ถ้ารู้ชื่อร้าน     | SELECT [รายละเอียดออเดอร์].[เลขที่ออเดอร์], [ข้อมูลร้านค้า].[ชื่อร้าน], [ข้อมูลส... |          8 | No             | No          | -            |

## Form Details

### frm_สต็อคสินค้า

**Purpose:** Stock/inventory tracking form -- displays current stock levels calculated from receipts, issues, and sales

**Record Source:** `SELECT [qry สต็อคสินค้า].[รหัสสินค้า], [qry สต็อคสินค้า].[หน่วยนับ], [qry สต็อคสินค้า].Expr2, [qry สต็อคสินค้า].Expr3...`

**Controls:**

| Type          |   Count |
|:--------------|--------:|
| ComboBox      |       2 |
| CommandButton |       1 |
| Label         |       2 |
| Line          |       2 |
| TextBox       |       8 |

**Data Bindings:**

| Name          | Type     | Control Source    |
|:--------------|:---------|:------------------|
| หน่วยนับ      | ComboBox | หน่วยนับ          |
| Expr1         | TextBox  | Expr1             |
| รหัสสินค้า    | TextBox  | รหัสสินค้า        |
| Text60        | TextBox  | Expr1             |
| สินค้า.สินค้า | TextBox  | [สินค้า].[สินค้า] |
| Text78        | TextBox  | SumOfจำนวน        |
| Expr7         | TextBox  | Expr7             |
| Expr8         | TextBox  | Expr8             |

---

### qry คะแนนรวมลูกค้าแต่ละคน subform

**Purpose:** Customer loyalty points subform -- shows total points per customer (embedded in order forms)

**Record Source:** `qry คะแนนรวมลูกค้าแต่ละคน`

**Controls:**

| Type    |   Count |
|:--------|--------:|
| Label   |       2 |
| TextBox |       2 |

**Data Bindings:**

| Name       | Type    | Control Source   |
|:-----------|:--------|:-----------------|
| SumOfคะแนน | TextBox | SumOfคะแนน       |

---

### qry สินค้าในแต่ละออเดอร์ Subform

**Purpose:** Order line items subform -- shows products within each order with pricing and quantities

**Record Source:** `qry สินค้าในแต่ละออเดอร์ปลีก`

**Controls:**

| Type     |   Count |
|:---------|--------:|
| ComboBox |       2 |
| Label    |       5 |
| TextBox  |       4 |

**Data Bindings:**

| Name    | Type     | Control Source   |
|:--------|:---------|:-----------------|
| สินค้า  | ComboBox | สินค้า           |
| จำนวน   | TextBox  | จำนวน            |
| ราคา    | TextBox  | ราคา             |
| ราคารวม | TextBox  | ราคารวม          |

---

### คะแนนคงเหลือหลังจากใช้แล้ว

**Purpose:** Loyalty points remaining -- displays accumulated points after redemptions for each customer

**Record Source:** `SELECT [qry คะแนนคงเหลือหลังจากใช้แล้ว].[หมายเลขสมาชิก], [qry คะแนนคงเหลือหลังจากใช้แล้ว].Expr1 FROM [qry คะแนนคงเหลื...`

**Controls:**

| Type    |   Count |
|:--------|--------:|
| Label   |       2 |
| TextBox |       2 |

**Data Bindings:**

| Name   | Type    | Control Source   |
|:-------|:--------|:-----------------|
| Expr1  | TextBox | Expr1            |

---

### สินค้าในแต่ละใบรับเข้า Subform

**Purpose:** Goods receipt line items subform -- shows products received in each receipt document

**Record Source:** `SELECT [สินค้าในแต่ละใบรับเข้า].[สินค้า], [สินค้าในแต่ละใบรับเข้า].[จำนวนรับเข้า], [สินค้า].[หน่วยนับ], [สินค้าในแต่ล...`

**Controls:**

| Type     |   Count |
|:---------|--------:|
| ComboBox |       3 |
| Label    |       1 |
| TextBox  |       4 |

**Data Bindings:**

| Name         | Type     | Control Source   |
|:-------------|:---------|:-----------------|
| จำนวน        | TextBox  | จำนวนรับเข้า     |
| หน่วยนับ     | ComboBox | หน่วยนับ         |
| สินค้า       | ComboBox | สินค้า           |
| หมายเลขกล่อง | TextBox  | หมายเลขกล่อง     |
| รหัสสินค้า   | TextBox  | รหัสสินค้า       |

---

### สินค้าในแต่ละใบเบิก Subform

**Purpose:** Goods issue line items subform -- shows products issued/withdrawn in each issue document

**Record Source:** `SELECT [สินค้าในแต่ละใบเบิก].*, [สินค้า].[หน่วยนับ], [สินค้าในแต่ละใบเบิก].[หมายเหตุ] FROM สินค้า INNER JOIN สินค้าใน...`

**Controls:**

| Type          |   Count |
|:--------------|--------:|
| ComboBox      |       3 |
| CommandButton |       1 |
| Label         |       1 |
| TextBox       |       3 |

**Data Bindings:**

| Name                         | Type     | Control Source                   |
|:-----------------------------|:---------|:---------------------------------|
| สินค้า                       | ComboBox | สินค้า                           |
| จำนวน                        | TextBox  | จำนวนเบิก                        |
| หน่วยนับ                     | ComboBox | หน่วยนับ                         |
| สินค้าในแต่ละใบเบิก.หมายเหตุ | TextBox  | [สินค้าในแต่ละใบเบิก].[หมายเหตุ] |

---

### หาเลขที่ออเดอร์ถ้ารู้ชื่อร้าน

**Purpose:** Order lookup form -- search for orders by shop name with order details

**Record Source:** `SELECT [รายละเอียดออเดอร์].[เลขที่ออเดอร์], [ข้อมูลร้านค้า].[ชื่อร้าน], [ข้อมูลสมาชิก].[ชื่อ], [ข้อมูลสมาชิก].[หมายเล...`

**Controls:**

| Type    |   Count |
|:--------|--------:|
| Label   |       1 |
| Line    |       2 |
| TextBox |       5 |

**Data Bindings:**

| Name          | Type    | Control Source   |
|:--------------|:--------|:-----------------|
| เลขที่ออเดอร์ | TextBox | เลขที่ออเดอร์    |
| ชื่อร้าน      | TextBox | ชื่อร้าน         |
| ชื่อ          | TextBox | ชื่อ             |
| หมายเลขสมาชิก | TextBox | หมายเลขสมาชิก    |

---

## Gaps: Corrupt VBA Forms (Not Exportable)

The following 4 forms could not be exported due to a corrupt VBA project in the database.
Partial data is available from their associated subquery SQL files.

### frm_salesorder_fishingshop

**Status:** Export failed -- corrupt VBA project

**Related Subquery SQL (partial reconstruction data):**

**`_tilde_sq_cfrm_salesorder_fishingshop_tilde_sq_cfrm_stck_fishingshop`:**
```sql
﻿PARAMETERS __เลขที่ออเดอร์ Value;
SELECT DISTINCTROW *
FROM (SELECT [รายละเอียดออเดอร์].[เลขที่ออเดอร์], [qry สินค้าในแต่ละออเดอร์ร้านค้า].[สินค้า], [qry สต็อคสินค้า].Expr1 FROM (รายละเอียดออเดอร์ INNER JOIN [qry สินค้าในแต่ละออเดอร์ร้านค้า] ON [รายละเอียดออเดอร์].[เลขที่ออเดอร์] = [qry สินค้าในแต่ละออเดอร์ร้านค้า].[เลขที่ออเดอร์]) INNER JOIN [qry สต็อคสินค้า] ON [qry สินค้าในแต่ละออเดอร์ร้านค้า].[สินค้า] = [qry สต็อคสินค้า].[สินค้า].[สินค้า] ORDER BY [qry สินค้าในแต่ละออเดอร์ร้านค้า].[สินค้า])  AS frm_salesorder_fishingshop
WHERE ([__เลขที่ออเดอร์] = [เลขที่ออเดอร์]);
```

---

### frm_salesorder_retail

**Status:** Export failed -- corrupt VBA project

**Related Subquery SQL (partial reconstruction data):**

**`_tilde_sq_cfrm_salesorder_retail_tilde_sq_cqry สินค้าในแต่ละออเดอร์ Subform1`:**
```sql
﻿PARAMETERS __เลขที่ออเดอร์ Value;
SELECT DISTINCTROW *
FROM [qry สินค้าในแต่ละออเดอร์ปลีก] AS frm_salesorder_retail
WHERE ([__เลขที่ออเดอร์] = [เลขที่ออเดอร์]);
```

**`_tilde_sq_cfrm_salesorder_retail_tilde_sq_cfrm_stck_retail`:**
```sql
﻿PARAMETERS __เลขที่ออเดอร์ Value;
SELECT DISTINCTROW *
FROM [qry สต็อคสินค้าในแต่ละออเดอร์ปลีก] AS frm_salesorder_retail
WHERE ([__เลขที่ออเดอร์] = [เลขที่ออเดอร์]);
```

---

### frm_stck_fishingshop

**Status:** Export failed -- corrupt VBA project

**Related Subquery SQL (partial reconstruction data):**

**`_tilde_sq_cfrm_salesorder_fishingshop_tilde_sq_cfrm_stck_fishingshop`:**
```sql
﻿PARAMETERS __เลขที่ออเดอร์ Value;
SELECT DISTINCTROW *
FROM (SELECT [รายละเอียดออเดอร์].[เลขที่ออเดอร์], [qry สินค้าในแต่ละออเดอร์ร้านค้า].[สินค้า], [qry สต็อคสินค้า].Expr1 FROM (รายละเอียดออเดอร์ INNER JOIN [qry สินค้าในแต่ละออเดอร์ร้านค้า] ON [รายละเอียดออเดอร์].[เลขที่ออเดอร์] = [qry สินค้าในแต่ละออเดอร์ร้านค้า].[เลขที่ออเดอร์]) INNER JOIN [qry สต็อคสินค้า] ON [qry สินค้าในแต่ละออเดอร์ร้านค้า].[สินค้า] = [qry สต็อคสินค้า].[สินค้า].[สินค้า] ORDER BY [qry สินค้าในแต่ละออเดอร์ร้านค้า].[สินค้า])  AS frm_salesorder_fishingshop
WHERE ([__เลขที่ออเดอร์] = [เลขที่ออเดอร์]);
```

---

### qry stck subform2

**Status:** Export failed -- corrupt VBA project

No related subquery SQL found.

---
