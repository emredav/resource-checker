"""Webhook settings window implementation."""

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
from core.network import WebhookNotifier
from core.language import language_manager


class WebhookSettingsWindow(tk.Toplevel):
    """Window for managing webhook configurations."""

    def __init__(self, master, webhook_config, webhook_notifier: WebhookNotifier | None = None):
        super().__init__(master)
        self.title(language_manager.get_text('webhook_window_title'))
        self.geometry("820x460")
        self.resizable(False, False)
        self.webhook_config = webhook_config
        self.webhook_notifier = webhook_notifier or WebhookNotifier(self.webhook_config)
        self._editing_name = None  # Track which webhook is being edited
        self._mode = "add"  # 'add' or 'edit'

        self._build_ui()
        self._populate_tree()

    # UI -----------------------------------------------------------------
    def _build_ui(self):
        form = ttk.Frame(self, padding=10)
        form.pack(fill=tk.X, anchor=tk.N)

        ttk.Label(form, text=language_manager.get_text('name_label')).grid(row=0, column=0, sticky=tk.W)
        self.name_var = tk.StringVar()
        ttk.Entry(form, textvariable=self.name_var, width=18).grid(row=0, column=1, padx=5, pady=2)

        ttk.Label(form, text=language_manager.get_text('url_label')).grid(row=1, column=0, sticky=tk.W)
        self.url_var = tk.StringVar()
        ttk.Entry(form, textvariable=self.url_var, width=42).grid(row=1, column=1, columnspan=4, padx=5, pady=2, sticky=tk.W)

        ttk.Label(form, text=language_manager.get_text('type_label')).grid(row=0, column=2, sticky=tk.W)
        self.type_var = tk.StringVar(value="network")
        type_combo = ttk.Combobox(form, textvariable=self.type_var, values=["network", "cpu"], width=10, state="readonly")
        type_combo.grid(row=0, column=3, padx=5, pady=2)
        type_combo.bind("<<ComboboxSelected>>", lambda e: self._on_type_change())

        self.active_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(form, text=language_manager.get_text('active_label'), variable=self.active_var).grid(row=0, column=4, padx=5, pady=2)

        ttk.Label(form, text=language_manager.get_text('threshold_label')).grid(row=2, column=0, sticky=tk.W)
        self.threshold_var = tk.StringVar(value="80")
        self.threshold_entry = ttk.Entry(form, textvariable=self.threshold_var, width=10)
        self.threshold_entry.grid(row=2, column=1, sticky=tk.W, pady=2)

        # Mode indicator
        self.mode_label = ttk.Label(self, text=language_manager.get_text('mode_add_new'), padding=(12, 2))
        self.mode_label.pack(anchor=tk.W)

        btn_frame = ttk.Frame(self, padding=(10, 0, 10, 5))
        btn_frame.pack(fill=tk.X)
        self.add_btn = ttk.Button(btn_frame, text=language_manager.get_text('add_new_btn'), command=self.add_webhook)
        self.add_btn.pack(side=tk.LEFT)
        self.save_btn = ttk.Button(btn_frame, text=language_manager.get_text('save_changes_btn'), command=self.update_webhook, state=tk.DISABLED)
        self.save_btn.pack(side=tk.LEFT, padx=5)
        self.cancel_btn = ttk.Button(btn_frame, text=language_manager.get_text('cancel_edit_btn'), command=lambda: self._clear_form(clear_name=True), state=tk.DISABLED)
        self.cancel_btn.pack(side=tk.LEFT, padx=5)
        self.test_btn = ttk.Button(btn_frame, text=language_manager.get_text('send_test_btn'), command=self.test_selected)
        self.test_btn.pack(side=tk.LEFT, padx=5)
        self.remove_btn = ttk.Button(btn_frame, text=language_manager.get_text('remove_selected_btn'), command=self.remove_selected)
        self.remove_btn.pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text=language_manager.get_text('close_btn'), command=self.destroy).pack(side=tk.RIGHT)

        # Treeview with URL column
        columns = ("name", "url", "type", "active", "threshold")
        self.tree = ttk.Treeview(self, columns=columns, show="headings", height=13)
        col_specs = {
            "name": (140, tk.W),
            "url": (260, tk.W),
            "type": (80, tk.CENTER),
            "active": (70, tk.CENTER),
            "threshold": (90, tk.CENTER)
        }
        for col in columns:
            self.tree.heading(col, text=col.capitalize())
            width, anchor = col_specs[col]
            self.tree.column(col, width=width, anchor=anchor)
        self.tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        self.tree.bind("<<TreeviewSelect>>", self._on_tree_select)
        self.tree.bind("<Double-1>", self._on_tree_double_click)

        self._on_type_change()

    # Event handlers ------------------------------------------------------
    def _on_type_change(self):
        if self.type_var.get() == "cpu":
            self.threshold_entry.config(state="normal")
        else:
            self.threshold_entry.config(state="disabled")

    # Data ops ------------------------------------------------------------
    def _populate_tree(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        for name, cfg in self.webhook_config.webhooks.items():
            self.tree.insert(
                "",
                tk.END,
                values=(
                    name,
                    cfg['url'],
                    cfg['type'],
                    "Yes" if cfg['active'] else "No",
                    cfg.get('threshold') if cfg.get('threshold') is not None else "-"
                )
            )

    def add_webhook(self):
        name = self.name_var.get().strip()
        url = self.url_var.get().strip()
        wtype = self.type_var.get()
        if not name or not url:
            messagebox.showwarning(language_manager.get_text('validation_title'), language_manager.get_text('validation_name_url_required'))
            return
        if name in self.webhook_config.webhooks:
            messagebox.showerror(language_manager.get_text('duplicate_title'), language_manager.get_text('duplicate_exists').format(name))
            return
        threshold = None
        if wtype == "cpu":
            try:
                threshold = float(self.threshold_var.get())
            except ValueError:
                messagebox.showerror(language_manager.get_text('validation_title'), language_manager.get_text('threshold_number_error'))
                return
        self.webhook_config.add_webhook(name, url, wtype, self.active_var.get(), threshold)
        self._populate_tree()
        self._clear_form(clear_name=True)

    def update_webhook(self):
        if not self._editing_name:
            return
        name = self.name_var.get().strip()
        url = self.url_var.get().strip()
        wtype = self.type_var.get()
        if not name or not url:
            messagebox.showwarning(language_manager.get_text('validation_title'), language_manager.get_text('validation_name_url_required'))
            return
        threshold = None
        if wtype == "cpu":
            try:
                threshold = float(self.threshold_var.get())
            except ValueError:
                messagebox.showerror(language_manager.get_text('validation_title'), language_manager.get_text('threshold_number_error'))
                return
        # Handle rename
        if name != self._editing_name and name in self.webhook_config.webhooks:
            messagebox.showerror(language_manager.get_text('duplicate_title'), language_manager.get_text('duplicate_rename_error').format(name))
            return
        # Remove old if renamed
        if name != self._editing_name:
            self.webhook_config.remove_webhook(self._editing_name)
        self.webhook_config.add_webhook(name, url, wtype, self.active_var.get(), threshold)
        self._editing_name = name
        self._populate_tree()
        self._set_edit_mode(name)

    def remove_selected(self):
        selected = self.tree.selection()
        if not selected:
            return
        for item in selected:
            name = self.tree.item(item, "values")[0]
            self.webhook_config.remove_webhook(name)
        self._populate_tree()
        self._clear_form(clear_name=True)

    # Helpers ------------------------------------------------------------
    def _clear_form(self, clear_name=False):
        if clear_name:
            self.name_var.set("")
        self.url_var.set("")
        self.type_var.set("network")
        self.active_var.set(True)
        self.threshold_var.set("80")
        self._on_type_change()
        self._editing_name = None
        self._mode = "add"
        self.mode_label.config(text=language_manager.get_text('mode_add_new'))
        self.save_btn.config(state=tk.DISABLED)
        self.add_btn.config(state=tk.NORMAL)
        self.cancel_btn.config(state=tk.DISABLED)

    def _on_tree_select(self, event=None):
        sel = self.tree.selection()
        if not sel:
            return
        item = sel[0]
        name, url, wtype, active, threshold = self.tree.item(item, "values")
        self.name_var.set(name)
        self.url_var.set(url)
        self.type_var.set(wtype)
        self.active_var.set(active == "Yes")
        if wtype == "cpu" and threshold not in ("-", "", None):
            self.threshold_var.set(str(threshold))
        else:
            self.threshold_var.set("80")
        self._on_type_change()
        self._set_edit_mode(name)

    def _set_edit_mode(self, name: str):
        self._editing_name = name
        self._mode = "edit"
        self.mode_label.config(text=language_manager.get_text('mode_editing').format(name))
        self.save_btn.config(state=tk.NORMAL)
        self.add_btn.config(state=tk.DISABLED)
        self.cancel_btn.config(state=tk.NORMAL)

    def _on_tree_double_click(self, event):
        # Double click toggles active status quickly
        sel = self.tree.selection()
        if not sel:
            return
        item = sel[0]
        name = self.tree.item(item, "values")[0]
        cfg = self.webhook_config.webhooks.get(name)
        if not cfg:
            return
        new_active = not cfg['active']
        self.webhook_config.update_webhook_status(name, new_active)
        self._populate_tree()

    # Test sending -------------------------------------------------------
    def test_selected(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo(language_manager.get_text('test_title'), language_manager.get_text('test_select_warning'))
            return
        sent = 0
        failed = 0
        for item in sel:
            name, url, wtype, active, threshold = self.tree.item(item, "values")
            # Ignore inactive
            cfg = self.webhook_config.webhooks.get(name)
            if not cfg:
                continue
            title = language_manager.get_text('test_message_title')
            msg = language_manager.get_text('test_message_body').format(
                name,
                cfg['type'],
                cfg['active'],
                datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            )
            ok = self.webhook_notifier.send_teams_message(cfg['url'], title, msg, color="0078D7")
            if ok:
                sent += 1
            else:
                failed += 1
        messagebox.showinfo(language_manager.get_text('test_results_title'), language_manager.get_text('test_results_message').format(sent, failed))