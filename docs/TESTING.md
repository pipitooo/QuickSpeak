# Testing and known limits

Run from the repository root after setup:

```powershell
.\.runtime\Scripts\python.exe -m unittest discover -s tests -v
.\.runtime\Scripts\python.exe tools\verify_model.py
.\.runtime\Scripts\python.exe main.py --self-test --report artifacts\benchmark.json --wav artifacts\benchmark.wav
```

Tests cover settings, chunking, cancellation/replacement, hotkey conflicts,
bounded playback and pause behavior. Model verification exercises eight voices,
speed extremes, finite audio, warm reuse and offline loading with socket
connections blocked. Diagnostics speak only a synthetic phrase.

On a system without interactive desktop/audio hardware:

```powershell
$env:QUICKSPEAK_SKIP_HARDWARE_TESTS = '1'
.\.runtime\Scripts\python.exe -m unittest discover -s tests -v
.\.runtime\Scripts\python.exe main.py --self-test --no-audio --report artifacts\headless.json --wav artifacts\headless.wav
Remove-Item Env:QUICKSPEAK_SKIP_HARDWARE_TESTS
```

Three of thirteen tests are skipped in that mode. CI uses it, verifies the model and
tests synthesis in the built EXE. CI does not establish physical playback,
clipboard behavior in other apps, startup-at-login or visual usability.

## Manual checks

Use synthetic text. Select text in Notepad and a browser, press the shortcut,
replace a long reading, then test Stop, Pause/Resume, voice/speed/volume and empty
selection. Check clipboard restoration during fallback. Test the manual text box,
close-to-tray and Exit. Check a second launch does not create another instance.
Test launch-at-login separately only when intending to change that preference.

While another app has focus, press Ctrl+Alt+I twice to pause then resume the same
reading. While idle it does nothing. Change either shortcut in settings, save,
and restart to check persistence. Conflicting shortcuts must show an error and
keep the previous working bindings.

Original Windows 11 checks covered Notepad/Opera, Unicode, UI Automation and
fallback, synthetic text/HTML/RTF restoration, source UI and packaged offline
audio. [Historical results](../TEST_RESULTS.md) record host measurements and
limits. Reports and WAVs stay local and are not committed.

Windows 10, Word, PDF viewers, protected/elevated content, full Office/OLE
clipboard preservation, device unplug/replug, actual sign-in startup, a separate
clean consumer PC and packaged UI Automation end-to-end remain unverified.
English speech is supported; scanned PDFs need external OCR.
