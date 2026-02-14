# Windows Export: epic_db.accdb

Export all forms, reports, queries, macros, and modules from the Access database using Microsoft Access COM automation.

## Why Windows?

The 17 forms and 25 reports in `epic_db.accdb` are stored as binary blobs that can only be extracted using Microsoft Access's `Application.SaveAsText` method. This requires a Windows environment with Access installed. Queries are also exported here via `QueryDef.SQL` for cross-validation against the macOS Jackcess extraction.

## Windows Environment Options

### Option A: UTM Virtual Machine on macOS (free, recommended)

UTM is a free, open-source virtual machine app for macOS that runs Windows 11 ARM on Apple Silicon.

1. Install UTM from [https://mac.getutm.app](https://mac.getutm.app) or the Mac App Store
2. Download a Windows 11 ARM ISO from Microsoft: [https://www.microsoft.com/software-download/windows11arm64](https://www.microsoft.com/software-download/windows11arm64)
3. Follow the UTM guide for Windows setup: [https://docs.getutm.app/guides/windows/](https://docs.getutm.app/guides/windows/)
4. Allocate at least 4 GB RAM and 40 GB disk to the VM
5. Install Microsoft Access (see Prerequisites below)

### Option B: Cloud Windows Instance

Use Azure, AWS, or another cloud provider to spin up a Windows VM with Microsoft 365 pre-installed. This avoids local disk space but costs money.

### Option C: Physical Windows Machine

Any Windows 10/11 machine with Microsoft Access installed will work. Borrow a machine, use a work computer, etc.

## Prerequisites

- **Microsoft Access** is required. Options:
  - **Microsoft 365 subscription** (includes Access) -- recommended, has native ARM64 builds
  - **Standalone Access 2019 or later** -- works but on ARM64 Windows may use x86 emulation (transparent on Win11 ARM)
  - Access 2016 also works but is end-of-life
- **PowerShell 5.1+** (included with Windows 10/11)
- No other software is needed

### ARM64 Note

If using an ARM64 Windows VM (UTM on Apple Silicon), Microsoft 365 provides native ARM64 Access builds. Standalone/retail Access versions are x86 only but run fine under Windows 11's transparent x86 emulation layer. Performance is adequate for this one-time export.

## Setup Steps

### 1. Copy files to the Windows machine

Copy these items to the Windows machine (e.g., to `C:\epic_db\`):

```
C:\epic_db\
  epic_db.accdb          <-- the database (from data/epic_db.accdb)
  windows\
    export_all.vbs       <-- the export script
    export_all.ps1       <-- the PowerShell wrapper
```

You can use:
- UTM shared folder / drag-and-drop
- USB drive
- Cloud storage (OneDrive, Google Drive)
- Network share

### 2. Run the export

Open **PowerShell** (search for "PowerShell" in the Start menu) and run:

```powershell
cd C:\epic_db\windows
.\export_all.ps1 -DbPath "C:\epic_db\epic_db.accdb" -OutputPath "C:\epic_db\export"
```

If PowerShell blocks the script with an execution policy error, run this first:

```powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
```

### 3. Wait for completion

The export takes approximately 30-60 seconds for all 74 objects. You will see progress output for each exported object.

### 4. Verify the export

Check the output counts match expectations:

| Directory | Expected Files | Format |
|-----------|---------------|--------|
| `export\forms\` | 17 .txt files | SaveAsText form definitions |
| `export\reports\` | 25 .txt files | SaveAsText report definitions |
| `export\queries\` | ~24 .txt files | SaveAsText query definitions |
| `export\queries_sql\` | ~24 .sql files | Raw QueryDef.SQL (UTF-16-LE) |
| `export\queries_sql\subqueries\` | ~8 .sql files | Hidden ~sq_c* subquery SQL |
| `export\macros\` | 0 files | No macros in database |
| `export\modules\` | 0 files | No modules in database |

## Thai Encoding

The database contains Thai text in table names, column names, form captions, and query SQL. To ensure Thai characters export correctly:

### Recommended: Enable UTF-8 system locale

1. Open **Settings** > **Time & Language** > **Language & region**
2. Click **Administrative language settings** (bottom of page)
3. Click **Change system locale...**
4. Check **Beta: Use Unicode UTF-8 for worldwide language support**
5. Restart Windows

### Alternative: Install Thai language pack

1. Open **Settings** > **Time & Language** > **Language & region**
2. Click **Add a language** and search for **Thai**
3. Install the Thai language pack (you do not need to set it as the display language)

### Verification

After running the export, open one of the form `.txt` files (e.g., `export\forms\หน้าหลัก.txt`) in Notepad. Thai characters should be readable, not garbled. If you see `?????` or random symbols, apply one of the encoding fixes above and re-run the export.

## Bringing Files Back to macOS

Copy the entire `export\` directory back to macOS and place it at:

```
/Users/jb/Dev/epic_gear/epic-db/windows/export/
```

The final structure on macOS should be:

```
windows/
  export_all.vbs
  export_all.ps1
  README.md
  export/
    forms/
      frm รับเข้าสินค้า.txt
      frm เบิกสินค้า.txt
      frm_salesorder_fishingshop.txt
      ... (17 files total)
    reports/
      ใบกำกับภาษีร้านค้า.txt
      ใบกำกับภาษีลูกค้าปลีก.txt
      ... (25 files total)
    queries/
      qry สต็อคสินค้า.txt
      ... (~24 files)
    queries_sql/
      qry สต็อคสินค้า.sql
      ... (~24 files)
      subqueries/
        _tilde_sq_c*.sql
        ... (~8 files)
    macros/
      (empty)
    modules/
      (empty)
```

## Troubleshooting

### "ActiveX component can't create object"

Microsoft Access is not installed. Install Microsoft 365 with Access or standalone Access 2019+.

### "Could not find installable ISAM"

The Access Database Engine is not properly registered. Try:
1. Repair the Office installation (Settings > Apps > Microsoft 365 > Modify > Repair)
2. Or download and install the [Access Database Engine](https://www.microsoft.com/en-us/download/details.aspx?id=54920)

### Script hangs (no output for >2 minutes)

Access may have opened a modal dialog (e.g., asking to repair the database, or a security warning). Try:
1. Open Task Manager (Ctrl+Shift+Esc)
2. Look for `MSACCESS.EXE` -- if it is running, end the task
3. Copy a fresh `epic_db.accdb` to the Windows machine
4. Before re-running, try opening `epic_db.accdb` manually in Access once to dismiss any first-time dialogs
5. Close Access and re-run the script

### "The database was created by a newer version of Access"

The database is Access 2010 format (.accdb). This should work with Access 2010 and later. If you see this error, your Access version may be too old. Update to Access 2019 or Microsoft 365.

### PowerShell execution policy error

Run this command before the export script:
```powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
```

### Thai text appears garbled in exported files

See the "Thai Encoding" section above. Enable UTF-8 system locale or install the Thai language pack, then re-run the export.

### Some objects fail to export but others succeed

The script continues past individual errors. Check the error output at the end. Common causes:
- Corrupted form/report definition (rare) -- the other objects will still export
- Name contains characters invalid for filenames (the script does not sanitize names; Windows NTFS allows Thai characters)

### Access opens visible windows during export

The script sets `accessApp.Visible = False`, but some Access versions may still briefly show a splash screen. This is cosmetic and does not affect the export.
