"""UIA first, conservative clipboard fallback. Never pastes or types text."""
import ctypes as C
from ctypes import wintypes as W
import multiprocessing as mp
import time
import win32clipboard as cb
import win32con
import win32gui

MAX_TEXT = 100_000
u32 = C.WinDLL('user32', use_last_error=True)
u32.GetClipboardSequenceNumber.restype = W.DWORD
u32.GetAsyncKeyState.argtypes = [C.c_int]
u32.GetAsyncKeyState.restype = C.c_short

class CaptureError(Exception):
    pass

def _uia_probe(pipe, hwnd):
    try:
        import comtypes
        from comtypes.client import CreateObject, GetModule
        comtypes.CoInitialize()
        try:
            module = GetModule('UIAutomationCore.dll')
            automation = CreateObject(module.CUIAutomation, interface=module.IUIAutomation)
            element = automation.GetFocusedElement()
            if win32gui.GetForegroundWindow() != hwnd:
                pipe.send(('focus', ''))
                return
            if element.CurrentIsPassword:
                pipe.send(('password', ''))
                return
            # Focus may be on a descendant inside an accessible document.
            for _ in range(6):
                if not element:
                    break
                try:
                    pattern = element.GetCurrentPattern(10014).QueryInterface(module.IUIAutomationTextPattern)
                    ranges = pattern.GetSelection()
                    text = '\n'.join(ranges.GetElement(i).GetText(MAX_TEXT) for i in range(ranges.Length))
                    pipe.send(('ok', text[:MAX_TEXT]))
                    return
                except Exception:
                    element = automation.ControlViewWalker.GetParentElement(element)
            pipe.send(('unsupported', ''))
        finally:
            comtypes.CoUninitialize()
    except Exception:
        pipe.send(('unsupported', ''))
    finally:
        pipe.close()

def uia_selection(hwnd, timeout=2.0):
    parent, child = mp.Pipe(duplex=False)
    process = mp.Process(target=_uia_probe, args=(child, hwnd), daemon=True)
    process.start()
    child.close()
    try:
        return parent.recv() if parent.poll(timeout) else ('unsupported', '')
    except EOFError:
        return 'unsupported', ''
    finally:
        parent.close()
        process.join(0.05)
        if process.is_alive():
            process.terminate()
            process.join(1)
        process.close()

def open_clipboard():
    for _ in range(20):
        try:
            cb.OpenClipboard()
            return
        except Exception:
            time.sleep(0.025)
    raise CaptureError('Clipboard is busy. Please try again.')

def read_clipboard():
    open_clipboard()
    try:
        return cb.GetClipboardData(win32con.CF_UNICODETEXT)[:MAX_TEXT] if cb.IsClipboardFormatAvailable(win32con.CF_UNICODETEXT) else ''
    finally:
        cb.CloseClipboard()

def snapshot_clipboard():
    """Only formats safely round-trippable as copied Python values."""
    open_clipboard()
    try:
        snapshot, fmt = [], 0
        while True:
            fmt = cb.EnumClipboardFormats(fmt)
            if not fmt:
                break
            # Bitmap/metafile/palette/private handles cannot be copied this way.
            if fmt not in (1, 7, 8, 13, 16, 17) and fmt < 0xC000:
                raise CaptureError('This clipboard contains unsupported rich data. Use the text box, or copy text and choose Read Clipboard.')
            value = cb.GetClipboardData(fmt)
            if not isinstance(value, (str, bytes)):
                raise CaptureError('Cannot safely preserve this clipboard. Use Read Clipboard instead.')
            snapshot.append((fmt, value))
        return snapshot, u32.GetClipboardSequenceNumber()
    finally:
        cb.CloseClipboard()

class KEYBDINPUT(C.Structure):
    _fields_ = [('wVk', W.WORD), ('wScan', W.WORD), ('dwFlags', W.DWORD), ('time', W.DWORD), ('dwExtraInfo', C.c_size_t)]
class MOUSEINPUT(C.Structure):
    _fields_ = [('dx', W.LONG), ('dy', W.LONG), ('mouseData', W.DWORD), ('dwFlags', W.DWORD), ('time', W.DWORD), ('dwExtraInfo', C.c_size_t)]
class INPUTUNION(C.Union):
    _fields_ = [('ki', KEYBDINPUT), ('mi', MOUSEINPUT)]
class INPUT(C.Structure):
    _fields_ = [('type', W.DWORD), ('data', INPUTUNION)]

def send_copy():
    events = (INPUT * 4)()
    for event, (key, flags) in zip(events, [(0x11, 0), (0x43, 0), (0x43, 2), (0x11, 2)]):
        event.type = 1
        event.data.ki = KEYBDINPUT(key, 0, flags, 0, 0)
    if u32.SendInput(4, events, C.sizeof(INPUT)) != 4:
        # Release only the keys we attempted to inject.
        releases = (INPUT * 2)(events[2], events[3])
        u32.SendInput(2, releases, C.sizeof(INPUT))
        raise CaptureError('Windows blocked copying from this application.')

def wait_for_modifiers():
    deadline = time.monotonic() + 1.5
    while any(u32.GetAsyncKeyState(key) & 0x8000 for key in (0x10, 0x11, 0x12, 0x5B, 0x5C)):
        if time.monotonic() > deadline:
            raise CaptureError('Release the shortcut keys and try again.')
        time.sleep(0.015)

def clipboard_selection(hwnd):
    wait_for_modifiers()
    if win32gui.GetForegroundWindow() != hwnd:
        raise CaptureError('Focus changed before text could be copied. Try again.')
    snapshot, before = snapshot_clipboard()
    if u32.GetClipboardSequenceNumber() != before or win32gui.GetForegroundWindow() != hwnd:
        raise CaptureError('Clipboard or focus changed. Please try again.')
    send_copy()
    deadline = time.monotonic() + 0.9
    copied = None
    try:
        while time.monotonic() < deadline:
            if u32.GetClipboardSequenceNumber() != before:
                open_clipboard()
                try:
                    copied = u32.GetClipboardSequenceNumber()
                    if win32gui.GetForegroundWindow() != hwnd:
                        raise CaptureError('Focus changed while copying. Please try again.')
                    return cb.GetClipboardData(13)[:MAX_TEXT] if cb.IsClipboardFormatAvailable(13) else ''
                finally:
                    cb.CloseClipboard()
            time.sleep(0.015)
        return ''  # No sequence change means no fresh copy; NEVER use stale text.
    finally:
        if copied is not None:
            open_clipboard()
            try:
                # Do not overwrite a later copy performed by the user/another app.
                if u32.GetClipboardSequenceNumber() == copied:
                    cb.EmptyClipboard()
                    for fmt, value in snapshot:
                        cb.SetClipboardData(fmt, value)
            finally:
                cb.CloseClipboard()

def capture_selection(hwnd):
    wait_for_modifiers()
    kind, text = uia_selection(hwnd)
    if win32gui.GetForegroundWindow() != hwnd or kind == 'focus':
        raise CaptureError('Focus changed. Select the text and try again.')
    if kind == 'password':
        raise CaptureError('Protected text cannot be read.')
    if text.strip():
        return text.strip(), 'UI Automation'
    # A supported TextPattern with an empty range is authoritative (avoids
    # editors where Ctrl+C with no selection copies the whole current line).
    if kind == 'ok':
        return '', 'UI Automation'
    return clipboard_selection(hwnd).strip(), 'Clipboard fallback'
