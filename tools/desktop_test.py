"""Opt-in desktop harness; stores only synthetic-test metrics, never passages."""
import multiprocessing
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

if __name__ == '__main__':
    multiprocessing.freeze_support()
    import json
    import time
    import threading
    import quickspeak.app as module
    from quickspeak.diagnostics import memory_mib
    records = []
    capture = module.capture_selection
    start = time.perf_counter()
    def observe_capture(hwnd):
        begin = time.perf_counter()
        text, method = capture(hwnd)
        records.append({'event': 'selection', 'method': method, 'chars': len(text), 'capture_s': time.perf_counter() - begin})
        return text, method
    module.capture_selection = observe_capture
    instance = module.SingleInstance()
    assert not instance.already_running
    app = module.App(show=True)
    status = app.set_status
    def observe_status(text):
        records.append({'event':'status', 'value':text, 'at_s':time.perf_counter() - start})
        status(text)
    app.set_status = observe_status
    last_audio = None
    def poll():
        global last_audio
        if app.audio.first_audio_at != last_audio:
            last_audio = app.audio.first_audio_at
            records.append({'event':'audio', 'at_s':last_audio - start})
        Path('artifacts/desktop-integration.json').write_text(json.dumps({'events':records, 'ram_mib':memory_mib()},indent=2),'utf-8')
        app.root.after(200, poll)
    app.root.after(200, poll)
    app.root.after(300_000, app.close)
    app.root.mainloop()
    instance.close()
    records.append({'event':'shutdown', 'workers_remaining':[t.name for t in threading.enumerate() if t.name in ('audio','synthesis','hotkey','selection','tray')]})
    Path('artifacts/desktop-integration.json').write_text(json.dumps({'events':records},indent=2),'utf-8')
