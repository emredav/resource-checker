import tkinter as tk
from tkinter import ttk, messagebox
from core.language import language_manager


class NetworkSettingsWindow(tk.Toplevel):
    """Network test hostlarını yönetmek için pencere."""

    def __init__(self, parent, network_checker):
        super().__init__(parent)
        self.title(language_manager.get_text('network_settings_title'))
        self.network_checker = network_checker
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self.resizable(False, False)

        self._build_ui()
        self._populate_hosts()

    def _build_ui(self):
        padding = {'padx': 8, 'pady': 6}

        # Host list label
        self.host_list_label = ttk.Label(self, text=language_manager.get_text('host_list_label'))
        self.host_list_label.grid(row=0, column=0, sticky='w', **padding)

        # Listbox + scrollbar
        list_frame = ttk.Frame(self)
        list_frame.grid(row=1, column=0, columnspan=4, sticky='nsew', **padding)
        self.host_listbox = tk.Listbox(list_frame, selectmode=tk.EXTENDED, width=55, height=8)
        scrollbar = ttk.Scrollbar(list_frame, orient='vertical', command=self.host_listbox.yview)
        self.host_listbox.config(yscrollcommand=scrollbar.set)
        self.host_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Name / Address inputs
        self.name_label = ttk.Label(self, text=language_manager.get_text('host_name_label'))
        self.name_label.grid(row=2, column=0, sticky='e', **padding)
        self.name_entry = ttk.Entry(self, width=20)
        self.name_entry.grid(row=2, column=1, sticky='w', **padding)

        self.address_label = ttk.Label(self, text=language_manager.get_text('host_address_label'))
        self.address_label.grid(row=2, column=2, sticky='e', **padding)
        self.address_entry = ttk.Entry(self, width=20)
        self.address_entry.grid(row=2, column=3, sticky='w', **padding)

        # Action buttons
        self.add_btn = ttk.Button(self, text=language_manager.get_text('add_host_btn'), command=self._add_host)
        self.add_btn.grid(row=3, column=0, sticky='ew', **padding)

        self.remove_btn = ttk.Button(self, text=language_manager.get_text('remove_host_btn'), command=self._remove_selected)
        self.remove_btn.grid(row=3, column=1, sticky='ew', **padding)

        self.reset_btn = ttk.Button(self, text=language_manager.get_text('reset_hosts_btn'), command=self._reset_defaults)
        self.reset_btn.grid(row=3, column=2, sticky='ew', **padding)

        self.close_btn = ttk.Button(self, text=language_manager.get_text('close_window_btn'), command=self._on_close)
        self.close_btn.grid(row=3, column=3, sticky='ew', **padding)

    def _populate_hosts(self):
        self.host_listbox.delete(0, tk.END)
        for name, addr in self.network_checker.test_hosts:
            self.host_listbox.insert(tk.END, f"{name} ({addr})")

    # Actions
    def _add_host(self):
        name = self.name_entry.get().strip()
        addr = self.address_entry.get().strip()
        if not name or not addr:
            messagebox.showwarning(
                language_manager.get_text('host_add_warning_title'),
                language_manager.get_text('host_add_warning_msg')
            )
            return
        self.network_checker.add_host(name, addr)
        self.name_entry.delete(0, tk.END)
        self.address_entry.delete(0, tk.END)
        self._populate_hosts()

    def _remove_selected(self):
        selection = list(self.host_listbox.curselection())
        if not selection:
            messagebox.showwarning(
                language_manager.get_text('host_remove_warning_title'),
                language_manager.get_text('host_remove_warning_msg')
            )
            return
        # Remove from highest index to lowest
        for idx in sorted(selection, reverse=True):
            # test_hosts ile listbox aynı sırada
            self.network_checker.remove_host(idx)
        self._populate_hosts()

    def _reset_defaults(self):
        self.network_checker.reset_to_defaults()
        self._populate_hosts()
        messagebox.showinfo(
            language_manager.get_text('hosts_reset_info_title'),
            language_manager.get_text('hosts_reset_info_msg')
        )

    def update_texts(self):
        """Dil değişince metinleri güncelle."""
        self.title(language_manager.get_text('network_settings_title'))
        self.host_list_label.config(text=language_manager.get_text('host_list_label'))
        self.name_label.config(text=language_manager.get_text('host_name_label'))
        self.address_label.config(text=language_manager.get_text('host_address_label'))
        self.add_btn.config(text=language_manager.get_text('add_host_btn'))
        self.remove_btn.config(text=language_manager.get_text('remove_host_btn'))
        self.reset_btn.config(text=language_manager.get_text('reset_hosts_btn'))
        self.close_btn.config(text=language_manager.get_text('close_window_btn'))
        # Listeyi yeniden doldur (metin formatı aynı ama yeniden çizim iyi olabilir)
        self._populate_hosts()

    def _on_close(self):
        self.destroy()

