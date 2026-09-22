# Version 0.4.0: lokale Python-Umgebung und serielle Bibliothek installieren.
$ErrorActionPreference = 'Stop'
$pythonPfad = Join-Path $env:LOCALAPPDATA 'Programs\Python\Python313\python.exe'
if (-not (Test-Path -LiteralPath $pythonPfad)) {
    $pythonPfad = (Get-Command python -ErrorAction Stop).Source
}
& $pythonPfad -m venv (Join-Path $PSScriptRoot '.venv')
if ($LASTEXITCODE -ne 0) { throw 'Python-Umgebung konnte nicht erstellt werden. Python mit Tcl/Tk installieren.' }
& (Join-Path $PSScriptRoot '.venv\Scripts\python.exe') -m pip install -r (Join-Path $PSScriptRoot 'requirements.txt')
if ($LASTEXITCODE -ne 0) { throw 'Installation von pyserial/PySide6 fehlgeschlagen.' }
Write-Output 'Fertig. Start.cmd oeffnet das Bedienfeld.'
