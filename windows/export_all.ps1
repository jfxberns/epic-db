<#
.SYNOPSIS
    PowerShell wrapper for export_all.vbs - exports all Access objects from epic_db.accdb.

.DESCRIPTION
    Validates prerequisites, runs the VBScript export, and reports results.
    Designed for use on Windows with Microsoft Access installed.

.PARAMETER DbPath
    Path to the .accdb database file. Default: .\epic_db.accdb

.PARAMETER OutputPath
    Directory to write exported files. Default: .\export

.EXAMPLE
    .\export_all.ps1 -DbPath "C:\epic_db\epic_db.accdb" -OutputPath "C:\epic_db\export"

.EXAMPLE
    .\export_all.ps1
    # Uses defaults: .\epic_db.accdb and .\export
#>

param(
    [string]$DbPath = ".\epic_db.accdb",
    [string]$OutputPath = ".\export"
)

# ---------------------------------------------------------------------------
# Resolve paths to absolute
# ---------------------------------------------------------------------------
if (-not (Test-Path $DbPath)) {
    Write-Host "ERROR: Database file not found: $DbPath" -ForegroundColor Red
    Write-Host ""
    Write-Host "Usage: .\export_all.ps1 -DbPath 'C:\path\to\epic_db.accdb' -OutputPath 'C:\path\to\export'"
    exit 1
}
$DbPath = (Resolve-Path $DbPath).Path

# Resolve output path (create if needed)
if (-not (Test-Path $OutputPath)) {
    New-Item -ItemType Directory -Path $OutputPath -Force | Out-Null
}
$OutputPath = (Resolve-Path $OutputPath).Path

# ---------------------------------------------------------------------------
# Check for Access installation
# ---------------------------------------------------------------------------
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  Epic DB Access Object Exporter" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Database:   $DbPath"
Write-Host "Output:     $OutputPath"
Write-Host ""

# Quick check: can we create the Access COM object?
try {
    $testAccess = New-Object -ComObject Access.Application
    $testAccess.Quit()
    [System.Runtime.Interopservices.Marshal]::ReleaseComObject($testAccess) | Out-Null
    Write-Host "Microsoft Access: FOUND" -ForegroundColor Green
} catch {
    Write-Host "ERROR: Microsoft Access is not installed or not registered." -ForegroundColor Red
    Write-Host "       Install Microsoft 365 with Access, or standalone Access 2019+." -ForegroundColor Red
    Write-Host ""
    Write-Host "Troubleshooting:" -ForegroundColor Yellow
    Write-Host "  - 'ActiveX component can''t create object' -> Access not installed"
    Write-Host "  - On ARM64 Windows: Microsoft 365 has native ARM64 Access builds"
    exit 1
}

Write-Host ""

# ---------------------------------------------------------------------------
# Run the VBScript
# ---------------------------------------------------------------------------
$vbsPath = Join-Path $PSScriptRoot "export_all.vbs"
if (-not (Test-Path $vbsPath)) {
    Write-Host "ERROR: export_all.vbs not found at: $vbsPath" -ForegroundColor Red
    exit 1
}

Write-Host "Running export..." -ForegroundColor Yellow
Write-Host ""

$stopwatch = [System.Diagnostics.Stopwatch]::StartNew()

# Run cscript and capture both stdout and stderr
$processInfo = New-Object System.Diagnostics.ProcessStartInfo
$processInfo.FileName = "cscript.exe"
$processInfo.Arguments = "//nologo `"$vbsPath`" `"$DbPath`" `"$OutputPath`""
$processInfo.RedirectStandardOutput = $true
$processInfo.RedirectStandardError = $true
$processInfo.UseShellExecute = $false
$processInfo.CreateNoWindow = $true

$process = New-Object System.Diagnostics.Process
$process.StartInfo = $processInfo
$process.Start() | Out-Null

$stdout = $process.StandardOutput.ReadToEnd()
$stderr = $process.StandardError.ReadToEnd()
$process.WaitForExit()

$stopwatch.Stop()

# Display VBScript output
if ($stdout) {
    Write-Host $stdout
}

# Display any errors
if ($stderr) {
    Write-Host ""
    Write-Host "ERRORS from VBScript:" -ForegroundColor Red
    Write-Host $stderr -ForegroundColor Red
}

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------
Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  Export Summary" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

$elapsed = $stopwatch.Elapsed
Write-Host ("Elapsed time: {0:mm\:ss}" -f $elapsed)
Write-Host ""

# Count exported files by type
$types = @(
    @{ Name = "Forms";       Path = "$OutputPath\forms";                Pattern = "*.txt" },
    @{ Name = "Reports";     Path = "$OutputPath\reports";              Pattern = "*.txt" },
    @{ Name = "Queries";     Path = "$OutputPath\queries";              Pattern = "*.txt" },
    @{ Name = "Query SQL";   Path = "$OutputPath\queries_sql";          Pattern = "*.sql" },
    @{ Name = "Subqueries";  Path = "$OutputPath\queries_sql\subqueries"; Pattern = "*.sql" },
    @{ Name = "Macros";      Path = "$OutputPath\macros";               Pattern = "*.txt" },
    @{ Name = "Modules";     Path = "$OutputPath\modules";              Pattern = "*.txt" }
)

foreach ($type in $types) {
    $count = 0
    if (Test-Path $type.Path) {
        $count = (Get-ChildItem -Path $type.Path -Filter $type.Pattern -File -ErrorAction SilentlyContinue).Count
    }
    $status = if ($count -gt 0) { "Green" } else { "DarkGray" }
    Write-Host ("  {0,-15} {1,4} file(s)" -f ($type.Name + ":"), $count) -ForegroundColor $status
}

Write-Host ""

if ($process.ExitCode -eq 0) {
    Write-Host "Export completed successfully." -ForegroundColor Green
} else {
    Write-Host "Export completed with errors (exit code: $($process.ExitCode))." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Next step: Copy the '$OutputPath' directory back to macOS." -ForegroundColor Cyan
Write-Host "Place it at: /Users/jb/Dev/epic_gear/epic-db/windows/export/"
