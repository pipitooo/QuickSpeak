# Third-party components

QuickSpeak uses KittenTTS 0.8.1 (Apache-2.0) and the KittenML Nano 0.8 INT8 model.
The model is downloaded separately; the executable does not embed model weights.

- KittenTTS release and source: https://github.com/KittenML/KittenTTS/releases/tag/0.8.1
- Exact wheel: https://github.com/KittenML/KittenTTS/releases/download/0.8.1/kittentts-0.8.1-py3-none-any.whl
- Model and model license: https://huggingface.co/KittenML/kitten-tts-nano-0.8-int8/tree/84781d74e29ee25217551556398b42f80593a813
- ONNX Runtime: https://github.com/microsoft/onnxruntime (MIT).
- NumPy: https://numpy.org/ (BSD).
- phonemizer-fork / phonemizer: https://github.com/bootphon/phonemizer (GPL-3.0-or-later).
- eSpeak NG: https://github.com/espeak-ng/espeak-ng (GPL-3.0-or-later).
- espeakng-loader: https://pypi.org/project/espeakng-loader/0.2.4/ (includes eSpeak runtime and data).
- sounddevice / PortAudio: https://python-sounddevice.readthedocs.io/ and https://www.portaudio.com/.
- soundfile / libsndfile: https://python-soundfile.readthedocs.io/ and https://libsndfile.github.io/libsndfile/.
- pystray: https://github.com/moses-palmer/pystray (LGPL-3.0).
- Pillow: https://python-pillow.org/.
- comtypes: https://github.com/enthought/comtypes.
- pywin32: https://github.com/mhammond/pywin32.
- Python / Tk: https://www.python.org/ and https://www.tcl.tk/.
- PyInstaller bootloader: https://pyinstaller.org/ (GPL with distribution exception).

The `licenses/` folder in the built package preserves license/notice files
provided by installed distributions. Exact dependency versions are recorded in
`requirements.txt` and `requirements-build.txt`.

The only patch to installed KittenTTS source removes its unused
`from misaki import en, espeak` line. `tools/patch_kitten.py` contains the complete
reproducible modification. The application adapter explicitly constructs the
original ONNX implementation's fields to supply CPU session options and uses its
original generation implementation. No upstream model weights are modified.
