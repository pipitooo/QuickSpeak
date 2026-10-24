"""RegisterHotKey: no keyboard hooks, polling, or key logging."""
import ctypes as C
from ctypes import wintypes as W
import queue
import threading

user32 = C.WinDLL('user32', use_last_error=True)
kernel32 = C.WinDLL('kernel32', use_last_error=True)
user32.GetForegroundWindow.restype = W.HWND
user32.RegisterHotKey.argtypes = [W.HWND, C.c_int, W.UINT, W.UINT]
user32.UnregisterHotKey.argtypes = [W.HWND, C.c_int]
user32.PostThreadMessageW.argtypes = [W.DWORD, W.UINT, W.WPARAM, W.LPARAM]

def parse_shortcut(value):
    parts = [x.strip().upper() for x in value.split('+')]
    mods = {'ALT': 1, 'CTRL': 2, 'SHIFT': 4}
    if len(parts) < 2 or len(set(parts)) != len(parts) or any(x not in mods for x in parts[:-1]):
        raise ValueError('Use Ctrl, Alt or Shift plus a letter, digit or F1–F12 (for example Ctrl+Alt+R).')
    mask = sum(mods[x] for x in parts[:-1])
    if not mask & 3:
        raise ValueError('Include Ctrl or Alt to avoid intercepting normal typing.')
    key = parts[-1]
    if len(key) == 1 and key.isascii() and key.isalnum():
        vk = ord(key)
    elif key.startswith('F') and key[1:].isdigit() and 1 <= int(key[1:]) <= 12:
        vk = 111 + int(key[1:])
    else:
        raise ValueError('Shortcut key must be A–Z, 0–9 or F1–F12.')
    return mask | 0x4000, vk

class Hotkey:
    def __init__(self, callback):
        self.callback = callback
        self.commands = queue.Queue()
        self.ready = threading.Event()
        self.current = None
        self.thread = threading.Thread(target=self._run, name='hotkey', daemon=True)
        self.thread.start()
        self.ready.wait(3)

    def _run(self):
        self.tid = kernel32.GetCurrentThreadId()
        msg = W.MSG()
        user32.PeekMessageW(C.byref(msg), None, 0, 0, 0)
        self.ready.set()
        slot = 1
        while user32.GetMessageW(C.byref(msg), None, 0, 0) > 0:
            if msg.message == 0x0312:
                self.callback(user32.GetForegroundWindow())
            elif msg.message == 0x8001:
                value, event, result = self.commands.get()
                if value is None:
                    if self.current:
                        user32.UnregisterHotKey(None, slot)
                    event.set()
                    break
                if self.current and parse_shortcut(value) == parse_shortcut(self.current):
                    self.current = value
                    event.set()
                    continue
                mods, vk = parse_shortcut(value)
                new_slot = 2 if slot == 1 else 1
                if user32.RegisterHotKey(None, new_slot, mods, vk):
                    if self.current:
                        user32.UnregisterHotKey(None, slot)
                    slot, self.current = new_slot, value
                else:
                    code = C.get_last_error()
                    result.append('This shortcut is already in use. Choose another one.' if code == 1409 else f'Windows could not register the shortcut (error {code}). Check desktop permissions or choose another shortcut.')
                event.set()

    def set(self, value):
        parse_shortcut(value)
        self._command(value)

    def _command(self, value):
        event, result = threading.Event(), []
        self.commands.put((value, event, result))
        if not user32.PostThreadMessageW(self.tid, 0x8001, 0, 0) or not event.wait(3):
            raise RuntimeError('The Windows shortcut listener did not respond.')
        if result:
            raise ValueError(result[0])

    def close(self):
        if self.thread.is_alive():
            self._command(None)
            self.thread.join(3)
