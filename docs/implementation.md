# Implementation

QuickSpeak is a Windows-only Python/Tk application. main.py dispatches normal
startup or explicit diagnostics. quickspeak/app.py coordinates the tray, window,
selection worker, inference worker and audio player. Preferences live in
%LOCALAPPDATA%\QuickSpeak; QUICKSPEAK_HOME overrides that directory.

## Selection and clipboard

hotkeys.py uses Windows RegisterHotKey. selection.py requests selected text
through UI Automation in a bounded child process. If that fails, it uses Ctrl+C
and requires a fresh clipboard sequence before accepting text. Supported formats
are restored only if no later copy occurred. Unsupported handle-based formats
are refused. This cannot preserve every Office/OLE object or protected content.

## Local speech

tts.py verifies model files against model.lock.json, creates a CPU-only ONNX
session and keeps it loaded between requests. It uses at most four inference
threads with idle spinning disabled. Text is split into bounded sentence chunks.
Generation IDs discard stale output after Stop or a new request; an already
running inference call must finish before the next starts.

audio.py feeds 24 kHz mono sound through a bounded queue. Pause and volume act on
playback; voice and speed apply to subsequent generation. Tk updates use its main
thread. Shutdown signals workers and closes playback, tray and hotkey resources.

## Dependencies and packaging

setup.ps1 installs pinned dependencies and KittenTTS 0.8.1 without its default
dependency graph. tools/patch_kitten.py removes an audited unused Misaki import.
The adapter uses upstream ONNX generation with explicit CPU options. PyTorch and
spaCy are not needed. This version-specific compatibility patch needs retesting
when upgraded. QuickSpeak.spec bundles UI Automation bindings, eSpeak data and
native libraries. Model weights are downloaded separately.

## Privacy

Normal operation does not log passages or retain reading history. Settings store
preferences. Diagnostic tools use synthetic text, except tools/capture_check.py,
which prints selected text and must only be used with test content. Dependency
and model downloads contact their hosts; inference needs no network. Windows
clipboard history and other apps may independently retain copied content.
