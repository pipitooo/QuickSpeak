param([switch]$SkipModel, [string]$Python = '', [string]$EnvironmentPath = '.runtime')
$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot
$env:PYTHONUTF8 = '1'
if ($env:OS -ne 'Windows_NT') { throw 'QuickSpeak requires Windows 10 or Windows 11 x64.' }
$runtimePython = Join-Path $EnvironmentPath 'Scripts\python.exe'
if (-not (Test-Path $runtimePython)) {
    if ($Python) {
        & $Python -m venv $EnvironmentPath
    } elseif (Get-Command py -ErrorAction SilentlyContinue) {
        py -3.11 -m venv $EnvironmentPath
    } else {
        throw 'Install Python 3.11 x64 from https://www.python.org/downloads/windows/ including its launcher and Tcl/Tk, or pass -Python C:\Path\To\python.exe.'
    }
    if ($LASTEXITCODE -ne 0) { throw 'Could not create the environment. Install Python 3.11 x64 with Tcl/Tk, then rerun setup.' }
}
$python = (Resolve-Path $runtimePython).Path
& $python -c "import sys,struct,tkinter; assert sys.version_info[:2] == (3,11) and struct.calcsize('P') == 8, 'Python 3.11 x64 is required'"
if ($LASTEXITCODE -ne 0) { throw 'Use a new environment with Python 3.11 x64 and Tkinter.' }
& $python -m pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) { throw 'Dependency installation failed.' }
# Upstream declares unused NLP dependencies. Install the audited ONNX wheel
# separately so pip does not pull in PyTorch/spaCy.
& $python -m pip install --no-deps 'https://github.com/KittenML/KittenTTS/releases/download/0.8.1/kittentts-0.8.1-py3-none-any.whl'
if ($LASTEXITCODE -ne 0) { throw 'KittenTTS installation failed.' }
& $python tools\patch_kitten.py
if ($LASTEXITCODE -ne 0) { throw 'KittenTTS compatibility check failed.' }
& $python -c "from comtypes.client import GetModule; GetModule('UIAutomationCore.dll')"
if ($LASTEXITCODE -ne 0) { throw 'Windows UI Automation initialization failed.' }
if (-not $SkipModel) {
    & $python -c "from quickspeak.tts import Model; Model(print).load()"
    if ($LASTEXITCODE -ne 0) { throw 'Model setup failed. Re-run setup when online, or launch QuickSpeak to retry.' }
}
Write-Host 'QuickSpeak is ready. Run .\run.ps1 or build with .\build.ps1.'
