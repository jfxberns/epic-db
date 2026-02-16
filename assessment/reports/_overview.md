# Report Catalogue

**Generated:** 2026-02-16
**Source:** windows/export/reports/ via SaveAsText exports
**Generator:** scripts/extract_forms_reports.py (rerun to regenerate)

## Summary

- **Exported reports:** 11
- **Reports with code-behind:** 0
- **Reports with subreports:** 1
- **Total controls across all reports:** 135

## Report Catalogue

| Name                                         | Record Source                                                                       |   Controls | Code-Behind?   | Output Type            |
|:---------------------------------------------|:------------------------------------------------------------------------------------|-----------:|:---------------|:-----------------------|
| qry เจาะจงหมายเลขออเดอร์ subreport           | qry เจาะจงหมายเลขออเดอร์ปลีก                                                        |         11 | No             | Subreport (embedded)   |
| rptดูเลขทีใบเบิก                             | SELECT [หัวใบเบิก].[เลขที่ใบเบิก], [หัวใบเบิก].[วันที่เบิก], [หัวใบเบิก].[หมายเล... |          9 | No             | Goods issue document   |
| rptทำที่อยู่เบิกสินค้า                       | SELECT [หัวใบเบิก].[เลขที่ใบเบิก], [หัวใบเบิก].[รหัสร้านค้าที่เบิก], [หัวใบเบิก]... |         22 | No             | Address label/list     |
| rptรายละเอียดการโอนเงินของแต่ละเลขที่ออเดอร์ | SELECT [รายละเอียดออเดอร์].[เลขที่ออเดอร์], [รายละเอียดออเดอร์].[วันที่โอนเงิน],... |          6 | No             | Bank transfer report   |
| ข้อมูลสำหรับแจ้งเลขพัสดุร้านค้า              | qry ที่อยู่เจาะจงโดยวันที่ (ร้านค้า)                                                |          8 | No             | Shipping notification  |
| ข้อมูลสำหรับแจ้งเลขพัสดุลูกค้าปลีก           | qry ที่อยู่เจาะจงโดยวันที่ (ปลีก)                                                   |          8 | No             | Shipping notification  |
| ตรวจภาษีขายเรียงตามเลขinv                    | SELECT [รายละเอียดออเดอร์].[เลขที่ออเดอร์], [รายละเอียดออเดอร์].ธนาคาร, [รายละเอ... |         20 | No             | Tax/invoice report     |
| ปรินท์ใบเบิกสินค้า                           | qry เจาะจงเลขที่ใบเบิก                                                              |         10 | No             | Goods issue document   |
| ปริ้นท์ที่อยู่ลูกค้าปลีก                     | qry ที่อยู่เจาะจงโดยวันที่ (ปลีก)                                                   |         16 | No             | Address label/list     |
| รายงานภาษีขาย                                | SELECT [รายละเอียดออเดอร์].[เลขที่ออเดอร์], [รายละเอียดออเดอร์].ธนาคาร, [รายละเอ... |         17 | No             | Tax/invoice report     |
| รายละเอียดใบรับเข้าสินค้า                    | SELECT [สินค้าในแต่ละใบรับเข้า].[สินค้า], [สินค้าในแต่ละใบรับเข้า].[จำนวนรับเข้า... |          8 | No             | Goods receipt document |

## Report Details

### qry เจาะจงหมายเลขออเดอร์ subreport

**Purpose:** Order-specific detail subreport -- shows line items for a particular order number

**Record Source:** `qry เจาะจงหมายเลขออเดอร์ปลีก`

**Key Fields Displayed:**

| Name          | Type     | Control Source   |
|:--------------|:---------|:-----------------|
| เลขที่ออเดอร์ | TextBox  | เลขที่ออเดอร์    |
| เบอร์โทรศัพท์ | TextBox  | เบอร์โทรศัพท์    |
| ชื่อ          | TextBox  | ชื่อ             |
| สินค้า        | ComboBox | สินค้า           |
| จำนวน         | TextBox  | จำนวน            |
| หน่วยนับ      | TextBox  | หน่วยนับ         |
| ราคา          | TextBox  | ราคา             |
| ราคารวม       | TextBox  | ราคารวม          |

---

### rptดูเลขทีใบเบิก

**Purpose:** View goods issue numbers -- lists all withdrawal documents with dates and destinations

**Record Source:** `SELECT [หัวใบเบิก].[เลขที่ใบเบิก], [หัวใบเบิก].[วันที่เบิก], [หัวใบเบิก].[หมายเลขสมาชิกที่เบิก], [หัวใบเบิก].[รหัสร้า...`

**Key Fields Displayed:**

| Name          | Type    | Control Source       |
|:--------------|:--------|:---------------------|
| เลขที่ออเดอร์ | TextBox | ชื่อ                 |
| วันที่โอนเงิน | TextBox | เลขที่ใบเบิก         |
| เวลาโอนเงิน   | TextBox | หมายเลขสมาชิกที่เบิก |
| Text2         | TextBox | ชื่อไลน์หรือเฟซ      |
| Text10        | TextBox | วันที่เบิก           |
| Text8         | TextBox | ชื่อร้าน             |

---

### rptทำที่อยู่เบิกสินค้า

**Purpose:** Goods issue address labels -- formats shipping addresses for goods withdrawal orders

**Record Source:** `SELECT [หัวใบเบิก].[เลขที่ใบเบิก], [หัวใบเบิก].[รหัสร้านค้าที่เบิก], [หัวใบเบิก].[หมายเลขสมาชิกที่เบิก], [ข้อมูลร้านค...`

**Key Fields Displayed:**

| Name          | Type    | Control Source       |
|:--------------|:--------|:---------------------|
| ชื่อ          | TextBox | ชื่อร้าน             |
| ที่อยู่ล่าสุด | TextBox | ที่อยู่              |
| เบอร์โทรศัพท์ | TextBox | เบอร์โทรศัพท์ร้านค้า |
| วันหยุด       | TextBox | วันหยุด              |
| ขนส่งที่สะดวก | TextBox | ขนส่งที่สะดวก        |
| Text39        | TextBox | ชื่อ                 |
| นามสกุล       | TextBox | นามสกุล              |
| Text40        | TextBox | ที่อยู่ล่าสุด        |
| Text42        | TextBox | เบอร์โทรศัพท์        |
| เลขที่ใบเบิก  | TextBox | เลขที่ใบเบิก         |
| Text1         | TextBox | เลขที่ใบเบิก         |

---

### rptรายละเอียดการโอนเงินของแต่ละเลขที่ออเดอร์

**Purpose:** Bank transfer details per order -- shows payment transfer information for each order

**Record Source:** `SELECT [รายละเอียดออเดอร์].[เลขที่ออเดอร์], [รายละเอียดออเดอร์].[วันที่โอนเงิน], [รายละเอียดออเดอร์].[เวลาโอนเงิน], [...`

**Key Fields Displayed:**

| Name          | Type    | Control Source   |
|:--------------|:--------|:-----------------|
| เลขที่ออเดอร์ | TextBox | เลขที่ออเดอร์    |
| วันที่โอนเงิน | TextBox | วันที่โอนเงิน    |
| เวลาโอนเงิน   | TextBox | เวลาโอนเงิน      |

---

### ข้อมูลสำหรับแจ้งเลขพัสดุร้านค้า

**Purpose:** Shop shipping notification -- provides tracking and address info for shop channel orders

**Record Source:** `qry ที่อยู่เจาะจงโดยวันที่ (ร้านค้า)`

**Key Fields Displayed:**

| Name            | Type     | Control Source   |
|:----------------|:---------|:-----------------|
| ชื่อไลน์หรือเฟซ | TextBox  | ชื่อเฟส          |
| ชื่อ            | TextBox  | ชื่อร้าน         |
| ช่องทางสั่งซื้อ | ComboBox | ช่องทางสั่งซื้อ  |
| Text57          | TextBox  | ชื่อไลน์         |

---

### ข้อมูลสำหรับแจ้งเลขพัสดุลูกค้าปลีก

**Purpose:** Retail customer shipping notification -- provides tracking and address info for retail orders

**Record Source:** `qry ที่อยู่เจาะจงโดยวันที่ (ปลีก)`

**Key Fields Displayed:**

| Name            | Type     | Control Source   |
|:----------------|:---------|:-----------------|
| ชื่อไลน์หรือเฟซ | TextBox  | ชื่อไลน์หรือเฟซ  |
| ชื่อ            | TextBox  | ชื่อ             |
| นามสกุล         | TextBox  | นามสกุล          |
| ช่องทางสั่งซื้อ | ComboBox | ช่องทางสั่งซื้อ  |

---

### ตรวจภาษีขายเรียงตามเลขinv

**Purpose:** Sales tax verification report sorted by invoice number -- cross-references order details with bank transfers and invoice data

**Record Source:** `SELECT [รายละเอียดออเดอร์].[เลขที่ออเดอร์], [รายละเอียดออเดอร์].ธนาคาร, [รายละเอียดออเดอร์].[เวลาโอนเงิน], [รายละเอีย...`

**Key Fields Displayed:**

| Name                                    | Type     | Control Source                          |
|:----------------------------------------|:---------|:----------------------------------------|
| เลขที่ออเดอร์                           | TextBox  | เลขที่ออเดอร์                           |
| ธนาคาร                                  | ComboBox | ธนาคาร                                  |
| ชื่อร้าน                                | TextBox  | ชื่อร้าน                                |
| Text41                                  | TextBox  | วันที่                                  |
| เลขที่invoiceของปี                      | TextBox  | เลขที่invoiceของปี                      |
| SumOfราคารวมก่อนแวทหลังหักส่วนลดท้ายบิล | TextBox  | SumOfราคารวมก่อนแวทหลังหักส่วนลดท้ายบิล |
| Text78                                  | TextBox  | SumOfภาษีมูลค่าเพิ่ม                    |
| SumOfราคาสุทธิรวมภาษีมูลค่าเพิ่ม        | TextBox  | SumOfราคาสุทธิรวมภาษีมูลค่าเพิ่ม        |
| ชื่อ                                    | TextBox  | ชื่อ                                    |
| SumOfราคารวมก่อนแวท                     | TextBox  | SumOfราคารวมก่อนแวท                     |
| SumOfภาษีมูลค่าเพิ่มปลีก                | TextBox  | SumOfภาษีมูลค่าเพิ่มปลีก                |
| SumOfราคาสุทธิปลีกรวมภาษีมูลค่าเพิ่ม    | TextBox  | SumOfราคาสุทธิปลีกรวมภาษีมูลค่าเพิ่ม    |
| วันที่โอนเงิน                           | TextBox  | วันที่โอนเงิน                           |
| เวลาโอนเงิน                             | TextBox  | เวลาโอนเงิน                             |

---

### ปรินท์ใบเบิกสินค้า

**Purpose:** Print goods issue document -- shows items in a specific withdrawal with product details

**Record Source:** `qry เจาะจงเลขที่ใบเบิก`

**Key Fields Displayed:**

| Name      | Type     | Control Source   |
|:----------|:---------|:-----------------|
| สินค้า    | ComboBox | สินค้า           |
| จำนวนเบิก | TextBox  | จำนวนเบิก        |
| หน่วยนับ  | ComboBox | หน่วยนับ         |

---

### ปริ้นท์ที่อยู่ลูกค้าปลีก

**Purpose:** Print retail customer addresses -- formatted address labels for retail order shipments

**Record Source:** `qry ที่อยู่เจาะจงโดยวันที่ (ปลีก)`

**Key Fields Displayed:**

| Name          | Type    | Control Source   |
|:--------------|:--------|:-----------------|
| ชื่อ          | TextBox | ชื่อ             |
| นามสกุล       | TextBox | นามสกุล          |
| ที่อยู่ล่าสุด | TextBox | ที่อยู่ล่าสุด    |
| เลขที่ออเดอร์ | TextBox | เลขที่ออเดอร์    |
| เบอร์โทรศัพท์ | TextBox | เบอร์โทรศัพท์    |

**Subreports:**

- **?** -> ``

---

### รายงานภาษีขาย

**Purpose:** Sales tax report -- lists order details with bank transfer info, dates, and amounts for tax reporting

**Record Source:** `SELECT [รายละเอียดออเดอร์].[เลขที่ออเดอร์], [รายละเอียดออเดอร์].ธนาคาร, [รายละเอียดออเดอร์].[วันที่โอนเงิน], [รายละเอ...`

**Key Fields Displayed:**

| Name                                    | Type     | Control Source                          |
|:----------------------------------------|:---------|:----------------------------------------|
| เลขที่invoiceของปี                      | TextBox  | เลขที่invoiceของปี                      |
| SumOfราคารวมก่อนแวทหลังหักส่วนลดท้ายบิล | TextBox  | SumOfราคารวมก่อนแวทหลังหักส่วนลดท้ายบิล |
| Text78                                  | TextBox  | SumOfภาษีมูลค่าเพิ่ม                    |
| SumOfราคารวมก่อนแวท                     | TextBox  | SumOfราคารวมก่อนแวท                     |
| SumOfภาษีมูลค่าเพิ่มปลีก                | TextBox  | SumOfภาษีมูลค่าเพิ่มปลีก                |
| เลขประจำตัวผู้เสียภาษีร้านค้า           | TextBox  | เลขประจำตัวผู้เสียภาษีร้านค้า           |
| ชื่อออกใบกำกับปลีก                      | TextBox  | ชื่อออกใบกำกับปลีก                      |
| ชื่อร้านสำหรับออกใบกำกับ                | TextBox  | ชื่อร้านสำหรับออกใบกำกับ                |
| สาขาสถานประกอบการ                       | TextBox  | สาขาสถานประกอบการ                       |
| สาขาสำนักงานใหญ่                        | TextBox  | สาขาสำนักงานใหญ่                        |
| วันที่                                  | TextBox  | วันที่                                  |
| วันที่โอนเงิน                           | TextBox  | วันที่โอนเงิน                           |
| เวลาโอนเงิน                             | TextBox  | เวลาโอนเงิน                             |
| ธนาคาร                                  | ComboBox | ธนาคาร                                  |

---

### รายละเอียดใบรับเข้าสินค้า

**Purpose:** Goods receipt details -- shows items received in each goods receipt document

**Record Source:** `SELECT [สินค้าในแต่ละใบรับเข้า].[สินค้า], [สินค้าในแต่ละใบรับเข้า].[จำนวนรับเข้า], [สินค้าในแต่ละใบรับเข้า].[หมายเลขก...`

**Key Fields Displayed:**

| Name         | Type     | Control Source   |
|:-------------|:---------|:-----------------|
| สินค้า       | ComboBox | สินค้า           |
| จำนวนรับเข้า | TextBox  | จำนวนรับเข้า     |
| หน่วยนับ     | ComboBox | หน่วยนับ         |
| หมายเลขกล่อง | TextBox  | หมายเลขกล่อง     |

---
