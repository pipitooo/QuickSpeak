from importlib.metadata import distributions
from pathlib import Path
import shutil

destination = Path('dist/QuickSpeak/licenses')
for dist in distributions():
    name = dist.metadata['Name']
    for entry in dist.files or []:
        if '.dist-info' in str(entry) and any(token in entry.name.lower() for token in ('license', 'copying', 'notice')):
            source = Path(dist.locate_file(entry))
            if source.is_file():
                folder = destination / name
                folder.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(source, folder / entry.name)
