"""Remove exactly one unused import from KittenTTS 0.8.1.

The ONNX implementation uses phonemizer directly; misaki.en/espeak are never
referenced. Avoid installing misaki[en], spaCy and torch for this unused import.
"""
from importlib.metadata import distribution

dist = distribution('kittentts')
assert dist.version == '0.8.1', 'Re-audit compatibility before changing KittenTTS version'
path = dist.locate_file('kittentts/onnx_model.py')
source = path.read_text('utf-8')
line = 'from misaki import en, espeak'
replacement = '# QuickSpeak: unused misaki import removed (see tools/patch_kitten.py).'
if line in source:
    path.write_text(source.replace(line, replacement, 1), 'utf-8')
elif replacement not in source:
    raise RuntimeError('Unexpected KittenTTS source; refusing to patch')
print('KittenTTS 0.8.1 minimal ONNX compatibility patch verified.')
