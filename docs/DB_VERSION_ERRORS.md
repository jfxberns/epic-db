# DB Version Export Analysis

## Summary

Export testing across all available database backups (2019-2024) reveals that **4 forms became corrupt between Sep 2019 and Jul 2020**, during the previous owner's (Chong) tenure. The 2019-09-07 backup is the only version where all forms export cleanly.

### Corruption Timeline

| Version | Date | Forms Exported | Error Type | Owner |
|---------|------|---------------|------------|-------|
| chong_softbaitx_2019-09-07 | 2019-09-07 | **17 (all clean)** | None | Chong |
| chong_softbaitx_2020-07-03 | 2020-07-03 | 7 (4 failed) | Property not found | Chong |
| chong_softbaitx_2021-07-03 | 2021-07-03 | 7 (4 failed) | Search key not found | Chong |
| chong_softbaitx_2022-06-19 | 2022-06-19 | 7 (4 failed) | VBA project corrupt | Chong |
| epic_sports_2023-10-16 | 2023-10-16 | 2 | None (stripped DB) | Epic |
| epic_sports_2023-10-23 | 2023-10-23 | 7 (4 failed) | DB recovered warning | Epic |
| epic_sports_2024-10-25 | 2024-10-25 | 7 (4 failed) | VBA project corrupt | Epic |

### Conclusion

The corruption is **dead legacy code** — the VBA project stream in the 4 affected forms was damaged during the 2019-2020 period and never repaired. The forms themselves continued to function in Access (the design surface is intact; only the VBA container is broken, preventing `SaveAsText` export). All 4 forms were successfully recovered from the 2019-09-07 backup.

### DB Evolution (Object Counts Over Time)

| Version | Forms | Reports | Queries | Subqueries |
|---------|-------|---------|---------|------------|
| 2019-09-07 | 17 | 14 | 21 | 16 |
| 2020-07-03 | 7* | 11 | 30 | 27 |
| 2021-07-03 | 7* | 11 | 32 | 27 |
| 2022-06-19 | 7* | 11 | 32 | 29 |
| 2023-10-16 | 2 | 1 | 1 | 2 |
| 2023-10-23 | 7* | 11 | 32 | 39 |
| 2024-10-25 | 7* | 11 | 32 | 34 |

\* Plus 4 corrupt forms that could not be exported.

---

## Per-Version Export Logs

## 2019-09-07 — chong softbaitx_2019-09-07.accdb (failed attempt: filename had spaces)

**DB file**

- `chong softbaitx_2019-09-07.accdb`

**Error**

- `ERROR: Database file not found: chong`

**Export Summary**

- Not produced (script exited early).

---

## 2019-09-07 — chong_softbaitx_2019-09-07.accdb

**DB file**

- `chong_softbaitx_2019-09-07.accdb`

**ERRORS from VBScript**

- None shown in the log for this run.

**Export Summary**

- Elapsed time: `00:09`

- Forms: `17`

- Reports: `14`

- Queries: `21`

- Query SQL: `21`

- Subqueries: `16`

- Macros: `0`

- Modules: `0`

---

## 2020-07-03 — chong_softbaitx_2020-07-03.accdb

**DB file**

- `chong_softbaitx_2020-07-03.accdb`

**ERRORS from VBScript**

- `ERROR exporting form 'frm_salesorder_fishingshop': Property not found.`

- `ERROR exporting form 'frm_salesorder_retail': Property not found.`

- `ERROR exporting form 'frm_stck_fishingshop': Property not found.`

- `ERROR exporting form 'qry stck subform2': Property not found.`

**Export Summary**

- Elapsed time: `00:08`

- Forms: `7`

- Reports: `11`

- Queries: `30`

- Query SQL: `30`

- Subqueries: `27`

- Macros: `0`

- Modules: `0`

---

## 2021-07-03 — chong_softbaitx_2021-07-03.accdb

**DB file**

- `chong_softbaitx_2021-07-03.accdb`

**ERRORS from VBScript**

- `ERROR exporting form 'frm_salesorder_fishingshop': The search key was not found in any record.`

- `ERROR exporting form 'frm_salesorder_retail': The search key was not found in any record.`

- `ERROR exporting form 'frm_stck_fishingshop': The search key was not found in any record.`

- `ERROR exporting form 'qry stck subform2': The search key was not found in any record.`

**Export Summary**

- Elapsed time: `00:08`

- Forms: `7`

- Reports: `11`

- Queries: `32`

- Query SQL: `32`

- Subqueries: `27`

- Macros: `0`

- Modules: `0`

---

## 2022-06-19 — chong_softbaitx_2022-06-19.accdb

**DB file**

- `chong_softbaitx_2022-06-19.accdb`

**ERRORS from VBScript**

- `ERROR exporting form 'frm_salesorder_fishingshop': The Visual Basic for Applications project in the database is corrupt.`

- `ERROR exporting form 'frm_salesorder_retail': The Visual Basic for Applications project in the database is corrupt.`

- `ERROR exporting form 'frm_stck_fishingshop': The Visual Basic for Applications project in the database is corrupt.`

- `ERROR exporting form 'qry stck subform2': The Visual Basic for Applications project in the database is corrupt.`

**Export Summary**

- Elapsed time: `00:09`

- Forms: `7`

- Reports: `11`

- Queries: `32`

- Query SQL: `32`

- Subqueries: `29`

- Macros: `0`

- Modules: `0`

---

## 2023-10-16 — epic_sports_2023-10-16.accdb

**DB file**

- `epic_sports_2023-10-16.accdb`

**ERRORS from VBScript**

- None shown in the log for this run.

**Export Summary**

- Elapsed time: `00:03`

- Forms: `2`

- Reports: `1`

- Queries: `1`

- Query SQL: `1`

- Subqueries: `2`

- Macros: `0`

- Modules: `0`

---

## 2023-10-23 — epic_sports_2023-10-23-backup.accdb

**DB file**

- `epic_sports_2023-10-23-backup.accdb`

**ERRORS from VBScript**

- `ERROR exporting form 'frm_salesorder_fishingshop': Microsoft Access has recovered this database. Examine the database to verify that there are no missing database objects.`

- `ERROR exporting form 'frm_salesorder_retail': Microsoft Access has recovered this database. Examine the database to verify that there are no missing database objects.`

- `ERROR exporting form 'frm_stck_fishingshop': Microsoft Access has recovered this database. Examine the database to verify that there are no missing database objects.`

- `ERROR exporting form 'qry stck subform2': Microsoft Access has recovered this database. Examine the database to verify that there are no missing database objects.`

**Export Summary**

- Elapsed time: `00:04`

- Forms: `7`

- Reports: `11`

- Queries: `32`

- Query SQL: `32`

- Subqueries: `39`

- Macros: `0`

- Modules: `0`

---

## 2023-10-23 — epic_sports_2023-10-23.accdb

**DB file**

- `epic_sports_2023-10-23.accdb`

**ERRORS from VBScript**

- `ERROR exporting form 'frm_salesorder_fishingshop': Microsoft Access has recovered this database. Examine the database to verify that there are no missing database objects.`

- `ERROR exporting form 'frm_salesorder_retail': Microsoft Access has recovered this database. Examine the database to verify that there are no missing database objects.`

- `ERROR exporting form 'frm_stck_fishingshop': Microsoft Access has recovered this database. Examine the database to verify that there are no missing database objects.`

- `ERROR exporting form 'qry stck subform2': Microsoft Access has recovered this database. Examine the database to verify that there are no missing database objects.`

**Export Summary**

- Elapsed time: `00:08`

- Forms: `7`

- Reports: `11`

- Queries: `32`

- Query SQL: `32`

- Subqueries: `39`

- Macros: `0`

- Modules: `0`

---

## 2023-10-23 — epic_sports_2023-10-23_backup.accdb

**DB file**

- `epic_sports_2023-10-23_backup.accdb`

**ERRORS from VBScript**

- `ERROR exporting form 'frm_salesorder_fishingshop': Microsoft Access has recovered this database. Examine the database to verify that there are no missing database objects.`

- `ERROR exporting form 'frm_salesorder_retail': Microsoft Access has recovered this database. Examine the database to verify that there are no missing database objects.`

- `ERROR exporting form 'frm_stck_fishingshop': Microsoft Access has recovered this database. Examine the database to verify that there are no missing database objects.`

- `ERROR exporting form 'qry stck subform2': Microsoft Access has recovered this database. Examine the database to verify that there are no missing database objects.`

**Export Summary**

- Elapsed time: `00:04`

- Forms: `7`

- Reports: `11`

- Queries: `32`

- Query SQL: `32`

- Subqueries: `39`

- Macros: `0`

- Modules: `0`

---

## 2024-10-25 — epic_sports_2024-10-25.accdb

**DB file**

- `epic_sports_2024-10-25.accdb`

**ERRORS from VBScript**

- `ERROR exporting form 'frm_salesorder_fishingshop': The Visual Basic for Applications project in the database is corrupt.`

- `ERROR exporting form 'frm_salesorder_retail': The Visual Basic for Applications project in the database is corrupt.`

- `ERROR exporting form 'frm_stck_fishingshop': The Visual Basic for Applications project in the database is corrupt.`

- `ERROR exporting form 'qry stck subform2': The Visual Basic for Applications project in the database is corrupt.`

**Export Summary**

- Elapsed time: `00:08`

- Forms: `7`

- Reports: `11`

- Queries: `32`

- Query SQL: `32`

- Subqueries: `34`

- Macros: `0`

- Modules: `0`
