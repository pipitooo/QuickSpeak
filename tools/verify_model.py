"""Verify voices/speeds and offline loading with network calls blocked."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from unittest.mock import patch
import json
import time
import numpy as np
from quickspeak.tts import Model
from quickspeak.settings import VOICES

results = []
Path('artifacts').mkdir(exist_ok=True)
with patch('socket.socket.connect', side_effect=AssertionError('Unexpected network access')):
    model = Model()
    model.load()
    original = id(model.model)
    for voice in VOICES:
        start = time.perf_counter()
        samples = model.generate('Hello, café! The test has 42 words.', voice, 1.15)
        assert len(samples) > 1000 and np.isfinite(samples).all()
        results.append({'voice':voice, 'seconds':round(time.perf_counter()-start,3), 'samples':len(samples)})
    for speed in (0.5, 2.0):
        samples = model.generate('QuickSpeak speed test.', 'Jasper', speed)
        assert np.isfinite(samples).all() and len(samples) > 0
    model.load()
    assert id(model.model) == original
assert 'torch' not in sys.modules
Path('artifacts/model-verification.json').write_text(json.dumps({'voices':results, 'offline_socket_guard':'passed', 'warm_reuse':'passed', 'speed_extremes':'passed'}, indent=2))
print('Eight voices, speed extremes, finite audio, warm reuse and offline network guard passed.')
