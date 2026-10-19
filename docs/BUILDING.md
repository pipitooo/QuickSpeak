# Building

Use Windows x64 and Python 3.11 x64 with Tk. From the repository root:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\setup.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File .\build.ps1
```

The build installs pinned tools, generates the icon and UI Automation bindings,
runs tests, and creates dist\QuickSpeak\QuickSpeak.exe. Keep the entire folder,
including _internal and licenses. The EXE needs no separate Python installation,
but needs the [model](MODELS.md). It is unsigned.

Exit any running copy of the built app before rebuilding; Windows locks its EXE.

On a runner without desktop/audio hardware, use build.ps1 -SkipHardwareTests.
This skips only native hotkey registration and physical playback tests.

## Packaged synthesis test

After setup has downloaded the model:

```powershell
$env:HF_HUB_OFFLINE = '1'
$exe = (Resolve-Path .\dist\QuickSpeak\QuickSpeak.exe).Path
$report = Join-Path $PWD 'artifacts\packaged.json'
$wav = Join-Path $PWD 'artifacts\packaged.wav'
Start-Process -FilePath $exe -ArgumentList @('--self-test', '--no-audio', '--report', "`"$report`"", '--wav', "`"$wav`"") -Wait
Get-Content $report
```

Require status: passed, frozen: true, and torch_imported: false. Omit --no-audio
to exercise an output device. Audio-free checks do not verify playback or tray UI.

## Public releases

The repository distributes source. CI tests packaging without uploading binaries.
tools/package_delivery.py creates local archives; it does not publish them.

Before distributing binaries, prepare matching application source, build scripts,
patches and the dependency sources required by bundled licenses. A ZIP of this
repository alone does not contain all corresponding source for GPL dependencies.
Preserve notices/licenses and provide corresponding source through a compliant
distribution method. See [third-party notices](../THIRD_PARTY_NOTICES.md).
Test the package on a clean Windows machine, including selection and audio,
before tagging a release. Model weights retain their Apache-2.0 license.
