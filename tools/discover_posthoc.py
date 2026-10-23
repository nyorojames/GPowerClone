import ctypes
import io
import os
import sys

# Switch thread desktop to 'Default' BEFORE importing pywinauto
user32 = ctypes.windll.user32
hdesk = user32.OpenDesktopW("Default", 0, False, 0x01FF)
if hdesk:
    user32.SetThreadDesktop(hdesk)

from pywinauto import Application

def get_gpower_window():
    hwnd_target = None
    def enum_cb(hwnd, extra):
        nonlocal hwnd_target
        if user32.IsWindowVisible(hwnd):
            length = user32.GetWindowTextLengthW(hwnd)
            if length > 0:
                buff = ctypes.create_unicode_buffer(length + 1)
                user32.GetWindowTextW(hwnd, buff, length + 1)
                if buff.value.startswith("G*Power"):
                    hwnd_target = hwnd
                    return False
        return True

    WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)
    cb = WNDENUMPROC(enum_cb)
    user32.EnumWindows(cb, 0)

    if not hwnd_target:
        raise RuntimeError("G*Power 3.1.9.7 window not found. Please open G*Power 3.1.9.7.")

    app = Application(backend="uia").connect(handle=hwnd_target)
    return app.window(handle=hwnd_target)

def configure_dropdowns(win):
    cb_family = win.child_window(auto_id="1000", control_type="ComboBox")
    cb_test = win.child_window(auto_id="1001", control_type="ComboBox")
    cb_type = win.child_window(auto_id="1002", control_type="ComboBox")

    # Select F tests
    cb_family.select("F tests")

    # Select ANOVA: Fixed effects, omnibus, one-way
    cb_test.select("ANOVA: Fixed effects, omnibus, one-way")

    # Select Post hoc: Compute achieved power
    cb_type.select("Post hoc: Compute achieved power - given α, sample size, and effect size")

if __name__ == "__main__":
    win = get_gpower_window()
    print("Connected to G*Power window:", win.window_text())

    configure_dropdowns(win)
    print("Dropdowns configured: F tests -> ANOVA: Fixed effects, omnibus, one-way -> Post hoc: Compute achieved power")

    # Capture control identifiers
    buf = io.StringIO()
    old_stdout = sys.stdout
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

    os.makedirs("tools", exist_ok=True)
    with open("tools/controls_dump_posthoc.txt", "w", encoding="utf-8") as f:
        f.write(dump)
    print("Saved control tree dump to tools/controls_dump_posthoc.txt")
