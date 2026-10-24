# Contributing to QuickSpeak

Bug reports, documentation fixes and focused pull requests are welcome.

## Local setup

Use Windows x64 and Python 3.11. Clone your fork, run `setup.ps1`, then
`run.ps1 -Show`. Follow [Installation](docs/INSTALL.md) for prerequisites.

```powershell
.\.runtime\Scripts\python.exe -m unittest discover -s tests -v
.\.runtime\Scripts\python.exe tools\verify_model.py
```

The second command requires the model files. On a headless runner, set
`QUICKSPEAK_SKIP_HARDWARE_TESTS=1`; the three hardware-dependent tests will be marked
skipped, not passed. Clear it before claiming desktop/audio testing.

## Design constraints

- Keep selected text local. No analytics, passage logs or cloud speech APIs.
- Keep CPU-only inference; do not add PyTorch or GPU dependencies.
- Preserve the UI Automation-first approach. Never type/paste into source apps.
- Check generation IDs on queued synthesis/audio and keep buffers bounded.
- Tkinter work belongs on the UI thread; background workers post events.
- Keep startup opt-in and retain the previous hotkey when registration fails.
- Test error paths and races, not only successful speech generation.

## Pull requests

Explain the problem, changed behavior and tests actually executed. Use harmless
synthetic passages in tests. Never attach private clipboard content, tokens,
personal model caches or environment directories. Include regression tests for
functional fixes; update documentation when installation or behavior changes.

Model/runtime updates must explicitly update dependency pins, audit the KittenTTS
compatibility patch, validate model file hashes and retest voices, offline loading,
packaging and cancellation. Do not loosen all pins to fix one installation error.

By contributing original code, you agree to license it under this repository's
GPL-3.0-or-later license. Third-party code must retain its license and attribution.
