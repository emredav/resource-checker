"""
System Information Window for ResourceChecker application.
Displays detailed hardware specifications.
"""

import threading
import tkinter as tk
from tkinter import ttk, messagebox
from core.language import language_manager
from core.system_info import SystemInfo

class SystemSpecsWindow(tk.Toplevel):
    """Window to display detailed system specifications."""

    def __init__(self, master):
        super().__init__(master)
        self.title(language_manager.get_text('system_specs_title'))
        self.geometry("700x700")
        
        self.specs = SystemInfo.get_detailed_specs()
        self.public_ip_var = tk.StringVar(value="*****") # Default masked
        
        self.canvas = None
        self.main_frame = None
        self.text_content_data = {}
        
        self.setup_ui()
        self.start_public_ip_fetch()

    def setup_ui(self):
        """Setup user interface with scrollable area."""
        # Scrollable container
        self.canvas = tk.Canvas(self)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = ttk.Frame(self.canvas)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Mousewheel scrolling
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)

        self._populate_content()

    def _on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")

    def _populate_content(self):
        main_frame = self.scrollable_frame
        
        # Padding wrapper
        pad_frame = ttk.Frame(main_frame, padding="20")
        pad_frame.pack(fill="both", expand=True)

        # Style
        style = ttk.Style()
        style.configure("SpecLabel.TLabel", font=("Helvetica", 10, "bold"))
        style.configure("SpecValue.TLabel", font=("Helvetica", 10))
        style.configure("Header.TLabel", font=("Helvetica", 11, "bold", "underline"))

        row_idx = 0

        # --- Section: Basic Info ---
        basic_rows = [
            ('lbl_os', 'os'),
            ('lbl_processor', 'cpu'),
            ('lbl_ram', 'ram'),
            ('lbl_mobo', 'mobo'),
            ('lbl_gpu', 'gpu'),
            ('lbl_bios', 'bios'),
            ('lbl_uptime', 'uptime'),
        ]

        for label_key, data_key in basic_rows:
            self._add_row(pad_frame, row_idx, label_key, self.specs.get(data_key, "Unknown"))
            row_idx += 1
        
        # --- Section: RAM Details ---
        self._add_separator(pad_frame, row_idx)
        row_idx += 1
        self._add_header(pad_frame, row_idx, 'lbl_ram_detail')
        row_idx += 1
        
        ram_details = self.specs.get('ram_detail', [])
        if not ram_details:
            self._add_row(pad_frame, row_idx, 'lbl_ram_detail', "N/A", header_mode=False)
            row_idx += 1
        else:
            for rd in ram_details:
                # Use a bullet point style
                self._add_list_item(pad_frame, row_idx, rd)
                row_idx += 1
        # Store for copy
        self.text_content_data[language_manager.get_text('lbl_ram_detail')] = "; ".join(ram_details)

        # --- Section: Disk Details ---
        self._add_separator(pad_frame, row_idx)
        row_idx += 1
        self._add_header(pad_frame, row_idx, 'lbl_disk_detail')
        row_idx += 1
        
        # Physical
        disk_details = self.specs.get('disk_detail', [])
        if disk_details:
            for dd in disk_details:
                self._add_list_item(pad_frame, row_idx, f"Phys: {dd}")
                row_idx += 1
        # Logical
        disk_parts = self.specs.get('disk', []) # Logical partitions
        if disk_parts:
            for dp in disk_parts:
                self._add_list_item(pad_frame, row_idx, f"Vol: {dp}")
                row_idx += 1
        
        self.text_content_data[language_manager.get_text('lbl_disk_detail')] = str(disk_details + disk_parts)

        # --- Section: Network Adapters ---
        self._add_separator(pad_frame, row_idx)
        row_idx += 1
        self._add_header(pad_frame, row_idx, 'lbl_adapters')
        row_idx += 1
        
        adapters = self.specs.get('adapters', [])
        # adapters is now a list of tuples (name, ip)
        if adapters:
            for name, ip in adapters:
                self._create_masked_row_manual(pad_frame, row_idx, name, ip)
                row_idx += 1
            
            # Store for copy (formatted string)
            copy_str = "\n".join([f"{n}: {i}" for n, i in adapters])
            self.text_content_data[language_manager.get_text('lbl_adapters')] = copy_str
        else:
             self._add_list_item(pad_frame, row_idx, "No adapters found")
             row_idx += 1

        # --- Section: IP / MAC ---
        self._add_separator(pad_frame, row_idx)
        row_idx += 1
        
        # Masked IP (Local)
        self._create_masked_row(pad_frame, row_idx, 'lbl_ip', self.specs.get('ip', 'Unknown'))
        row_idx += 1
        
        # Masked IP (Public) - Special handling
        self.public_ip_label_row = row_idx
        self._create_masked_row_dynamic(pad_frame, row_idx, 'lbl_public_ip', self.public_ip_var)
        row_idx += 1
        
        # Masked MAC
        self._create_masked_row(pad_frame, row_idx, 'lbl_mac', self.specs.get('mac', 'Unknown'))
        row_idx += 1

        # Copy Button
        copy_btn = ttk.Button(pad_frame, text=language_manager.get_text('btn_copy_clipboard'), command=self.copy_to_clipboard)
        copy_btn.grid(row=row_idx, column=0, columnspan=2, pady=(20, 0))

    def _add_row(self, parent, row, label_key, value, header_mode=True):
        label_text = language_manager.get_text(label_key) if header_mode else label_key
        lbl = ttk.Label(parent, text=label_text, style="SpecLabel.TLabel")
        lbl.grid(row=row, column=0, sticky="nw", pady=(0, 5))
        
        val_lbl = ttk.Label(parent, text=value, style="SpecValue.TLabel", wraplength=400)
        val_lbl.grid(row=row, column=1, sticky="w", padx=(10, 0), pady=(0, 5))
        
        if header_mode:
            self.text_content_data[label_text] = value

    def _add_header(self, parent, row, label_key):
        lbl = ttk.Label(parent, text=language_manager.get_text(label_key), style="Header.TLabel")
        lbl.grid(row=row, column=0, columnspan=2, sticky="w", pady=(10, 5))

    def _add_list_item(self, parent, row, text):
        lbl = ttk.Label(parent, text="• " + text, style="SpecValue.TLabel", wraplength=550)
        lbl.grid(row=row, column=0, columnspan=2, sticky="w", padx=(20, 0))

    def _add_separator(self, parent, row):
        ttk.Separator(parent, orient='horizontal').grid(row=row, column=0, columnspan=2, sticky='ew', pady=10)

    def _create_masked_row(self, parent, row, label_key, value):
        label_text = language_manager.get_text(label_key)
        self._create_masked_row_manual(parent, row, label_text, value)

    def _create_masked_row_manual(self, parent, row, label_text, value):
        lbl = ttk.Label(parent, text=label_text + ":", style="SpecLabel.TLabel")
        lbl.grid(row=row, column=0, sticky="w", pady=(0, 5))

        # Update copy data map
        # Note: If duplicate keys (e.g. multiple adapters generally have unique names but hypothetically), this might overwrite.
        # But for display it's fine. For copy, we handled 'adapters' block separately above.
        # But individual IPs might be desired? The block above handles the full list copy.
        # So we don't strictly need to add to text_content_data here if we handled the block.
        # But let's add it for safety if logic changes.
        # Actually, let's NOT add to text_content_data here to avoid cluttering the copy list with individual rows if we already added the block string.
        
        val_frame = ttk.Frame(parent)
        val_frame.grid(row=row, column=1, sticky="w", padx=(10, 0))

        display_var = tk.StringVar(value="*****")
        val_lbl = ttk.Label(val_frame, textvariable=display_var, style="SpecValue.TLabel")
        val_lbl.pack(side=tk.LEFT)

        def toggle_view():
            if display_var.get() == "*****":
                display_var.set(value)
            else:
                display_var.set("*****")

        btn = ttk.Button(val_frame, text="👁️‍🗨️", width=3, command=toggle_view)
        btn.pack(side=tk.LEFT, padx=(10, 0))

    def _create_masked_row_dynamic(self, parent, row, label_key, var):
        """Maked row where the real value is in a StringVar that updates later."""
        label_text = language_manager.get_text(label_key)
        lbl = ttk.Label(parent, text=label_text, style="SpecLabel.TLabel")
        lbl.grid(row=row, column=0, sticky="w", pady=(0, 5))

        val_frame = ttk.Frame(parent)
        val_frame.grid(row=row, column=1, sticky="w", padx=(10, 0))

        # We will use 'var' as the source of truth, but display a separate masked var
        # Actually easier: The var passed IS the masked one? No, var is the REAL value holder.
        
        self.public_ip_real_val = language_manager.get_text('loading') # Initial
        
        display_var = tk.StringVar(value="*****")
        val_lbl = ttk.Label(val_frame, textvariable=display_var, style="SpecValue.TLabel")
        val_lbl.pack(side=tk.LEFT)

        def toggle_view():
            current = display_var.get()
            if current == "*****":
                display_var.set(self.public_ip_real_val)
            else:
                display_var.set("*****")

        def on_real_val_change(*args):
             self.public_ip_real_val = var.get()
             # If currently showing real value, update it
             if display_var.get() != "*****":
                 display_var.set(self.public_ip_real_val)

        var.trace_add("write", on_real_val_change)

        btn = ttk.Button(val_frame, text="👁️‍🗨️", width=3, command=toggle_view)
        btn.pack(side=tk.LEFT, padx=(10, 0))
        
        # Register for copy (will copy loading initially, but updated later if we refetch)
        # Note: copy logic just grabs self.text_content_data. We need to update that map too.
        # This is a bit hacky for the copy map.
        self.public_ip_key = label_text

    def start_public_ip_fetch(self):
        def fetch():
            ip = SystemInfo.get_public_ip()
            self.public_ip_var.set(ip)
            if hasattr(self, 'public_ip_key'):
                 self.text_content_data[self.public_ip_key] = ip
        threading.Thread(target=fetch, daemon=True).start()

    def copy_to_clipboard(self):
        lines = []
        # Update dynamic values in map just in case
        if hasattr(self, 'public_ip_key'):
             self.text_content_data[self.public_ip_key] = self.public_ip_var.get()

        for k, v in self.text_content_data.items():
            lines.append(f"{k} {v}")
        
        text = "\n".join(lines)
        self.clipboard_clear()
        self.clipboard_append(text)
        messagebox.showinfo(
            language_manager.get_text('msg_copy_title'),
            language_manager.get_text('msg_copied')
        )
