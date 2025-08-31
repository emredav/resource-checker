"""Tests for the webhook settings window functionality."""

import tkinter as tk

from gui.main_window import SystemMonitorGUI
import requests
import traceback
from tkinter import messagebox

class _Resp:
    def __init__(self, code=200):
        self.status_code = code


def test_webhook_window_open_and_add():
    root = tk.Tk()
    root.withdraw()
    try:
        gui = SystemMonitorGUI(root)
        # Initially no window
        assert gui.webhook_settings_window is None
        gui.open_webhook_settings()
        assert gui.webhook_settings_window is not None
        assert gui.webhook_settings_window.winfo_exists()

        win = gui.webhook_settings_window
        initial_count = len(win.tree.get_children())

        # Initial mode state assertions
        assert win.mode_label.cget("text").startswith("Mode: Add"), "Initial mode should be Add New"
        add_state = win.add_btn['state']
        print('Add button state:', add_state)
        # Tkinter'da bazı platformlarda 'normal', bazılarında tk.NORMAL dönebilir
        assert str(add_state).lower() == 'normal', f"Unexpected add button state: {add_state}"
        assert str(win.save_btn['state']).lower() == 'disabled'
        assert str(win.cancel_btn['state']).lower() == 'disabled'

        # Fill form (Add New)
        win.name_var.set("TestHook")
        win.url_var.set("https://example.com/webhook")
        win.type_var.set("network")
        win._on_type_change()
        # Patch requests.post to avoid network
        orig_post = requests.post
        requests.post = lambda url, json=None, timeout=10: _Resp(200)
        try:
            win.add_webhook()
        finally:
            requests.post = orig_post

        root.update()
        new_count = len(win.tree.get_children())
        assert new_count == initial_count + 1, "Webhook not added to tree"

        # Select first row and load into form for edit (switch to edit mode)
        first_item = win.tree.get_children()[0]
        win.tree.selection_set(first_item)
        win._on_tree_select()  # should switch to edit mode
        assert win.mode_label.cget("text").startswith("Mode: Editing"), "Mode label should indicate Editing"
        assert str(win.add_btn['state']).lower() == 'disabled' , "Add button should be disabled in edit mode"
        assert str(win.save_btn['state']).lower() == 'normal', "Save button should be enabled in edit mode"
        assert str(win.cancel_btn['state']).lower() == 'normal', "Cancel should be enabled in edit mode"
        # Edit URL
        win.url_var.set("https://example.com/updated")
        # Save edit (update)
        orig_post = requests.post
        requests.post = lambda url, json=None, timeout=10: _Resp(200)
        try:
            win.update_webhook()
        finally:
            requests.post = orig_post
        # Verify updated in tree (re-find row by name)
        for iid in win.tree.get_children():
            vals = win.tree.item(iid, "values")
            if vals[0] == "TestHook":
                assert vals[1] == "https://example.com/updated"
                first_item = iid
                break
        else:
            raise AssertionError("Updated webhook row not found")

        # Test send test message
        win.tree.selection_set(first_item)
        orig_post = requests.post
        requests.post = lambda url, json=None, timeout=10: _Resp(200)
        # Monkeypatch messagebox to avoid blocking
        orig_mb = messagebox.showinfo
        messagebox.showinfo = lambda *a, **kw: None
        try:
            win.test_selected()
        finally:
            requests.post = orig_post
            messagebox.showinfo = orig_mb

        # Cancel edit mode and verify return to Add mode
        win.cancel_btn.invoke()
        assert win._editing_name is None
        assert win.mode_label.cget("text").startswith("Mode: Add"), "Should return to Add mode after cancel"
        # Buton state'lerini platformdan bağımsız karşılaştır
        add_btn_state = str(win.add_btn['state']).lower()
        save_btn_state = str(win.save_btn['state']).lower()
        cancel_btn_state = str(win.cancel_btn['state']).lower()
        print('Add:', add_btn_state, 'Save:', save_btn_state, 'Cancel:', cancel_btn_state)
        assert add_btn_state == 'normal', f"Add button should be enabled after cancel, got: {add_btn_state}"
        assert save_btn_state == 'disabled', f"Save button should be disabled after cancel, got: {save_btn_state}"
        assert cancel_btn_state == 'disabled', f"Cancel button should be disabled after cancel, got: {cancel_btn_state}"

        # === Delete (Remove) Test ===
        # Select the webhook again and remove it
        # Find the item with name TestHook
        target_iid = None
        for iid in win.tree.get_children():
            if win.tree.item(iid, 'values')[0] == 'TestHook':
                target_iid = iid
                break
        assert target_iid is not None, "TestHook row should exist before delete"
        count_before_delete = len(win.tree.get_children())
        win.tree.selection_set(target_iid)
        win.remove_selected()  # perform deletion
        root.update()
        count_after_delete = len(win.tree.get_children())
        assert count_after_delete == count_before_delete - 1, "Row count should decrease by 1 after deletion"
        assert 'TestHook' not in win.webhook_config.webhooks, "Webhook config should not contain deleted entry"
        print('✅ Delete test passed')

        # Re-open should focus existing window, not create new
        gui.open_webhook_settings()
        assert gui.webhook_settings_window is win
        print("✅ Webhook window add/edit/test/delete passed")
        return True
    except Exception as e:
        print("❌ Webhook window test failed:", e)
        traceback.print_exc()
        return False
    finally:
        root.destroy()


if __name__ == "__main__":
    ok = test_webhook_window_open_and_add()
    print("Result:", "PASS" if ok else "FAIL")