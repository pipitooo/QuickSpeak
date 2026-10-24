"""Windows integration tests. Use a normal desktop session."""
import os
from pathlib import Path
import tempfile
import threading
import time
import unittest
from unittest.mock import patch

class WindowsTests(unittest.TestCase):
    def test_mutex_prevents_second_instance(self):
        from quickspeak.app import SingleInstance
        first, second = SingleInstance(), SingleInstance()
        try:
            self.assertTrue(second.already_running)
        finally:
            second.close()
            first.close()

    def test_settings_roundtrip_and_invalid_defaults(self):
        from quickspeak.settings import Settings
        with tempfile.TemporaryDirectory() as directory, patch.dict(os.environ, QUICKSPEAK_HOME=directory):
            settings = Settings(voice='Luna', speed=1.25, volume=0.3, shortcut='Ctrl+Shift+F8')
            settings.save()
            self.assertEqual(Settings.load(), settings)
            Path(directory, 'settings.json').write_text('{bad json', 'utf-8')
            self.assertEqual(Settings.load(), Settings())
            Path(directory, 'settings.json').write_text('{"speed":20}', 'utf-8')
            self.assertEqual(Settings.load(), Settings())

    def test_existing_settings_gain_pause_shortcut_and_preserve_preferences(self):
        from quickspeak.settings import Settings
        with tempfile.TemporaryDirectory() as directory, patch.dict(os.environ, QUICKSPEAK_HOME=directory):
            Path(directory, 'settings.json').write_text('{"voice":"Luna","shortcut":"Ctrl+Shift+F8"}', 'utf-8')
            settings = Settings.load()
            self.assertEqual(settings.voice, 'Luna')
            self.assertEqual(settings.shortcut, 'Ctrl+Shift+F8')
            self.assertEqual(settings.pause_shortcut, 'Ctrl+Alt+I')
            settings.pause_shortcut = 'Ctrl+Shift+F9'
            settings.save()
            self.assertEqual(Settings.load(), settings)

    def test_audio_error_is_reported(self):
        import numpy as np
        from quickspeak.audio import AudioPlayer
        failed = threading.Event()
        errors = []
        def error(message):
            errors.append(message)
            failed.set()
        with patch('quickspeak.audio.sd.OutputStream', side_effect=RuntimeError('test device error')):
            audio = AudioPlayer(error=error)
            try:
                audio.reset(1)
                audio.enqueue(1, np.zeros(1000, dtype='float32'))
                self.assertTrue(failed.wait(2))
                self.assertIn('Audio output unavailable', errors[0])
            finally:
                audio.close()
            self.assertFalse(audio.worker.is_alive())

    @unittest.skipIf(os.environ.get('QUICKSPEAK_SKIP_HARDWARE_TESTS') == '1', 'Requires an audio output device')
    def test_real_audio_pause_stop_and_replacement(self):
        import numpy as np
        from quickspeak.audio import AudioPlayer
        completed = threading.Event()
        errors = []
        audio = AudioPlayer(error=errors.append, on_done=lambda gen: completed.set())
        try:
            audio.volume = 0  # Exercise actual device without an audible test tone.
            audio.reset(1)
            audio.enqueue(1, np.ones(24000 * 4, dtype='float32') * 0.01)
            audio.finish(1)
            deadline = time.monotonic() + 3
            while audio.first_audio_at is None and time.monotonic() < deadline:
                time.sleep(0.02)
            self.assertIsNotNone(audio.first_audio_at)
            audio.toggle_pause()
            with audio.lock:
                before = audio.offset
            time.sleep(0.15)
            with audio.lock:
                self.assertEqual(audio.offset, before)
            audio.reset(2)
            audio.enqueue(1, np.ones(500))  # An old generation must be ignored.
            self.assertEqual(len(audio.buffers), 0)
            audio.enqueue(2, np.zeros(2400, dtype='float32'))
            audio.finish(2)
            self.assertTrue(completed.wait(3))
            self.assertFalse(errors)
        finally:
            audio.close()

if __name__ == '__main__':
    unittest.main()
