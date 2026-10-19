"""Keep entry point lightweight so spawned UIA workers do not load the model."""
import multiprocessing
import sys

if __name__ == '__main__':
    multiprocessing.freeze_support()
    if '--self-test' in sys.argv or '--selection-check' in sys.argv:
        from quickspeak.diagnostics import main
        main()
    else:
        try:
            from quickspeak.app import run
            run('--show' in sys.argv)
        except Exception as exc:
            import ctypes
            ctypes.windll.user32.MessageBoxW(None, 'QuickSpeak could not start (' + type(exc).__name__ + '). Run setup.ps1 or rebuild the package. No text has been saved.', 'QuickSpeak', 0x10)
            raise
