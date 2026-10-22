import argparse
import csv
import ctypes
import os
import sys
import time
from PIL import Image

# Switch thread desktop to 'Default' BEFORE importing pywinauto
user32 = ctypes.windll.user32
hdesk = user32.OpenDesktopW("Default", 0, False, 0x01FF)
if hdesk:
    user32.SetThreadDesktop(hdesk)

from pywinauto import Application, Desktop

def get_gpower_app_and_win():
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

    curr_pid = ctypes.c_ulong()
    user32.GetWindowThreadProcessId(hwnd_target, ctypes.byref(curr_pid))

    app = Application(backend="uia").connect(handle=hwnd_target)
    win = app.window(handle=hwnd_target)
    return app, win, hwnd_target, curr_pid.value

def check_for_dialog(pid, main_hwnd):
    popups = []
    def enum_cb(hwnd, extra):
        if hwnd != main_hwnd:
            curr_pid = ctypes.c_ulong()
            user32.GetWindowThreadProcessId(hwnd, ctypes.byref(curr_pid))
            if curr_pid.value == pid and user32.IsWindowVisible(hwnd):
                popups.append(hwnd)
        return True

    WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)
    cb = WNDENUMPROC(enum_cb)
    user32.EnumWindows(cb, 0)
    return popups

def extract_dialog_text_and_dismiss(popup_hwnd, win, screenshot_path):
    msg_parts = []
    ok_button_hwnd = None

    WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)

    def enum_child(hwnd, extra):
        nonlocal ok_button_hwnd
        length = user32.GetWindowTextLengthW(hwnd)
        buff = ctypes.create_unicode_buffer(length + 1)
        if length > 0:
            user32.GetWindowTextW(hwnd, buff, length + 1)
        txt = buff.value.strip()

        cls_buff = ctypes.create_unicode_buffer(256)
        user32.GetClassNameW(hwnd, cls_buff, 256)
        cls_name = cls_buff.value

        if "Button" in cls_name and txt in ["OK", "&OK"]:
            ok_button_hwnd = hwnd
        elif txt and txt not in ["OK", "&OK", "Cancel"]:
            msg_parts.append(txt)
        return True

    user32.EnumChildWindows(popup_hwnd, WNDENUMPROC(enum_child), 0)

    buf_title = ctypes.create_unicode_buffer(256)
    user32.GetWindowTextW(popup_hwnd, buf_title, 256)
    dlg_title = buf_title.value

    full_msg = " | ".join(msg_parts) if msg_parts else dlg_title

    # Capture composite screenshot
    try:
        main_img = win.capture_as_image()
        try:
            dlg_w32 = Desktop(backend="win32").window(handle=popup_hwnd)
            dlg_img = dlg_w32.capture_as_image()
            main_rect = win.rectangle()
            dlg_rect = dlg_w32.rectangle()
            offset_x = max(0, dlg_rect.left - main_rect.left)
            offset_y = max(0, dlg_rect.top - main_rect.top)
            main_img.paste(dlg_img, (offset_x, offset_y))
        except Exception:
            pass
        main_img.save(screenshot_path)
    except Exception as e:
        print(f"Screenshot error on dialog: {e}")

    # Dismiss dialog
    if ok_button_hwnd:
        user32.SendMessageW(ok_button_hwnd, 0x00F5, 0, 0) # BM_CLICK
    else:
        user32.SendMessageW(popup_hwnd, 0x0111, 1, 0) # WM_COMMAND IDOK
    time.sleep(0.2)
    if user32.IsWindow(popup_hwnd):
        user32.SendMessageW(popup_hwnd, 0x0010, 0, 0) # WM_CLOSE

    return full_msg

def collect_oracle(csv_path="oracle/gpower_vectors.csv", screenshot_dir="oracle/screenshots", max_rows=None, start_row=0, target_ids=None):
    os.makedirs(screenshot_dir, exist_ok=True)
    app, win, main_hwnd, pid = get_gpower_app_and_win()
    win.set_focus()

    # Input controls
    edit_f = win.child_window(auto_id="1020", control_type="Edit")
    edit_alpha = win.child_window(auto_id="1021", control_type="Edit")
    edit_power = win.child_window(auto_id="1022", control_type="Edit")
    edit_k = win.child_window(auto_id="1023", control_type="Edit")
    btn_calc = win.child_window(auto_id="1009", control_type="Button")

    # Output controls
    edit_ncp = win.child_window(auto_id="1050", control_type="Edit")
    edit_crit_f = win.child_window(auto_id="1051", control_type="Edit")
    edit_df1 = win.child_window(auto_id="1052", control_type="Edit")
    edit_df2 = win.child_window(auto_id="1053", control_type="Edit")
    edit_n = win.child_window(auto_id="1054", control_type="Edit")
    edit_act_power = win.child_window(auto_id="1055", control_type="Edit")

    with open(csv_path, "r", encoding="utf-8-sig") as f:
        reader = list(csv.DictReader(f))
        fieldnames = list(reader[0].keys()) if reader else []

    processed_count = 0

    for i, row in enumerate(reader):
        row_id = row.get("id", f"row_{i+1}")

        if target_ids is not None:
            if row_id not in target_ids:
                continue
        else:
            if i < start_row:
                continue
            if max_rows is not None and processed_count >= max_rows:
                break

        k_val = str(row.get("k_groups", "")).strip()
        f_val = str(row.get("effect_size_f", "")).strip()
        alpha_val = str(row.get("alpha", "")).strip()
        power_val = str(row.get("power", "")).strip()
        screenshot_file = row.get("screenshot_file", f"{row_id}.png").strip()
        screenshot_path = os.path.join(screenshot_dir, screenshot_file)

        print(f"\n--- Processing {row_id} (row {i+1}/{len(reader)}): k={k_val}, f={f_val}, alpha={alpha_val}, power={power_val} ---")

        # Set inputs
        for edit_ctrl, val_str, name in [
            (edit_f, f_val, "f"),
            (edit_alpha, alpha_val, "alpha"),
            (edit_power, power_val, "power"),
            (edit_k, k_val, "k")
        ]:
            try:
                edit_ctrl.set_text(val_str)
            except Exception:
                edit_ctrl.type_keys("^a{BACKSPACE}" + val_str)

        time.sleep(0.1)

        # Trigger Calculate
        try:
            btn_calc.invoke()
        except Exception:
            btn_calc.click()

        time.sleep(0.4)

        # Check for dialogs
        popups = check_for_dialog(pid, main_hwnd)

        if popups:
            popup_hwnd = popups[0]
            print(f"  [DIALOG DETECTED] Popup HWND: {popup_hwnd}")
            msg = extract_dialog_text_and_dismiss(popup_hwnd, win, screenshot_path)
            print(f"  Dialog Message: {msg}")

            row["noncentrality"] = ""
            row["critical_F"] = ""
            row["df1"] = ""
            row["df2"] = ""
            row["total_N"] = ""
            row["actual_power"] = ""
            row["gui_message_or_notes"] = f"Dialog: {msg}"
        else:
            # Read outputs directly from G*Power
            ncp_val = edit_ncp.get_value().strip()
            crit_f_val = edit_crit_f.get_value().strip()
            df1_val = edit_df1.get_value().strip()
            df2_val = edit_df2.get_value().strip()
            n_val = edit_n.get_value().strip()
            act_power_val = edit_act_power.get_value().strip()

            img = win.capture_as_image()
            img.save(screenshot_path)

            has_question_mark = any("?" in val for val in [ncp_val, crit_f_val, df1_val, df2_val, n_val, act_power_val])

            if has_question_mark:
                print(f"  [QUESTION MARK DETECTED] G*Power left '?' in output fields.")
                row["noncentrality"] = ""
                row["critical_F"] = ""
                row["df1"] = ""
                row["df2"] = ""
                row["total_N"] = ""
                row["actual_power"] = ""
                row["gui_message_or_notes"] = f"G*Power output contained '?' (ncp={ncp_val}, N={n_val}, power={act_power_val})"
            else:
                row["noncentrality"] = ncp_val
                row["critical_F"] = crit_f_val
                row["df1"] = df1_val
                row["df2"] = df2_val
                row["total_N"] = n_val
                row["actual_power"] = act_power_val
                print(f"  Results read: N={n_val}, df1={df1_val}, df2={df2_val}, lambda={ncp_val}, critF={crit_f_val}, actPower={act_power_val}")

        processed_count += 1

        # Save after every row to persist progress
        with open(csv_path, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(reader)

    print(f"\nFinished processing {processed_count} rows. All updates saved to {csv_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--rows", type=int, default=None, help="Number of rows to process")
    parser.add_argument("--start", type=int, default=0, help="Row index to start at (0-based)")
    parser.add_argument("--ids", type=str, default=None, help="Comma-separated IDs to process (e.g. v017,v022)")
    args = parser.parse_args()

    ids_set = set(args.ids.split(",")) if args.ids else None
    collect_oracle(max_rows=args.rows, start_row=args.start, target_ids=ids_set)
