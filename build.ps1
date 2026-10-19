param([switch]$SkipHardwareTests)
$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot
$env:PYTHONUTF8 = '1'
$python = Join-Path $PSScriptRoot '.runtime\Scripts\python.exe'
if (-not (Test-Path $python)) { throw 'Run setup.ps1 first.' }
& $python -m pip install -r requirements-build.txt
if ($LASTEXITCODE -ne 0) { throw 'Build dependency installation failed.' }
& $python tools\patch_kitten.py
if ($LASTEXITCODE -ne 0) { throw 'Compatibility patch failed.' }
& $python -c "from comtypes.client import GetModule; GetModule('UIAutomationCore.dll'); from quickspeak.tray import icon_image; icon_image().save('quickspeak.ico')"
if ($LASTEXITCODE -ne 0) { throw 'Build resource generation failed.' }
if ($SkipHardwareTests) { $env:QUICKSPEAK_SKIP_HARDWARE_TESTS = '1' }
& $python -m unittest discover -s tests -v
if ($LASTEXITCODE -ne 0) { throw 'Tests failed.' }
& $python -m PyInstaller --noconfirm QuickSpeak.spec
if ($LASTEXITCODE -ne 0) { throw 'Packaging failed.' }
Copy-Item README.md, LICENSE, THIRD_PARTY_NOTICES.md -Destination dist\QuickSpeak
Copy-Item docs -Destination dist\QuickSpeak -Recurse -Force
& $python tools\collect_licenses.py
if ($LASTEXITCODE -ne 0) { throw 'License collection failed.' }
Write-Host 'Built dist\QuickSpeak\QuickSpeak.exe. Distribute the complete QuickSpeak folder.'
