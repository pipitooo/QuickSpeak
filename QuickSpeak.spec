from PyInstaller.utils.hooks import collect_data_files, collect_dynamic_libs, collect_submodules, copy_metadata

datas = [('quickspeak/model.lock.json', 'quickspeak')]
binaries = []
for package in ['espeakng_loader', 'phonemizer', 'language_tags', 'jsonschema_specifications']:
    datas += collect_data_files(package)
    binaries += collect_dynamic_libs(package)
for package in ['kittentts', 'phonemizer-fork', 'huggingface_hub', 'sounddevice']:
    datas += copy_metadata(package)
hidden = ['pystray._win32', 'win32clipboard', 'win32gui', 'win32con']
hidden += collect_submodules('comtypes.gen')
hidden += collect_submodules('phonemizer.backend')
a = Analysis(['main.py'], pathex=[], binaries=binaries, datas=datas,
    hiddenimports=hidden, hookspath=[], hooksconfig={}, runtime_hooks=[],
    excludes=['torch', 'spacy', 'misaki', 'scipy', 'matplotlib', 'pytest', 'IPython'], noarchive=False)
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, [], exclude_binaries=True, name='QuickSpeak', debug=False,
    bootloader_ignore_signals=False, strip=False, upx=False, console=False,
    disable_windowed_traceback=False, icon='quickspeak.ico')
coll = COLLECT(exe, a.binaries, a.datas, strip=False, upx=False, name='QuickSpeak')
