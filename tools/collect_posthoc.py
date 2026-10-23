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
        raise RuntimeError("G*Power window not found. Please open G*Power 3.1.9.7.")

    curr_pid = ctypes.c_ulong()
    user32.GetWindowThreadProcessId(hwnd_target, ctypes.byref(curr_pid))

    app = Application(backend="uia").connect(handle=hwnd_target)
    win = app.window(handle=hwnd_target)
    return app, win, hwnd_target, curr_pid.value

def ensure_posthoc_mode(win):
    cb_family = win.child_window(auto_id="1000", control_type="ComboBox")
    cb_test = win.child_window(auto_id="1001", control_type="ComboBox")
    cb_type = win.child_window(auto_id="1002", control_type="ComboBox")

    fam_val = cb_family.legacy_properties().get("Value", "")
    if "F tests" not in fam_val:
        cb_family.select("F tests")
        time.sleep(0.2)

    test_val = cb_test.legacy_properties().get("Value", "")
    if "ANOVA: Fixed effects, omnibus, one-way" not in test_val:
        cb_test.select("ANOVA: Fixed effects, omnibus, one-way")
        time.sleep(0.2)

    type_val = cb_type.legacy_properties().get("Value", "")
    if "Post hoc" not in type_val:
        cb_type.select("Post hoc: Compute achieved power - given α, sample size, and effect size")
        time.sleep(0.2)

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
        user32.SetForegroundWindow(win.handle)
        user32.SetForegroundWindow(popup_hwnd)
        time.sleep(0.3)
        main_img = win.capture_as_image()
        try:
            dlg_w32 = Desktop(backend="win32").window(handle=popup_hwnd)
            dlg_img = dlg_w32.capture_as_image()
            main_rect = win.rectangle()
            dlg_rect = dlg_w32.rectangle()
            offset_x = max(0, dlg_rect.left - main_rect.left)
            offset_y = max(0, dlg_rect.top - main_rect.top)
            main_img.paste(dlg_img, (offset_x, offset_y))
        except Exception as e:
            print(f"Composite paste error: {e}")
        main_img.save(screenshot_path)

        # Also save alias without leading zero if applicable (e.g. p33.png as well as p033.png)
        base = os.path.basename(screenshot_path)
        if base.startswith("p0") and len(base) == 8:
            short_base = "p" + base[2:]
            short_path = os.path.join(os.path.dirname(screenshot_path), short_base)
            main_img.save(short_path)
    except Exception as e:
        print(f"Screenshot error on dialog: {e}")

    # Dismiss dialog
    if ok_button_hwnd:
        btn_id = user32.GetDlgCtrlID(ok_button_hwnd)
        user32.SendMessageW(popup_hwnd, 0x0111, btn_id, ok_button_hwnd)
        user32.SendMessageW(ok_button_hwnd, 0x00F5, 0, 0) # BM_CLICK
    else:
        user32.SendMessageW(popup_hwnd, 0x0111, 1, 0) # IDOK
        user32.SendMessageW(popup_hwnd, 0x0111, 2, 0) # IDCANCEL
    time.sleep(0.2)
    if user32.IsWindow(popup_hwnd):
        user32.SendMessageW(popup_hwnd, 0x0010, 0, 0) # WM_CLOSE

    return full_msg

def collect_posthoc(
    input_csv="oracle/posthoc_inputs.csv",
    output_csv="oracle/posthoc_vectors.csv",
    screenshot_dir="oracle/screenshots",
    max_rows=None,
    start_row=0,
    target_ids=None
):
    os.makedirs(screenshot_dir, exist_ok=True)
    os.makedirs(os.path.dirname(output_csv) if os.path.dirname(output_csv) else ".", exist_ok=True)

    app, win, main_hwnd, pid = get_gpower_app_and_win()
    win.set_focus()
    ensure_posthoc_mode(win)

    # Input controls
    edit_f = win.child_window(auto_id="1020", control_type="Edit")
    edit_alpha = win.child_window(auto_id="1021", control_type="Edit")
    edit_n = win.child_window(auto_id="1022", control_type="Edit")
    edit_k = win.child_window(auto_id="1023", control_type="Edit")
    btn_calc = win.child_window(auto_id="1009", control_type="Button")

    # Output controls
    edit_ncp = win.child_window(auto_id="1050", control_type="Edit")
    edit_crit_f = win.child_window(auto_id="1051", control_type="Edit")
    edit_df1 = win.child_window(auto_id="1052", control_type="Edit")
    edit_df2 = win.child_window(auto_id="1053", control_type="Edit")
    edit_power = win.child_window(auto_id="1054", control_type="Edit")

    fieldnames = [
        "id",
        "f",
        "alpha",
        "n_total",
        "groups",
        "f_typed",
        "alpha_typed",
        "n_total_typed",
        "groups_typed",
        "f_displayed",
        "alpha_displayed",
        "n_total_displayed",
        "groups_displayed",
        "ncp",
        "critical_F",
        "df1",
        "df2",
        "power",
        "notes",
        "screenshot_file",
        "probe"
    ]

    with open(input_csv, "r", encoding="utf-8-sig") as f:
        input_rows = list(csv.DictReader(f))

    # Read existing output rows if file exists
    existing_rows = {}
    if os.path.exists(output_csv):
        with open(output_csv, "r", encoding="utf-8-sig") as f:
            for r in csv.DictReader(f):
                if r.get("id"):
                    existing_rows[r["id"]] = r

    processed_count = 0
    prev_outputs = None
    prev_inputs = None

    target_ids_normalized = set()
    if target_ids is not None:
        for tid in target_ids:
            clean = tid.strip().lower()
            target_ids_normalized.add(clean)
            num_part = clean.lstrip("p")
            if num_part.isdigit():
                target_ids_normalized.add(f"p{int(num_part):03d}")
                target_ids_normalized.add(f"p{int(num_part)}")
                target_ids_normalized.add(str(int(num_part)))

    results = []

    for i, in_row in enumerate(input_rows):
        row_id = f"p{i+1:03d}"

        if target_ids_normalized:
            if row_id not in target_ids_normalized:
                if row_id in existing_rows:
                    results.append(existing_rows[row_id])
                continue
        else:
            if i < start_row:
                if row_id in existing_rows:
                    results.append(existing_rows[row_id])
                continue
            if max_rows is not None and processed_count >= max_rows:
                if row_id in existing_rows:
                    results.append(existing_rows[row_id])
                continue

        f_val = str(in_row.get("f", "")).strip()
        alpha_val = str(in_row.get("alpha", "")).strip()
        n_val = str(in_row.get("n_total", "")).strip()
        k_val = str(in_row.get("groups", "")).strip()
        probe_val = str(in_row.get("probe", "")).strip()

        screenshot_file = f"{row_id}.png"
        screenshot_path = os.path.join(screenshot_dir, screenshot_file)

        print(f"\n--- Processing {row_id} (row {i+1}/{len(input_rows)}): f={f_val}, alpha={alpha_val}, N={n_val}, groups={k_val} ---")

        # Set input edits
        for edit_ctrl, val_str in [
            (edit_f, f_val),
            (edit_alpha, alpha_val),
            (edit_n, n_val),
            (edit_k, k_val)
        ]:
            try:
                edit_ctrl.set_text(val_str)
            except Exception:
                edit_ctrl.type_keys("^a{BACKSPACE}" + val_str)

        time.sleep(0.1)

        # Read back displayed inputs
        f_disp = edit_f.get_value().strip()
        alpha_disp = edit_alpha.get_value().strip()
        n_disp = edit_n.get_value().strip()
        k_disp = edit_k.get_value().strip()

        # Trigger Calculate via PostMessage BM_CLICK to avoid blocking on modal dialogs
        user32.PostMessageW(btn_calc.handle, 0x00F5, 0, 0)
        time.sleep(0.4)

        # Check for dialogs
        popups = check_for_dialog(pid, main_hwnd)
        dialog_msg = ""
        has_dialog = False

        if popups:
            has_dialog = True
            popup_hwnd = popups[0]
            print(f"  [DIALOG DETECTED] Popup HWND: {popup_hwnd}")
            dialog_msg = extract_dialog_text_and_dismiss(popup_hwnd, win, screenshot_path)
            print(f"  Dialog Message: {dialog_msg}")
            time.sleep(0.2)
        else:
            # Capture main window screenshot
            try:
                user32.SetForegroundWindow(win.handle)
                win.set_focus()
                time.sleep(0.3)
                img = win.capture_as_image()
                img.save(screenshot_path)
                base = os.path.basename(screenshot_path)
                if base.startswith("p0") and len(base) == 8:
                    short_base = "p" + base[2:]
                    short_path = os.path.join(os.path.dirname(screenshot_path), short_base)
                    img.save(short_path)
            except Exception as e:
                print(f"Screenshot error: {e}")

        # Read outputs directly from G*Power
        ncp_val = edit_ncp.get_value().strip()
        crit_f_val = edit_crit_f.get_value().strip()
        df1_val = edit_df1.get_value().strip()
        df2_val = edit_df2.get_value().strip()
        power_val = edit_power.get_value().strip()

        current_outputs = (ncp_val, crit_f_val, df1_val, df2_val, power_val)
        current_inputs = (f_val, alpha_val, n_val, k_val)

        has_question_mark = any("?" in val for val in [ncp_val, crit_f_val, df1_val, df2_val, power_val])

        notes_parts = []
        if dialog_msg:
            notes_parts.append(f"Dialog: {dialog_msg}")

        is_same_as_previous = False
        if (
            not has_question_mark
            and prev_outputs is not None
            and current_outputs == prev_outputs
            and current_inputs != prev_inputs
        ):
            is_same_as_previous = True
            notes_parts.append("SAME_AS_PREVIOUS_ROW")

        if has_question_mark:
            print("  [OUTPUT HAS '?'] G*Power refused or cleared outputs.")
            ncp_out = ""
            crit_out = ""
            df1_out = ""
            df2_out = ""
            power_out = ""
            if not dialog_msg:
                notes_parts.append(f"G*Power output contained '?' (ncp={ncp_val}, power={power_val})")
        else:
            ncp_out = ncp_val
            crit_out = crit_f_val
            df1_out = df1_val
            df2_out = df2_val
            power_out = power_val
            print(f"  Results read: ncp={ncp_out}, critF={crit_out}, df1={df1_out}, df2={df2_out}, power={power_out}")
            if dialog_msg:
                print(f"  [INFORMATIONAL DIALOG WITH VALID OUTPUTS RECORDED BOTH]")

        notes_final = " | ".join(notes_parts)

        row_data = {
            "id": row_id,
            "f": f_val,
            "alpha": alpha_val,
            "n_total": n_val,
            "groups": k_val,
            "f_typed": f_val,
            "alpha_typed": alpha_val,
            "n_total_typed": n_val,
            "groups_typed": k_val,
            "f_displayed": f_disp,
            "alpha_displayed": alpha_disp,
            "n_total_displayed": n_disp,
            "groups_displayed": k_disp,
            "ncp": ncp_out,
            "critical_F": crit_out,
            "df1": df1_out,
            "df2": df2_out,
            "power": power_out,
            "notes": notes_final,
            "screenshot_file": screenshot_file,
            "probe": probe_val
        }

        results.append(row_data)
        processed_count += 1
        prev_outputs = current_outputs
        prev_inputs = current_inputs

        # Save after every row
        with open(output_csv, "w", encoding="utf-8-sig", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(results)

    print(f"\nFinished processing {processed_count} rows. All updates saved to {output_csv}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--rows", type=int, default=None, help="Number of rows to process")
    parser.add_argument("--start", type=int, default=0, help="Row index to start at (0-based)")
    parser.add_argument("--ids", type=str, default=None, help="Comma-separated IDs to process (e.g. p001,p002)")
    parser.add_argument("--input", type=str, default="oracle/posthoc_inputs.csv", help="Input CSV path")
    parser.add_argument("--output", type=str, default="oracle/posthoc_vectors.csv", help="Output CSV path")
    parser.add_argument("--screenshots", type=str, default="oracle/screenshots", help="Screenshot output directory")
    args = parser.parse_args()

    ids_set = set(args.ids.split(",")) if args.ids else None
    collect_posthoc(
        input_csv=args.input,
        output_csv=args.output,
        screenshot_dir=args.screenshots,
        max_rows=args.rows,
        start_row=args.start,
        target_ids=ids_set
    )
