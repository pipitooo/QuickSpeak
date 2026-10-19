"""Bounded producer queue; device is opened only during playback."""
from collections import deque
import threading
import time
import numpy as np
import sounddevice as sd

class AudioPlayer:
    def __init__(self, status=lambda text: None, error=lambda text: None, on_done=lambda generation: None):
        self.status, self.error, self.on_done = status, error, on_done
        self.lock = threading.Lock()
        self.wake = threading.Event()
        self.buffers = deque()
        self.generation = 0
        self.offset = 0
        self.complete = False
        self.paused = False
        self.volume = 0.8
        self.closed = False
        self.first_audio_at = None
        self.worker = threading.Thread(target=self._run, name='audio', daemon=True)
        self.worker.start()

    def reset(self, generation):
        with self.lock:
            self.generation = generation
            self.buffers.clear()
            self.offset = 0
            self.complete = False
            self.paused = False
        self.wake.set()

    def enqueue(self, generation, samples):
        with self.lock:
            if generation != self.generation:
                return True
            if len(self.buffers) >= 3:
                return False
            self.buffers.append(np.asarray(samples, dtype='float32').reshape(-1))
        self.wake.set()
        return True

    def finish(self, generation):
        with self.lock:
            if generation == self.generation:
                self.complete = True
        self.wake.set()

    def toggle_pause(self):
        with self.lock:
            self.paused = not self.paused
        self.status('Paused' if self.paused else 'Reading…')

    def _run(self):
        while not self.closed:
            self.wake.wait()
            self.wake.clear()
            with self.lock:
                if not self.buffers or self.closed:
                    continue
                generation = self.generation
            done = threading.Event()
            first = True
            def callback(out, frames, timing, flags):
                nonlocal first
                out.fill(0)
                with self.lock:
                    if self.closed or generation != self.generation:
                        raise sd.CallbackAbort
                    if self.paused:
                        return
                    written = 0
                    while written < frames and self.buffers:
                        data = self.buffers[0]
                        count = min(frames - written, len(data) - self.offset)
                        out[written:written + count, 0] = data[self.offset:self.offset + count] * self.volume
                        written += count
                        self.offset += count
                        if first and count:
                            self.first_audio_at = time.perf_counter() + max(0, timing.outputBufferDacTime - timing.currentTime)
                            first = False
                        if self.offset == len(data):
                            self.buffers.popleft()
                            self.offset = 0
                    if not self.buffers and self.complete:
                        raise sd.CallbackStop
            try:
                with sd.OutputStream(samplerate=24000, channels=1, dtype='float32', blocksize=480,
                                     latency='low', callback=callback, finished_callback=done.set):
                    self.status('Reading…')
                    while not done.wait(0.04):
                        if self.closed or generation != self.generation:
                            break
                if generation == self.generation and self.complete:
                    self.on_done(generation)
                    self.status('Ready · finished reading')
            except Exception as exc:
                if generation == self.generation:
                    with self.lock:
                        self.buffers.clear()
                    self.on_done(generation)
                    self.error(f'Audio output unavailable ({type(exc).__name__}). Check your speakers and try again.')

    def close(self):
        self.closed = True
        self.wake.set()
        self.worker.join(3)
