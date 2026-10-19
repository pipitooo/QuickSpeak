import ctypes as C
from ctypes import wintypes as W
import queue
import threading
import tkinter as tk
from .settings import Settings
from .hotkeys import Hotkey
from .audio import AudioPlayer
from .tts import SpeechEngine
from .selection import capture_selection, read_clipboard
from .tray import Tray
from .ui import Window

class SingleInstance:
    def __init__(self):
        self.kernel = C.WinDLL('kernel32', use_last_error=True)
        self.kernel.CreateMutexW.argtypes = [C.c_void_p, W.BOOL, W.LPCWSTR]
        self.kernel.CreateMutexW.restype = W.HANDLE
        self.kernel.CloseHandle.argtypes = [W.HANDLE]
        self.handle = self.kernel.CreateMutexW(None, False, 'Local\\QuickSpeak.Desktop.1')
        if not self.handle:
            raise OSError('Cannot create application mutex')
        self.already_running = C.get_last_error() == 183

    def close(self):
        if self.handle:
            self.kernel.CloseHandle(self.handle)
            self.handle = None

class App:
    def __init__(self, show=False):
        self.root = tk.Tk()
        self.root.withdraw()
        self.events = queue.Queue()
        self.closing = False
        self.root.report_callback_exception = lambda kind, value, tb: self.error(f'Action failed ({kind.__name__}). Please try again.')
        self.capture_busy = threading.Lock()
        self.capture_thread = None
        self.settings = Settings.load()
        self.audio = AudioPlayer(self.status, self.audio_error, lambda gen: self.dispatch(lambda: self.finished(gen)))
        self.audio.volume = self.settings.volume
        self.hotkey = Hotkey(lambda hwnd: self.dispatch(lambda: self.capture(hwnd)))
        self.window = Window(self.root, self)
        self.tray = Tray(self.dispatch, self.clipboard, self.window.show, self.stop, self.close)
        self.engine = SpeechEngine(self.audio, self.status, self.error)
        try:
            self.hotkey.set(self.settings.shortcut)
        except Exception as exc:
            self.error(str(exc))
            show = True
        if show:
            self.window.show()
        self.root.after(50, self.pump)
        self.tray.notify('Loading local voices. Open QuickSpeak from this tray icon for status.')

    def dispatch(self, fn):
        if not self.closing:
            self.events.put(fn)

    def pump(self):
        for _ in range(50):
            try:
                fn = self.events.get_nowait()
            except queue.Empty:
                break
            try:
                fn()
            except Exception as exc:
                self.error(f'Action failed ({type(exc).__name__}). Please try again.')
            if self.closing:
                return
        self.root.after(50, self.pump)

    def set_status(self, text):
        self.window.status.set(text)
        self.tray.status(text)

    def status(self, text):
        self.dispatch(lambda: self.set_status(text))

    def error(self, text):
        self.dispatch(lambda: (self.set_status(text), self.tray.notify(text)))

    def read(self, text):
        if text.strip():
            if len(text) > 100_000:
                self.error('Please read passages of 100,000 characters or fewer.')
                return
            self.engine.speak(text, self.settings.voice, self.settings.speed)
        else:
            self.error('No text selected. Select some text and try again.')

    def stop(self):
        self.engine.stop()

    def pause(self):
        if self.engine.active:
            self.audio.toggle_pause()

    def audio_error(self, text):
        self.dispatch(lambda: (self.stop(), self.error(text)))

    def finished(self, generation):
        if generation == self.engine.generation:
            self.engine.active = False

    def capture(self, hwnd):
        if self.closing or not self.capture_busy.acquire(blocking=False):
            return
        self.stop()  # Stop immediately, before waiting for capture.
        generation = self.engine.generation
        def work():
            try:
                text, method = capture_selection(hwnd)
                if text:
                    self.dispatch(lambda: self.read(text) if generation == self.engine.generation else None)
                else:
                    self.error('No text selected. Reading stopped.')
            except Exception as exc:
                self.error(str(exc) if type(exc).__name__ == 'CaptureError' else 'Selection unavailable. Try copying the text and choose Read Clipboard.')
            finally:
                self.capture_busy.release()
        self.capture_thread = threading.Thread(target=work, name='selection', daemon=True)
        self.capture_thread.start()

    def clipboard(self):
        def work():
            try:
                text = read_clipboard()
                self.dispatch(lambda: self.read(text))
            except Exception:
                self.error('Clipboard is unavailable. Please try again.')
        threading.Thread(target=work, name='clipboard', daemon=True).start()

    def close(self):
        if self.closing:
            return
        self.closing = True
        self.root.withdraw()
        self.hotkey.close()
        self.engine.close()
        if self.capture_thread:
            self.capture_thread.join(4)
        self.tray.close()
        self.root.destroy()

def run(show=False):
    instance = SingleInstance()
    try:
        if instance.already_running:
            C.windll.user32.MessageBoxW(None, 'QuickSpeak is already running. Open it from the system tray.', 'QuickSpeak', 0x40)
            return
        app = App(show)
        try:
            app.root.mainloop()
        finally:
            app.close()
    finally:
        instance.close()
