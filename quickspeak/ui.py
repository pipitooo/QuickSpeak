import tkinter as tk
from tkinter import ttk, messagebox
from .settings import Settings, VOICES, startup_enabled, set_startup

class Window:
    def __init__(self, root, app):
        self.root, self.app = root, app
        root.title('QuickSpeak')
        root.geometry('540x600')
        root.minsize(460, 580)
        from PIL import ImageTk
        from .tray import icon_image
        self.icon = ImageTk.PhotoImage(icon_image())
        root.iconphoto(True, self.icon)
        root.protocol('WM_DELETE_WINDOW', root.withdraw)
        style = ttk.Style(root)
        style.theme_use('vista')
        style.configure('TLabel', font=('Segoe UI', 10))
        style.configure('TButton', font=('Segoe UI', 10), padding=(10, 5))
        frame = ttk.Frame(root, padding=20)
        frame.pack(fill='both', expand=True)
        ttk.Label(frame, text='QuickSpeak', font=('Segoe UI', 21, 'bold')).pack(anchor='w')
        ttk.Label(frame, text='Select text anywhere, then press your shortcut.').pack(anchor='w', pady=(2, 12))
        self.text = tk.Text(frame, height=7, wrap='word', font=('Segoe UI', 11), undo=True, relief='solid', borderwidth=1)
        self.text.pack(fill='both', expand=True)
        row = ttk.Frame(frame)
        row.pack(fill='x', pady=10)
        ttk.Button(row, text='Read', command=lambda: app.read(self.text.get('1.0', 'end'))).pack(side='left')
        ttk.Button(row, text='Pause / Resume', command=app.pause).pack(side='left', padx=8)
        ttk.Button(row, text='Stop', command=app.stop).pack(side='left')
        controls = ttk.Frame(frame)
        controls.pack(fill='x')
        controls.columnconfigure(1, weight=1)
        self.voice = tk.StringVar(value=app.settings.voice)
        self.speed = tk.DoubleVar(value=app.settings.speed)
        self.volume = tk.DoubleVar(value=app.settings.volume)
        self.shortcut = tk.StringVar(value=app.settings.shortcut)
        self.startup = tk.BooleanVar(value=startup_enabled())
        ttk.Label(controls, text='Voice').grid(row=0, column=0, sticky='w', padx=(0, 16), pady=5)
        voice = ttk.Combobox(controls, values=VOICES, textvariable=self.voice, state='readonly')
        voice.grid(row=0, column=1, sticky='ew')
        voice.bind('<<ComboboxSelected>>', lambda event: self.live_preferences())
        ttk.Label(controls, text='Speed').grid(row=1, column=0, sticky='w', pady=5)
        self.speed_label = ttk.Label(controls, width=6)
        self.speed_label.grid(row=1, column=2)
        ttk.Scale(controls, from_=0.5, to=2, variable=self.speed, command=lambda _: self.live_preferences()).grid(row=1, column=1, sticky='ew')
        ttk.Label(controls, text='Volume').grid(row=2, column=0, sticky='w', pady=5)
        self.volume_label = ttk.Label(controls, width=6)
        self.volume_label.grid(row=2, column=2)
        ttk.Scale(controls, from_=0, to=1, variable=self.volume, command=lambda _: self.live_preferences()).grid(row=2, column=1, sticky='ew')
        ttk.Label(controls, text='Shortcut').grid(row=3, column=0, sticky='w', pady=5)
        ttk.Entry(controls, textvariable=self.shortcut).grid(row=3, column=1, sticky='ew')
        ttk.Checkbutton(frame, text='Launch QuickSpeak when I sign in', variable=self.startup).pack(anchor='w', pady=(10, 5))
        bottom = ttk.Frame(frame)
        bottom.pack(fill='x')
        ttk.Button(bottom, text='Save settings', command=self.save).pack(side='right')
        ttk.Button(bottom, text='Hide to tray', command=root.withdraw).pack(side='right', padx=8)
        ttk.Button(bottom, text='Exit', command=app.close).pack(side='left')
        self.status = tk.StringVar(value='Loading local voices…')
        ttk.Label(frame, textvariable=self.status, wraplength=480).pack(anchor='w', pady=(12, 0))
        self.live_preferences()

    def live_preferences(self):
        self.speed_label.configure(text=f'{self.speed.get():.2f}×')
        self.volume_label.configure(text=f'{self.volume.get():.0%}')
        self.app.settings.voice = self.voice.get()
        self.app.settings.speed = round(self.speed.get(), 2)
        self.app.settings.volume = round(self.volume.get(), 2)
        self.app.audio.volume = self.volume.get()

    def save(self):
        old_shortcut = self.app.settings.shortcut
        old_startup = startup_enabled()
        try:
            self.app.hotkey.set(self.shortcut.get())
            set_startup(self.startup.get())
            self.app.settings.shortcut = self.shortcut.get()
            self.app.settings.save()
            self.app.set_status('Settings saved')
        except Exception as exc:
            self.app.settings.shortcut = old_shortcut
            try:
                self.app.hotkey.set(old_shortcut)
                if startup_enabled() != old_startup:
                    set_startup(old_startup)
            except Exception:
                pass
            messagebox.showerror('Could not save settings', str(exc), parent=self.root)

    def show(self):
        self.root.deiconify()
        self.root.lift()
