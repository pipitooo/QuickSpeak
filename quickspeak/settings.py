import json
import os
from dataclasses import asdict, dataclass
from pathlib import Path
import subprocess
import sys
import winreg

VOICES = ('Bella', 'Jasper', 'Luna', 'Bruno', 'Rosie', 'Hugo', 'Kiki', 'Leo')

def data_dir():
    path = Path(os.environ.get('QUICKSPEAK_HOME', Path(os.environ['LOCALAPPDATA']) / 'QuickSpeak'))
    path.mkdir(parents=True, exist_ok=True)
    return path

@dataclass
class Settings:
    voice: str = 'Jasper'
    speed: float = 1.0
    volume: float = 0.8
    shortcut: str = 'Ctrl+Alt+R'

    @classmethod
    def load(cls):
        try:
            raw = json.loads((data_dir() / 'settings.json').read_text('utf-8'))
            s = cls(**{k: v for k, v in raw.items() if k in cls.__dataclass_fields__})
            if s.voice not in VOICES or not 0.5 <= float(s.speed) <= 2 or not 0 <= float(s.volume) <= 1:
                raise ValueError('Invalid settings')
            from .hotkeys import parse_shortcut
            parse_shortcut(s.shortcut)
            return s
        except (OSError, ValueError, TypeError, AttributeError):
            return cls()

    def save(self):
        path = data_dir() / 'settings.json'
        temp = path.with_suffix('.tmp')
        temp.write_text(json.dumps(asdict(self), indent=2), 'utf-8')
        temp.replace(path)

RUN_KEY = r'Software\Microsoft\Windows\CurrentVersion\Run'

def startup_enabled():
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY) as key:
            return bool(winreg.QueryValueEx(key, 'QuickSpeak')[0])
    except OSError:
        return False

def set_startup(enabled):
    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, RUN_KEY) as key:
        if enabled:
            args = [sys.executable] if getattr(sys, 'frozen', False) else [str(Path(sys.executable).with_name('pythonw.exe')), str(Path(__file__).resolve().parents[1] / 'main.py')]
            winreg.SetValueEx(key, 'QuickSpeak', 0, winreg.REG_SZ, subprocess.list2cmdline(args))
        else:
            try:
                winreg.DeleteValue(key, 'QuickSpeak')
            except FileNotFoundError:
                pass
