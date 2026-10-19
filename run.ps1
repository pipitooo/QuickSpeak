param([switch]$Show)
$ErrorActionPreference = 'Stop'
$python = Join-Path $PSScriptRoot '.runtime\Scripts\pythonw.exe'
if (-not (Test-Path $python)) { throw 'Run setup.ps1 first.' }
$appArgs = @(('"' + (Join-Path $PSScriptRoot 'main.py') + '"'))
if ($Show) { $appArgs += '--show' }
Start-Process -FilePath $python -ArgumentList $appArgs -WorkingDirectory $PSScriptRoot -WindowStyle Hidden
