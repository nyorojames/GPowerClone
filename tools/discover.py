import ctypes
import io
import sys

# Switch thread desktop to 'Default' BEFORE importing pywinauto,
# because SetThreadDesktop fails once pywinauto initializes thread hooks/windows.
user32 = ctypes.windll.user32
hdesk = user32.OpenDesktopW("Default", 0, False, 0x01FF)
if hdesk:
    user32.SetThreadDesktop(hdesk)

from pywinauto import Application

def get_gpower_window():
    hwnd_target = None
    def enum_cb(hwnd, extra):
        nonlocal hwnd_target
        length = user32.GetWindowTextLengthW(hwnd)
        if length > 0:
            buff = ctypes.create_unicode_buffer(length + 1)
            user32.GetWindowTextW(hwnd, buff, length + 1)
            if "G*Power" in buff.value:
                hwnd_target = hwnd
                return False
        return True

    WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)
    cb = WNDENUMPROC(enum_cb)
    user32.EnumWindows(cb, 0)

    if not hwnd_target:
        raise RuntimeError("G*Power window not found.")

    app = Application(backend="uia").connect(handle=hwnd_target)
    return app.window(handle=hwnd_target)

if __name__ == "__main__":
    win = get_gpower_window()
    print("Found G*Power window:", win.window_text())

    # Capture control identifiers
    old_stdout = sys.stdout
    buf = io.StringIO()
    sys.stdout = buf
    try:
        win.print_control_identifiers()
    finally:
        sys.stdout = old_stdout

    dump = buf.getvalue()
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

    print(dump)

    with open("tools/controls_dump.txt", "w", encoding="utf-8") as f:
        f.write(dump)
    print("\nSaved dump to tools/controls_dump.txt")
