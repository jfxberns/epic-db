' export_all.vbs
' Headless VBScript to export all Access objects via SaveAsText + QueryDef.SQL
'
' Usage: cscript //nologo export_all.vbs "C:\path\to\epic_db.accdb" "C:\output"
'
' Exports:
'   forms/          - SaveAsText form definitions (17 expected)
'   reports/        - SaveAsText report definitions (25 expected)
'   queries/        - SaveAsText query definitions
'   queries_sql/    - Raw QueryDef.SQL text (Unicode UTF-16-LE)
'   queries_sql/subqueries/ - Hidden ~sq_c* subquery SQL (8 expected)
'   macros/         - SaveAsText macro definitions
'   modules/        - SaveAsText module definitions
'
' Object type constants for SaveAsText:
'   acForm   = 2
'   acReport = 3
'   acQuery  = 1
'   acMacro  = 4
'   acModule = 5

Option Explicit

' ---------------------------------------------------------------------------
' Parse arguments
' ---------------------------------------------------------------------------
Dim args
Set args = WScript.Arguments

If args.Count < 2 Then
    WScript.StdErr.WriteLine "Usage: cscript //nologo export_all.vbs <db_path> <output_path>"
    WScript.StdErr.WriteLine ""
    WScript.StdErr.WriteLine "  db_path     Full path to the .accdb file"
    WScript.StdErr.WriteLine "  output_path Directory to write exported files"
    WScript.Quit 1
End If

Dim dbPath, outputPath
dbPath = args(0)
outputPath = args(1)

' Ensure outputPath does not end with a backslash (we add them ourselves)
If Right(outputPath, 1) = "\" Then
    outputPath = Left(outputPath, Len(outputPath) - 1)
End If

' ---------------------------------------------------------------------------
' Filesystem setup
' ---------------------------------------------------------------------------
Dim fso
Set fso = CreateObject("Scripting.FileSystemObject")

If Not fso.FileExists(dbPath) Then
    WScript.StdErr.WriteLine "ERROR: Database file not found: " & dbPath
    WScript.Quit 1
End If

' Create output directory tree
Dim dirs, d
dirs = Array( _
    outputPath, _
    outputPath & "\forms", _
    outputPath & "\reports", _
    outputPath & "\queries", _
    outputPath & "\queries_sql", _
    outputPath & "\queries_sql\subqueries", _
    outputPath & "\macros", _
    outputPath & "\modules" _
)

For Each d In dirs
    If Not fso.FolderExists(d) Then
        fso.CreateFolder(d)
    End If
Next

' ---------------------------------------------------------------------------
' Counters
' ---------------------------------------------------------------------------
Dim countForms, countReports, countQueries, countQuerySQL
Dim countSubqueries, countMacros, countModules, countErrors
countForms = 0
countReports = 0
countQueries = 0
countQuerySQL = 0
countSubqueries = 0
countMacros = 0
countModules = 0
countErrors = 0

' ---------------------------------------------------------------------------
' Open Access headless
' ---------------------------------------------------------------------------
WScript.Echo "Opening Access database: " & dbPath
Dim accessApp
Set accessApp = CreateObject("Access.Application")
accessApp.Visible = False
accessApp.AutomationSecurity = 1  ' msoAutomationSecurityLow - trust all active content
accessApp.OpenCurrentDatabase dbPath

Dim db
Set db = accessApp.CurrentDb()

WScript.Echo "Database opened successfully."
WScript.Echo ""

' ---------------------------------------------------------------------------
' Export Forms (SaveAsText acForm=2)
' ---------------------------------------------------------------------------
WScript.Echo "=== FORMS ==="
Dim container, doc
Set container = db.Containers("Forms")
For Each doc In container.Documents
    On Error Resume Next
    accessApp.SaveAsText 2, doc.Name, outputPath & "\forms\" & doc.Name & ".txt"
    If Err.Number <> 0 Then
        WScript.StdErr.WriteLine "ERROR exporting form '" & doc.Name & "': " & Err.Description
        countErrors = countErrors + 1
        Err.Clear
    Else
        WScript.Echo "  Form: " & doc.Name
        countForms = countForms + 1
    End If
    On Error GoTo 0
Next

WScript.Echo "  Exported " & countForms & " form(s)"
WScript.Echo ""

' ---------------------------------------------------------------------------
' Export Reports (SaveAsText acReport=3)
' ---------------------------------------------------------------------------
WScript.Echo "=== REPORTS ==="
Set container = db.Containers("Reports")
For Each doc In container.Documents
    On Error Resume Next
    accessApp.SaveAsText 3, doc.Name, outputPath & "\reports\" & doc.Name & ".txt"
    If Err.Number <> 0 Then
        WScript.StdErr.WriteLine "ERROR exporting report '" & doc.Name & "': " & Err.Description
        countErrors = countErrors + 1
        Err.Clear
    Else
        WScript.Echo "  Report: " & doc.Name
        countReports = countReports + 1
    End If
    On Error GoTo 0
Next

WScript.Echo "  Exported " & countReports & " report(s)"
WScript.Echo ""

' ---------------------------------------------------------------------------
' Export Queries (SaveAsText acQuery=1 + raw SQL)
' ---------------------------------------------------------------------------
WScript.Echo "=== QUERIES ==="
Dim qdf, i, sqlFile, safeName

For i = 0 To db.QueryDefs.Count - 1
    Set qdf = db.QueryDefs(i)

    ' Check if this is a hidden subquery (~sq_c* prefix)
    If Left(qdf.Name, 4) = "~sq_" Then
        ' Export subquery SQL to queries_sql/subqueries/
        On Error Resume Next
        safeName = Replace(qdf.Name, "~", "_tilde_")
        Set sqlFile = fso.CreateTextFile(outputPath & "\queries_sql\subqueries\" & safeName & ".sql", True, True)
        sqlFile.Write qdf.SQL
        sqlFile.Close
        If Err.Number <> 0 Then
            WScript.StdErr.WriteLine "ERROR exporting subquery SQL '" & qdf.Name & "': " & Err.Description
            countErrors = countErrors + 1
            Err.Clear
        Else
            WScript.Echo "  Subquery SQL: " & qdf.Name & " (Type=" & qdf.Type & ")"
            countSubqueries = countSubqueries + 1
        End If
        On Error GoTo 0

    ElseIf Left(qdf.Name, 1) <> "~" Then
        ' Regular visible query -- export both SaveAsText and raw SQL
        On Error Resume Next

        ' SaveAsText definition
        accessApp.SaveAsText 1, qdf.Name, outputPath & "\queries\" & qdf.Name & ".txt"
        If Err.Number <> 0 Then
            WScript.StdErr.WriteLine "ERROR exporting query definition '" & qdf.Name & "': " & Err.Description
            countErrors = countErrors + 1
            Err.Clear
        Else
            countQueries = countQueries + 1
        End If

        ' Raw SQL (Unicode UTF-16-LE)
        Set sqlFile = fso.CreateTextFile(outputPath & "\queries_sql\" & qdf.Name & ".sql", True, True)
        sqlFile.Write qdf.SQL
        sqlFile.Close
        If Err.Number <> 0 Then
            WScript.StdErr.WriteLine "ERROR exporting query SQL '" & qdf.Name & "': " & Err.Description
            countErrors = countErrors + 1
            Err.Clear
        Else
            countQuerySQL = countQuerySQL + 1
        End If

        On Error GoTo 0

        WScript.Echo "  Query: " & qdf.Name & " (Type=" & qdf.Type & ")"
    End If
    ' Skip other ~ prefixed system queries (e.g., ~TMPCLPMacro queries)
Next

WScript.Echo "  Exported " & countQueries & " query definition(s)"
WScript.Echo "  Exported " & countQuerySQL & " query SQL file(s)"
WScript.Echo "  Exported " & countSubqueries & " subquery SQL file(s)"
WScript.Echo ""

' ---------------------------------------------------------------------------
' Export Macros (SaveAsText acMacro=4)
' ---------------------------------------------------------------------------
WScript.Echo "=== MACROS ==="
Set container = db.Containers("Scripts")
For Each doc In container.Documents
    If Left(doc.Name, 1) <> "~" Then
        On Error Resume Next
        accessApp.SaveAsText 4, doc.Name, outputPath & "\macros\" & doc.Name & ".txt"
        If Err.Number <> 0 Then
            WScript.StdErr.WriteLine "ERROR exporting macro '" & doc.Name & "': " & Err.Description
            countErrors = countErrors + 1
            Err.Clear
        Else
            WScript.Echo "  Macro: " & doc.Name
            countMacros = countMacros + 1
        End If
        On Error GoTo 0
    End If
Next

WScript.Echo "  Exported " & countMacros & " macro(s)"
WScript.Echo ""

' ---------------------------------------------------------------------------
' Export Modules (SaveAsText acModule=5)
' ---------------------------------------------------------------------------
WScript.Echo "=== MODULES ==="
Set container = db.Containers("Modules")
For Each doc In container.Documents
    On Error Resume Next
    accessApp.SaveAsText 5, doc.Name, outputPath & "\modules\" & doc.Name & ".txt"
    If Err.Number <> 0 Then
        WScript.StdErr.WriteLine "ERROR exporting module '" & doc.Name & "': " & Err.Description
        countErrors = countErrors + 1
        Err.Clear
    Else
        WScript.Echo "  Module: " & doc.Name
        countModules = countModules + 1
    End If
    On Error GoTo 0
Next

WScript.Echo "  Exported " & countModules & " module(s)"
WScript.Echo ""

' ---------------------------------------------------------------------------
' Cleanup
' ---------------------------------------------------------------------------
db.Close
accessApp.Quit
Set db = Nothing
Set accessApp = Nothing

' ---------------------------------------------------------------------------
' Summary
' ---------------------------------------------------------------------------
WScript.Echo "=========================================="
WScript.Echo "EXPORT COMPLETE"
WScript.Echo "=========================================="
WScript.Echo "  Forms:       " & countForms
WScript.Echo "  Reports:     " & countReports
WScript.Echo "  Queries:     " & countQueries & " definitions + " & countQuerySQL & " SQL files"
WScript.Echo "  Subqueries:  " & countSubqueries & " SQL files (hidden ~sq_* queries)"
WScript.Echo "  Macros:      " & countMacros
WScript.Echo "  Modules:     " & countModules
WScript.Echo "  Errors:      " & countErrors
WScript.Echo ""
WScript.Echo "Output directory: " & outputPath
