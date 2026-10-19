# Voice model and offline installation

QuickSpeak uses **KittenML/kitten-tts-nano-0.8-int8**, English, CPU only, 24 kHz.
It does not use the newer KittenTTS 2 model. Jasper is the default voice. INT8 was
tested successfully; there is no automatic FP32 download or GPU dependency.

## Automatic installation (recommended)

Run `install.cmd` or `setup.ps1`. The three model files are fetched automatically,
or reused from an existing matching Hugging Face cache, then verified using
SHA-256. Starting the app also prepares missing files in a background worker.

Default location: **`%LOCALAPPDATA%\QuickSpeak\model`**.
Paste that path into File Explorer's address bar to open it.

## Manual download / air-gapped computer

Download these files on an online computer, using this exact revision:
`84781d74e29ee25217551556398b42f80593a813`.

| File | Direct download |
|---|---|
| `config.json` | [Download config](https://huggingface.co/KittenML/kitten-tts-nano-0.8-int8/resolve/84781d74e29ee25217551556398b42f80593a813/config.json?download=true) |
| `kitten_tts_nano_v0_8.onnx` | [Download model](https://huggingface.co/KittenML/kitten-tts-nano-0.8-int8/resolve/84781d74e29ee25217551556398b42f80593a813/kitten_tts_nano_v0_8.onnx?download=true) |
| `voices.npz` | [Download voices](https://huggingface.co/KittenML/kitten-tts-nano-0.8-int8/resolve/84781d74e29ee25217551556398b42f80593a813/voices.npz?download=true) |

Create `%LOCALAPPDATA%\QuickSpeak\model` on the destination computer and copy the
three files directly inside it, preserving their names. Do not nest another model
directory inside it. Total file size is about **26.4 MiB**.

The runtime must also be installed. For a fully offline destination, build the
standalone folder on an online Windows x64 computer, then transfer the **entire**
`dist\QuickSpeak` folder plus those three model files. Copying a source checkout
alone does not install Python dependencies offline.

## Verify checksums

The source of truth is [`quickspeak/model.lock.json`](../quickspeak/model.lock.json).
From the repository directory:

```powershell
$lock = Get-Content .\quickspeak\model.lock.json -Raw | ConvertFrom-Json
$modelFolder = Join-Path $env:LOCALAPPDATA 'QuickSpeak\model'
foreach ($entry in $lock.sha256.PSObject.Properties) {
    $file = Join-Path $modelFolder $entry.Name
    $actual = (Get-FileHash -LiteralPath $file -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($actual -ne $entry.Value) { throw "Checksum mismatch: $($entry.Name)" }
    Write-Host "Verified $($entry.Name)"
}
```

The app performs these checks itself before loading. A matching revision avoids
silently changing voices or model behavior when upstream updates its main branch.

## Custom cache / portable use

In the PowerShell session that launches QuickSpeak:

```powershell
$env:QUICKSPEAK_HOME = Join-Path $PWD 'portable-data'
.\run.ps1
```

The model then lives in `portable-data\model` and preferences in
`portable-data\settings.json`. Keep this environment variable consistent when
installing and launching. Launch-at-login does not preserve a temporary shell
environment override; use the default per-user directory for that feature.

## Recover from an interrupted or corrupt download

Exit QuickSpeak, move the three model files to a backup directory, then rerun
`setup.ps1` while online. Keep files from one revision together. Never replace the
ONNX file with a differently named model or edit the hashes to accept a mismatch.

Completed verified files are used without network access. Missing or corrupt files
require a valid offline copy or a download. No selected text is sent to Hugging Face.

The model retains its [Apache-2.0 license](https://huggingface.co/KittenML/kitten-tts-nano-0.8-int8).
