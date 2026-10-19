"""Opt-in synthetic-text benchmark. Never reads the user's clipboard."""
import argparse
import ctypes as C
from ctypes import wintypes as W
import json
import os
from pathlib import Path
import platform
import sys
import time

def memory_mib():
    class Counters(C.Structure):
        _fields_ = [('cb', W.DWORD), ('PageFaultCount', W.DWORD)] + [(name, C.c_size_t) for name in (
            'PeakWorkingSetSize', 'WorkingSetSize', 'QuotaPeakPagedPoolUsage', 'QuotaPagedPoolUsage',
            'QuotaPeakNonPagedPoolUsage', 'QuotaNonPagedPoolUsage', 'PagefileUsage', 'PeakPagefileUsage')]
    counters = Counters()
    counters.cb = C.sizeof(counters)
    kernel = C.WinDLL('kernel32')
    kernel.GetCurrentProcess.restype = W.HANDLE
    psapi = C.WinDLL('psapi')
    psapi.GetProcessMemoryInfo.argtypes = [W.HANDLE, C.c_void_p, W.DWORD]
    psapi.GetProcessMemoryInfo(kernel.GetCurrentProcess(), C.byref(counters), counters.cb)
    return round(counters.WorkingSetSize / 1048576, 1)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--self-test', action='store_true')
    parser.add_argument('--selection-check', action='store_true')
    parser.add_argument('--no-audio', action='store_true', help='Synthesize and save WAV without opening an audio device (CI)')
    parser.add_argument('--report', default='benchmark.json')
    parser.add_argument('--wav', default='benchmark.wav')
    args = parser.parse_args()
    if args.selection_check:
        from .selection import capture_selection, u32
        import win32gui
        before = u32.GetClipboardSequenceNumber()
        start = time.perf_counter()
        try:
            text, method = capture_selection(win32gui.GetForegroundWindow())
            result = {'status': 'passed', 'method': method, 'characters': len(text),
                      'elapsed_s': round(time.perf_counter() - start, 3),
                      'clipboard_unchanged': before == u32.GetClipboardSequenceNumber(),
                      'frozen': bool(getattr(sys, 'frozen', False))}
        except Exception as exc:
            result = {'status': 'failed', 'error_type': type(exc).__name__}
        Path(args.report).parent.mkdir(parents=True, exist_ok=True)
        Path(args.report).write_text(json.dumps(result, indent=2), 'utf-8')
        return
    report = {'platform': platform.platform(), 'python': platform.python_version(), 'cpu': platform.processor(),
              'logical_cpus': os.cpu_count(), 'frozen': bool(getattr(sys, 'frozen', False)), 'sample_rate': 24000}
    try:
        from .tts import Model
        from .audio import AudioPlayer
        import soundfile as sf
        import sounddevice as sd
        import threading
        started = time.perf_counter()
        model = Model()
        model.load()
        report['model_load_s'] = round(time.perf_counter() - started, 3)
        report['providers'] = model.model.session.get_providers()
        report['loaded_ram_mib'] = memory_mib()
        report['torch_imported'] = 'torch' in sys.modules
        report['audio_playback_tested'] = not args.no_audio
        if not args.no_audio:
            report['output_device'] = sd.query_devices(kind='output')['name']
        report['runs'] = []
        errors = []
        for i in range(3):
            if args.no_audio:
                import numpy as np
                start = time.perf_counter()
                samples = model.generate('Hello! QuickSpeak is working.', 'Jasper', 1.0)
                if len(samples) < 1000 or not np.isfinite(samples).all():
                    raise RuntimeError('Invalid synthesized audio')
                report['runs'].append({'synthesis_s': round(time.perf_counter() - start, 3),
                                      'audio_duration_s': round(len(samples) / 24000, 3)})
                continue
            done = threading.Event()
            audio = AudioPlayer(error=errors.append, on_done=lambda generation: done.set())
            audio.reset(i + 1)
            start = time.perf_counter()
            samples = model.generate('Hello! QuickSpeak is working.', 'Jasper', 1.0)
            synthesized = time.perf_counter()
            audio.enqueue(i + 1, samples)
            audio.finish(i + 1)
            if not done.wait(20):
                raise RuntimeError('Audio playback timed out')
            if errors or audio.first_audio_at is None:
                raise RuntimeError('Audio device playback failed')
            report['runs'].append({'synthesis_s': round(synthesized - start, 3),
                'estimated_first_dac_audio_s': round(audio.first_audio_at - start, 3),
                'audio_duration_s': round(len(samples) / 24000, 3)})
            audio.close()
        Path(args.wav).parent.mkdir(parents=True, exist_ok=True)
        sf.write(args.wav, samples, 24000)
        report['after_speech_ram_mib'] = memory_mib()
        before_cpu, before_wall = time.process_time(), time.perf_counter()
        time.sleep(2)
        report['idle_one_core_cpu_percent'] = round(100 * (time.process_time() - before_cpu) / (time.perf_counter() - before_wall), 2)
        report['status'] = 'passed'
    except Exception as exc:
        import traceback
        report['status'] = 'failed'
        report['error'] = repr(exc)
        report['traceback'] = traceback.format_exc()
    Path(args.report).parent.mkdir(parents=True, exist_ok=True)
    Path(args.report).write_text(json.dumps(report, indent=2), 'utf-8')
    if sys.stdout:
        print(json.dumps(report, indent=2))
    if report['status'] != 'passed':
        raise SystemExit(1)
