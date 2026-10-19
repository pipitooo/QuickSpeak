"""Archive the finished app and source without environments or test passages."""
from pathlib import Path
import hashlib
import json
import shutil
import zipfile

root = Path(__file__).resolve().parents[1]
app = root / 'dist' / 'QuickSpeak'
for name in ('README.md', 'LICENSE', 'TEST_RESULTS.md', 'THIRD_PARTY_NOTICES.md'):
    shutil.copyfile(root / name, app / name)
archive = root / 'dist' / 'QuickSpeak-Windows-x64.zip'
with zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as z:
    for file in sorted(app.rglob('*')):
        if file.is_file():
            z.write(file, file.relative_to(app.parent))
source = root / 'dist' / 'QuickSpeak-source.zip'
with zipfile.ZipFile(source, 'w', zipfile.ZIP_DEFLATED) as z:
    for folder in ('quickspeak', 'tools', 'tests', 'docs', '.github'):
        for file in sorted((root / folder).rglob('*')):
            if file.is_file() and '__pycache__' not in file.parts:
                z.write(file, file.relative_to(root))
    for name in ('main.py', 'setup.ps1', 'run.ps1', 'build.ps1', 'requirements.txt',
                 'requirements-build.txt', 'QuickSpeak.spec', 'quickspeak.ico',
                 'README.md', 'LICENSE', 'CONTRIBUTING.md', 'SECURITY.md',
                 '.gitignore', '.gitattributes', 'install.cmd', 'start.cmd',
                 'TEST_RESULTS.md', 'THIRD_PARTY_NOTICES.md'):
        z.write(root / name, name)
for path in (archive, source):
    with zipfile.ZipFile(path) as z:
        assert z.testzip() is None
metrics = {
    'package_mib': round(sum(f.stat().st_size for f in app.rglob('*') if f.is_file()) / 1048576, 2),
    'zip_mib': round(archive.stat().st_size / 1048576, 2),
    'source_zip_mib': round(source.stat().st_size / 1048576, 2),
    'exe_sha256': hashlib.sha256((app / 'QuickSpeak.exe').read_bytes()).hexdigest(),
    'zip_sha256': hashlib.sha256(archive.read_bytes()).hexdigest(),
    'zip_integrity': 'passed',
}
(root / 'artifacts').mkdir(exist_ok=True)
(root / 'artifacts' / 'delivery-package.json').write_text(json.dumps(metrics, indent=2), 'utf-8')
(root / 'dist' / 'SHA256SUMS.txt').write_text(
    metrics['exe_sha256'] + '  QuickSpeak/QuickSpeak.exe\n' +
    metrics['zip_sha256'] + '  QuickSpeak-Windows-x64.zip\n', 'utf-8')
print(json.dumps(metrics, indent=2))
