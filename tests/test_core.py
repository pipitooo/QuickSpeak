import threading
import os
import time
import unittest
from unittest.mock import patch
from quickspeak.hotkeys import parse_shortcut, Hotkey
from quickspeak.tts import chunks, SpeechEngine

class CoreTests(unittest.TestCase):
    def test_unicode_chunk_boundaries_and_size(self):
        original = 'Hello café!\n世界 ' + 'word ' * 500 + 'x' * 500
        result = list(chunks(original))
        self.assertTrue(all(0 < len(s) <= 220 for s in result))
        self.assertEqual(''.join(original.split()), ''.join(''.join(result).split()))
        self.assertEqual(result[0], 'Hello café!')

    def test_shortcut_validation(self):
        self.assertEqual(parse_shortcut('Ctrl+Alt+R'), (0x4003, 82))
        self.assertEqual(parse_shortcut('Ctrl+F12'), (0x4002, 123))
        for value in ('R', 'Shift+R', 'Ctrl+Ctrl+R', 'Ctrl+é', 'Win+R', 'Ctrl+F13'):
            with self.assertRaises(ValueError):
                parse_shortcut(value)

    @unittest.skipIf(os.environ.get('QUICKSPEAK_SKIP_HARDWARE_TESTS') == '1', 'Requires an interactive Windows desktop')
    def test_native_shortcut_conflict_and_recovery(self):
        a, b = Hotkey(lambda h: None), Hotkey(lambda h: None)
        try:
            a.set('Ctrl+Alt+Shift+F11')
            b.set('Ctrl+Alt+Shift+F10')
            with self.assertRaises(ValueError):
                b.set('Ctrl+Alt+Shift+F11')
            self.assertEqual(b.current, 'Ctrl+Alt+Shift+F10')
            a.set('Ctrl+Alt+Shift+F9')
            b.set('Ctrl+Alt+Shift+F11')
        finally:
            a.close()
            b.close()
        self.assertFalse(a.thread.is_alive())

    def test_inflight_generation_cannot_play_after_replacement(self):
        entered, release, played = threading.Event(), threading.Event(), threading.Event()
        class Model:
            def load(self): pass
            def generate(self, text, voice, speed):
                if text == 'old':
                    entered.set()
                    release.wait(2)
                return text
        class Audio:
            def __init__(self): self.outputs = []
            def reset(self, gen): pass
            def enqueue(self, gen, data):
                self.outputs.append(data)
                played.set()
                return True
            def finish(self, gen): pass
            def close(self): pass
        audio = Audio()
        engine = SpeechEngine(audio, lambda s: None, self.fail, Model())
        try:
            engine.speak('old')
            self.assertTrue(entered.wait(2))
            engine.speak('new')
            release.set()
            self.assertTrue(played.wait(2))
            self.assertEqual(audio.outputs, ['new'])
            engine.stop()
            self.assertFalse(engine.active)
        finally:
            release.set()
            engine.close()
        self.assertFalse(engine.worker.is_alive())

    def test_pause_toggle_only_affects_active_reading(self):
        from types import SimpleNamespace
        from quickspeak.app import App
        from quickspeak.audio import AudioPlayer
        audio = AudioPlayer()
        app = SimpleNamespace(engine=SimpleNamespace(active=False), audio=audio)
        try:
            App.pause(app)
            self.assertFalse(audio.paused)
            app.engine.active = True
            App.pause(app)
            self.assertTrue(audio.paused)
            App.pause(app)
            self.assertFalse(audio.paused)
        finally:
            audio.close()

    @unittest.skipIf(os.environ.get('QUICKSPEAK_SKIP_HARDWARE_TESTS') == '1', 'Requires an interactive Windows desktop')
    def test_read_and_pause_listeners_dispatch_independently(self):
        from quickspeak.hotkeys import user32
        read, pause = threading.Event(), threading.Event()
        a, b = Hotkey(lambda hwnd: read.set()), Hotkey(lambda hwnd: pause.set())
        try:
            a.set('Ctrl+Alt+Shift+F11')
            b.set('Ctrl+Alt+Shift+F10')
            b.set('Alt+Ctrl+Shift+F10')
            user32.PostThreadMessageW(b.tid, 0x0312, 2, 0)
            self.assertTrue(pause.wait(2))
            self.assertFalse(read.is_set())
            user32.PostThreadMessageW(a.tid, 0x0312, 2, 0)
            self.assertTrue(read.wait(2))
        finally:
            a.close()
            b.close()
        self.assertFalse(a.thread.is_alive())
        self.assertFalse(b.thread.is_alive())

    def test_stale_clipboard_is_never_read(self):
        from quickspeak import selection as s
        with patch.object(s, 'snapshot_clipboard', return_value=([], 42)), \
             patch.object(s.u32, 'GetAsyncKeyState', return_value=0), \
             patch.object(s.u32, 'GetClipboardSequenceNumber', return_value=42), \
             patch.object(s.win32gui, 'GetForegroundWindow', return_value=100), \
             patch.object(s, 'send_copy'), patch.object(s, 'read_clipboard') as read:
            self.assertEqual(s.clipboard_selection(100), '')
            read.assert_not_called()

    def test_empty_supported_selection_does_not_copy_current_line(self):
        from quickspeak import selection as s
        with patch.object(s, 'uia_selection', return_value=('ok', '')), \
             patch.object(s.win32gui, 'GetForegroundWindow', return_value=1), \
             patch.object(s, 'clipboard_selection') as copy:
            self.assertEqual(s.capture_selection(1)[0], '')
            copy.assert_not_called()

if __name__ == '__main__':
    unittest.main()
