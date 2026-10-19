import threading
import pystray
from PIL import Image, ImageDraw

def icon_image():
    image = Image.new('RGBA', (64, 64), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((3, 3, 61, 61), 15, fill='#2765d5')
    draw.polygon([(14, 26), (23, 26), (34, 17), (34, 47), (23, 38), (14, 38)], fill='white')
    draw.arc((26, 16, 51, 48), -65, 65, fill='white', width=4)
    return image

class Tray:
    def __init__(self, dispatch, read, show, stop, close):
        def action(fn):
            return lambda icon, item: dispatch(fn)
        self.icon = pystray.Icon('QuickSpeak', icon_image(), 'QuickSpeak · loading voices', pystray.Menu(
            pystray.MenuItem('Open QuickSpeak', action(show), default=True),
            pystray.MenuItem('Read Clipboard', action(read)),
            pystray.MenuItem('Stop Reading', action(stop)),
            pystray.MenuItem('Settings', action(show)),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem('Exit', action(close))))
        self.thread = threading.Thread(target=self.icon.run, name='tray', daemon=True)
        self.thread.start()

    def notify(self, text):
        try:
            self.icon.notify(text, 'QuickSpeak')
        except Exception:
            pass

    def status(self, text):
        self.icon.title = ('QuickSpeak · ' + text)[:127]

    def close(self):
        self.icon.stop()
        self.thread.join(3)
