import json
import hashlib
import os
from pathlib import Path
import re
import shutil
import threading
import queue

from .settings import data_dir

REPO = 'KittenML/kitten-tts-nano-0.8-int8'

def chunks(text, limit=220):
    """Bound each inference, retaining sentence punctuation and Unicode."""
    for sentence in re.split(r'(?<=[.!?])\s+|\n+', text.strip()):
        while len(sentence) > limit:
            boundary = sentence.rfind(' ', 0, limit + 1)
            if boundary <= 0:
                boundary = limit
            yield sentence[:boundary].strip()
            sentence = sentence[boundary:].lstrip()
        if sentence.strip():
            yield sentence.strip()

class Model:
    def __init__(self, status=lambda text: None):
        self.status = status
        self.model = None

    def load(self):
        if self.model is not None:
            return
        os.environ['HF_HUB_DISABLE_TELEMETRY'] = '1'
        os.environ['HF_HUB_DISABLE_PROGRESS_BARS'] = '1'
        os.environ['HF_HUB_ETAG_TIMEOUT'] = '10'
        os.environ['HF_HUB_DOWNLOAD_TIMEOUT'] = '20'
        from huggingface_hub import hf_hub_download
        import espeakng_loader
        from phonemizer.backend.espeak.wrapper import EspeakWrapper
        from kittentts.onnx_model import KittenTTS_1_Onnx
        import onnxruntime as ort
        import numpy as np

        root = data_dir() / 'model'
        root.mkdir(exist_ok=True)
        lock = json.loads((Path(__file__).with_name('model.lock.json')).read_text('utf-8'))
        revision = lock['revision']
        def valid(path):
            if not path.is_file():
                return False
            with path.open('rb') as stream:
                return hashlib.file_digest(stream, 'sha256').hexdigest() == lock['sha256'].get(path.name)
        def get_file(name):
            if Path(name).name != name:
                raise ValueError('Unsafe model filename')
            target = root / name
            if valid(target):
                return target
            self.status(f'Preparing model: {name} (first use may download files)…')
            try:
                cached = hf_hub_download(REPO, name, revision=revision, local_files_only=True, token=False)
            except Exception:
                cached = hf_hub_download(REPO, name, revision=revision, local_dir=str(root), force_download=target.exists(), token=False)
            if Path(cached).resolve() != target.resolve():
                temp = target.with_suffix(target.suffix + '.partial')
                shutil.copyfile(cached, temp)
                temp.replace(target)
            if not valid(target):
                raise ValueError('Model integrity check failed; remove the damaged model file and retry.')
            return target

        config = json.loads(get_file('config.json').read_text('utf-8'))
        model_path, voices_path = get_file(config['model_file']), get_file(config['voices'])
        self.status('Loading the local voice model…')
        EspeakWrapper.set_library(espeakng_loader.get_library_path())
        EspeakWrapper.set_data_path(espeakng_loader.get_data_path())
        # Initialize the same 0.8.1 model with explicit CPU session options.
        # Its constructor offers no session-options argument; populate only
        # those constructor fields, using its original phonemizer/tokenizer.
        from kittentts.onnx_model import TextCleaner, TextPreprocessor
        import phonemizer
        instance = KittenTTS_1_Onnx.__new__(KittenTTS_1_Onnx)
        options = ort.SessionOptions()
        options.intra_op_num_threads = min(4, os.cpu_count() or 2)
        options.inter_op_num_threads = 1
        options.add_session_config_entry('session.intra_op.allow_spinning', '0')
        options.add_session_config_entry('session.inter_op.allow_spinning', '0')
        instance.session = ort.InferenceSession(str(model_path), sess_options=options, providers=['CPUExecutionProvider'])
        instance.model_path = str(model_path)
        instance.voices = np.load(voices_path)
        instance.phonemizer = phonemizer.backend.EspeakBackend(language='en-us', preserve_punctuation=True, with_stress=True)
        instance.text_cleaner = TextCleaner()
        instance.speed_priors = config.get('speed_priors', {})
        instance.voice_aliases = config.get('voice_aliases', {})
        instance.available_voices = list(instance.voices.keys())
        instance.all_voice_names = list(instance.voice_aliases)
        instance.preprocessor = TextPreprocessor(remove_punctuation=False, remove_urls=False, remove_emails=False, remove_html=False)
        self.model = instance
        self.status('Ready · local voices loaded')

    def generate(self, text, voice, speed):
        # Avoid the public wrapper which prints every private passage to stdout.
        prepared = self.model.preprocessor(text)
        return self.model.generate_single_chunk(prepared, voice, speed).reshape(-1)

class SpeechEngine:
    def __init__(self, audio, status, error, model=None):
        self.audio, self.status, self.error = audio, status, error
        self.model = model or Model(status)
        self.condition = threading.Condition()
        self.generation = 0
        self.request = None
        self.closed = False
        self.active = False
        self.ready = threading.Event()
        self.load_error = None
        self.worker = threading.Thread(target=self._run, name='synthesis', daemon=True)
        self.worker.start()

    def speak(self, text, voice='Jasper', speed=1.0):
        text = text.strip()
        if not text:
            return
        with self.condition:
            self.generation += 1
            self.audio.reset(self.generation)
            self.request = (self.generation, text, voice, speed)
            self.active = True
            self.condition.notify()
        self.status('Preparing speech…')

    def stop(self):
        with self.condition:
            self.generation += 1
            self.request = None
            self.active = False
            self.audio.reset(self.generation)
            self.condition.notify()
        self.status('Stopped')

    def _run(self):
        try:
            self.model.load()
        except Exception as exc:
            self.load_error = type(exc).__name__
            self.error('Model could not load. Check your connection on first use, then press Read to retry. (' + self.load_error + ')')
        finally:
            self.ready.set()
        while True:
            with self.condition:
                self.condition.wait_for(lambda: self.closed or self.request is not None)
                if self.closed:
                    return
                generation, text, voice, speed = self.request
                self.request = None
            try:
                self.model.load()
                for passage in chunks(text):
                    if generation != self.generation or self.closed:
                        break
                    samples = self.model.generate(passage, voice, speed)
                    while generation == self.generation and not self.closed:
                        if self.audio.enqueue(generation, samples):
                            break
                        with self.condition:
                            self.condition.wait(0.04)
                if generation == self.generation and not self.closed:
                    self.audio.finish(generation)
            except Exception as exc:
                if generation == self.generation:
                    self.stop()
                    self.error(f'Speech failed ({type(exc).__name__}). Check the model and audio output, then retry.')
            finally:
                text = ''

    def close(self):
        self.stop()
        with self.condition:
            self.closed = True
            self.condition.notify()
        self.worker.join(5)
        self.audio.close()
