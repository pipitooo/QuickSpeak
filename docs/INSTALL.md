# Installation, updates and removal

## Requirements

- Windows 10 or Windows 11 **x64**, with an interactive desktop and audio output.
- Python **3.11 x64**, with pip, the Python launcher and Tcl/Tk (for source installs).
- Internet access for dependency/model installation; no account or API key.
- Allow roughly 1 GB free while installing/building. The model is about 26.4 MiB;
  the previously tested standalone app was about 181 MiB. Source environments,
  installer caches and build intermediates need extra space.

Windows 11 is tested. ARM64-native builds, 32-bit Windows and macOS/Linux are not
supported. Do not install QuickSpeak globally with `pip install -r requirements.txt`;
use its setup script and isolated environment.

## Download ZIP (no Git required)

1. Open https://github.com/pipitooo/QuickSpeak and choose **Code → Download ZIP**.
2. Extract everything. Do not run files from inside the ZIP preview.
3. Keep the extracted folder in a permanent location, such as your user Apps folder.
4. Double-click `install.cmd`. It runs the supplied PowerShell setup script.
5. Wait for model download/loading to complete; then double-click `start.cmd`.

The tray icon may be under Windows' overflow arrow. Double-click it to open settings.
The initial install can take several minutes; the model download itself is small,
but dependencies and antivirus scanning also take time. No latency is promised.

## PowerShell / Git

```powershell
git clone https://github.com/pipitooo/QuickSpeak.git
cd QuickSpeak
powershell -NoProfile -ExecutionPolicy Bypass -File .\setup.ps1
.\run.ps1
```

The per-process execution-policy option does not alter your saved policy. If your
organization blocks scripts, contact its administrator rather than weakening its
policy. You can run the Python entry point directly after dependencies are installed:

```powershell
.\.runtime\Scripts\pythonw.exe .\main.py
```

## Python cannot be found

Check `py -3.11 --version`. If the launcher is missing, rerun the Python installer
with the launcher option, or provide your interpreter explicitly:

```powershell
.\setup.ps1 -Python 'C:\Path\To\Python311\python.exe'
```

Setup rejects other Python minor versions, 32-bit Python and missing Tkinter.
If `.runtime` was created with an incompatible interpreter, exit QuickSpeak, rename
that folder to `.runtime-old`, and rerun setup with the correct Python.

## Model download

`setup.ps1` downloads the model by default. `setup.ps1 -SkipModel` installs only
dependencies; the app will then download its model on first launch. Look at the
tray tooltip or open the window to see the current preparation status.

For direct file links, offline copies and hash checks, see [MODELS.md](MODELS.md).
For a failed download, check connectivity to Hugging Face and retry setup or Read.
Do not put proxy passwords or Hugging Face access tokens in this repository. The
model is public and the app explicitly downloads without an account token.

## Everyday use

- Ctrl+Alt+R reads the current selection. A new passage replaces the old one.
- Ctrl+Alt+I pauses the current reading; press it again to resume. Both shortcuts are configurable in settings and must be different.
- An empty selection stops reading and shows a small notification.
- Read Clipboard explicitly reads existing copied text if selection capture fails.
- The manual text box is useful for unsupported applications.
- Voice and speed affect the next reading; volume updates during playback.
- Save settings persists preferences. Closing the window hides it; Exit quits.
- Launch at login must be enabled by you. It uses your user-level Windows Run key.

## Update

Exit QuickSpeak before updating. For a clone, run `git pull --ff-only`, then rerun
`setup.ps1`. For ZIP installs, extract the new source separately and run its setup.
Keep the old folder until the new version starts successfully. Preferences/model
files live separately in `%LOCALAPPDATA%\QuickSpeak` and are reused.

If launch at login was enabled and the app moved, open settings in the new copy
and save with the startup checkbox enabled to update its registered path.

## Uninstall

1. Open settings, uncheck launch at login, click Save settings, then Exit.
2. Delete the extracted/cloned QuickSpeak folder, including its `.runtime` folder.
3. Optionally delete `%LOCALAPPDATA%\QuickSpeak` to remove preferences/model files.

If the app folder was already removed, delete only the `QuickSpeak` value under
`HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Run` using Registry
Editor. Other startup entries are unrelated.

## Troubleshooting

| Symptom | Try |
|---|---|
| Shortcut conflict | Open settings and choose another Ctrl/Alt combination. |
| Nothing selected | Reselect actual text, release modifiers, keep the source focused. |
| Source won't copy | Use the manual box or explicit Read Clipboard. Protected/scanned content is unsupported. |
| Clipboard preservation warning | Use UIA-capable apps or the manual box; unsupported formats are intentionally refused. |
| No sound | Check Windows' default audio device/volume, then Stop and Read again. |
| Model error | Rerun setup; see model repair instructions. |
| Import error after an update | Recreate the isolated environment and run setup. |
| `pip check` reports misaki/spaCy/num2words missing | Expected for the audited KittenTTS patch; see Building. Do not add PyTorch to silence it. |

Include Windows/Python versions, steps and a harmless example when opening an
issue. Do not post your selected private text, clipboard contents or credentials.
