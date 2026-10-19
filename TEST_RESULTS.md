# QuickSpeak test results — 19 October 2026

Test host: Windows 11 x64, build 26200; AMD Ryzen 5 3600 (6 cores / 12 logical
processors); Python 3.11.9. Audio: Headphones (Arctis 5 Game), 24 kHz mono.
Python's platform string calls this `Windows-10-10.0.26200-SP0`; build 26200 is the
actual host build. Results are specific to this machine.

## Measured performance

Fixed phrase: “Hello! QuickSpeak is working.” Jasper, speed 1.0; generated audio
length 2.917 seconds. The model was loaded before each three-run series.

| Measurement | Result |
|---|---:|
| Development model load | 1.931 s |
| Development synthesis | 0.233–0.239 s |
| Development estimated first DAC audio | 0.377–0.389 s |
| Delivered binary model load, including imports/hash verification | 4.289 s |
| Delivered binary synthesis | 0.270–0.336 s |
| Delivered binary estimated first DAC audio | 0.417–0.488 s |
| Packaged model-loaded diagnostic working set | 157.8 MiB |
| Packaged diagnostic working set after speech | 208.2 MiB |
| Running packaged tray/UI after preload | 178.9 MiB |
| Development tray/UI after real selection playback | about 223 MiB |
| Two-second idle diagnostic CPU sample | 0.0% of one core, at sample resolution |
| App folder including runtime and notices | about 181.4 MiB |
| Model files, stored separately per user | 26.37 MiB |

Audio timing uses `perf_counter` plus PortAudio's
`outputBufferDacTime - currentTime`. It estimates when the first buffer reaches
the device. It is **not** an acoustic/microphone measurement, does not include
human keypress duration, and should not be generalized to other passages/devices.

The interactive browser run measured about **0.812 s** from the app's shortcut
handler/Stop status to estimated first device audio. The Notepad fallback run
measured about **0.859 s**. That includes selection capture and UI dispatch;
these are single observations, not a latency distribution.

## Executed checks

- Ten automated tests passed: sentence/Unicode chunking; shortcut syntax;
  real Windows shortcut conflict/replacement/release; stale-clipboard rejection;
  known-empty selection; cancellation during in-flight synthesis; single-instance
  mutex; settings round-trip/corrupt defaults; simulated audio-device failure;
  real-device pause, stop, replacement and stale-generation rejection.
- All eight voices generated finite audio. Speed 0.5 and 2.0 passed. Calling load
  again reused the existing model object. `socket.connect` was blocked during
  model load and synthesis: offline tests passed. No torch module was loaded.
- Generated WAV files and played them through sounddevice on the actual output
  device. This verifies audio delivery, not a human listening assessment.
- Fresh-cache Hugging Face downloads passed, including the final direct-to-cache
  path and SHA-256 verification. Standard per-user setup passed.
- Actual Notepad selection with “Café” returned through UI Automation in 0.320 s,
  with clipboard sequence unchanged. Empty Notepad selection returned empty
  through UI Automation in 0.284 s, with clipboard unchanged.
- Actual Opera page selection returned through UI Automation in 0.290 s,
  with clipboard unchanged. The page contained synthetic local test text.
- Ctrl+Alt+R was exercised in the running app in Opera and Notepad. Opera used
  UI Automation; Notepad also exercised clipboard fallback. Playback completed.
- Forced Ctrl+C fallback captured the Notepad test selection and restored all
  synthetic Unicode, HTML, RTF and Windows-derived text/locale formats exactly.
  A copy that did not advance the clipboard sequence was rejected, as intended.
- Interactive application shutdown reported no remaining `audio`, `synthesis`,
  `hotkey`, `selection` or `tray` worker threads.
- PyInstaller executable ran from the system temporary directory, with no
  activated development environment and `HF_HUB_OFFLINE=1`; model/audio checks
  passed. PE subsystem is 2 (Windows GUI), so it has no console window.
- Setup and the development launcher were executed. Launch-at-login was checked
  and remained **off**. No startup registry entry was enabled during testing.
- Source settings UI was visually inspected. A clipped status line was found and
  fixed by enlarging the minimum/default height, then visually rechecked: all
  controls and the Ready status fit. Manual Read, Pause, Stop and Exit were
  clicked successfully in the corrected source UI. The compiled executable's
  desktop-tool visual access timed out; its process was responsive and its
  executable diagnostics passed.

Packaged UI Automation end-to-end remains unverified. Source selection was
verified in both applications; the final binary passed its offline audio test.

The following evidence files are generated locally and are not committed.

Evidence: `artifacts/development-benchmark.json`,
`artifacts/final-packaged-benchmark.json`, `artifacts/model-verification.json`,
`artifacts/desktop-integration.json`, `artifacts/package-metrics.json`.
The delivered binary's last rerun is `artifacts/delivery-benchmark.json`;
archive integrity and final sizes are in `artifacts/delivery-package.json`.
Only synthetic test text appears in generated WAVs. The desktop report contains
status, character counts and timings, not the selected passage.

## Not established by these tests

Windows 10 on a separate machine; Word; PDF viewers; protected/elevated sources;
full Office/OLE rich clipboard preservation; hardware unplug/replug; actual
sign-out/sign-in startup execution; a completely clean second PC; microphone
latency or subjective voice quality. These are not claimed as tested.

Full rich clipboard preservation is not claimed. Unsupported handle formats
are refused, and later clipboard updates are left alone. A slow source copy or
clipboard manager can still interfere. See the README's limits and recovery notes.
