# QuickSpeak

**Select text. Press Ctrl+Alt+R. Hear it aloud — locally.**

[![Windows build](https://github.com/pipitooo/QuickSpeak/actions/workflows/windows.yml/badge.svg)](https://github.com/pipitooo/QuickSpeak/actions/workflows/windows.yml)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](LICENSE)

QuickSpeak is an open-source Windows tray utility powered by **KittenTTS Nano INT8**. It runs on your CPU, keeps the voice model warm, and works offline after setup. No account, API key, cloud speech service, GPU, or PyTorch is required.

> **Early release:** Windows 11, Notepad and Opera were tested. Windows 10 is a target but has not been tested on a separate machine. Word and PDF compatibility depends on the application exposing text or permitting copying. See [tested behavior and limitations](docs/TESTING.md).

## Install

### 1. Install Python

Install **Python 3.11, Windows 64-bit**, including **Tcl/Tk and IDLE**, **pip**, and the **Python launcher** from [python.org](https://www.python.org/downloads/windows/). Python 3.11.9 is the tested version. Newer Python versions are not currently supported.

### 2. Download QuickSpeak

Use **Code → Download ZIP** on [this repository](https://github.com/pipitooo/QuickSpeak), then extract the entire ZIP into a folder you intend to keep. Or clone it:

```powershell
git clone https://github.com/pipitooo/QuickSpeak.git
cd QuickSpeak
```

### 3. Install dependencies and the model

Double-click **`install.cmd`** inside the extracted folder. Keep the installation window open until it says installation is complete.

Setup creates a private Python environment, installs the pinned dependencies, and automatically downloads and verifies the model. Internet access is needed for this step. No administrator access is normally needed.

Prefer PowerShell?

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\setup.ps1
```

The execution-policy option applies only to this installer process; it does not change your saved Windows policy. On a managed computer, follow your organization's script policy.

### 4. Start reading

Double-click **`start.cmd`**. QuickSpeak starts in the system tray without a terminal window. Find its blue speaker icon under the tray overflow arrow if it is hidden.

1. Select text in Notepad or a browser.
2. Press **Ctrl+Alt+R**, then release the keys.
3. Press **Ctrl+Alt+I** to pause; press it again to resume from the same position.
4. To stop, choose **Stop Reading** from the tray menu or click **Stop** in the window.

Double-click the tray icon for the manual text box, voice, speed, volume, pause/resume, shortcut and startup settings. Launch at login is **off by default**. Closing the window hides it; **Exit** quits.

**No hosted EXE release is published yet.** The source installer above is the supported public installation route. To make a standalone EXE locally, see [Building](docs/BUILDING.md). Do not download an executable from an unrelated repository.

## Model installation and offline use

The default model is [`KittenML/kitten-tts-nano-0.8-int8`](https://huggingface.co/KittenML/kitten-tts-nano-0.8-int8), about **26.4 MiB** including voices. Setup downloads these three files automatically:

- `config.json`
- `kitten_tts_nano_v0_8.onnx`
- `voices.npz`

They are stored in **`%LOCALAPPDATA%\QuickSpeak\model`**. The model revision and SHA-256 checksums are pinned in [model.lock.json](quickspeak/model.lock.json). There is no model download on subsequent launches when the verified files are present.

[Model guide](docs/MODELS.md) covers direct download links, manual/offline installation, checksums, download failures and moving the cache. [Installation guide](docs/INSTALL.md) covers Python issues, updates, uninstalling and troubleshooting.

## Features

- Global, customizable Windows shortcut; default **Ctrl+Alt+R**.
- Global, customizable pause/resume shortcut; default **Ctrl+Alt+I**. Both shortcuts can be changed in settings and must be different.
- UI Automation selection capture first; conservative Ctrl+C fallback.
- Background model loading, sentence-chunked speech and bounded audio buffering.
- Stop, pause/resume, and replacement of the current reading.
- Eight voices: Jasper (default), Bella, Luna, Bruno, Rosie, Hugo, Kiki and Leo.
- Speed and volume controls; manual text box; explicit Read Clipboard action.
- Single-instance protection and opt-in launch at login.
- CPU-only ONNX inference and 24 kHz local audio.

## Privacy and limitations

Selected text is processed locally. QuickSpeak does not send it to a server, store passage history or add analytics. Settings contain preferences only. First-run downloads contact PyPI, GitHub and Hugging Face; subsequent speech generation is offline. Windows clipboard history and other clipboard-monitoring apps remain outside QuickSpeak's control.

The fallback checks for a fresh clipboard update before reading and restores supported formats when no later copy has occurred. Unicode/text, HTML and RTF were tested with synthetic data; **complete rich clipboard preservation is not claimed**. Unsupported handle-based formats are refused. Never assume protected documents, scanned PDFs, elevated apps or every Office clipboard object will work.

The selected model speaks English. Unicode input is accepted, but this is not a multilingual model or OCR. See [implementation details](docs/implementation.md) for capture, cancellation, privacy and shutdown behavior.

## Development

```powershell
# Set up without downloading a model yet:
.\setup.ps1 -SkipModel
# Open the window immediately:
.\run.ps1 -Show
# Run all tests on an interactive Windows machine with audio:
.\.runtime\Scripts\python.exe -m unittest discover -s tests -v
# Build a standalone folder:
.\build.ps1
```

Hosted CI skips only the real-desktop hotkey and physical-audio tests; it runs the remaining tests, downloads/verifies the model, generates speech, checks offline loading, builds the EXE, and tests packaged synthesis without requiring an audio device. CI does not publish executables.

Read [Contributing](CONTRIBUTING.md), [Building](docs/BUILDING.md), [Testing](docs/TESTING.md) and [Security](SECURITY.md). Report reproducible problems using [GitHub Issues](https://github.com/pipitooo/QuickSpeak/issues); do not include private passages or clipboard contents.

## License and credits

QuickSpeak is licensed under **GPL-3.0-or-later**. See [LICENSE](LICENSE). Copyright © 2026 QuickSpeak contributors.

Thanks to [KittenML](https://github.com/KittenML/KittenTTS), [ONNX Runtime](https://onnxruntime.ai/), [eSpeak NG](https://github.com/espeak-ng/espeak-ng), phonemizer, sounddevice, Tkinter and pystray. Their components retain their own licenses; the KittenTTS model is Apache-2.0. See [third-party notices](THIRD_PARTY_NOTICES.md).
