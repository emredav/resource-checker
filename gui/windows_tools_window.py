"""
Windows Tools & Utilities Window.
Provides shortcuts to system tools and a command console.
"""

import tkinter as tk
from tkinter import ttk, scrolledtext
import threading
from core.language import language_manager
from core.windows_utils import WindowsUtils

from gui.path_editor_window import PathEditorWindow
from tkinter import messagebox

class WindowsToolsWindow(tk.Toplevel):
    def __init__(self, master):
        super().__init__(master)
        self.title(language_manager.get_text('win_tools_title'))
        self.geometry("800x650") # Increased size
        
        self.setup_ui()
        self.path_editor = None

    def setup_ui(self):
        # Notebook for Tabs
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self._setup_shortcuts_tab()
        self._setup_console_tab()

    def _setup_shortcuts_tab(self):
        tab = ttk.Frame(self.notebook, padding=20)
        self.notebook.add(tab, text=language_manager.get_text('tab_shortcuts'))

        # --- Advanced Tools Section ---
        adv_frame = ttk.LabelFrame(tab, text="Advanced Utilities", padding=10)
        adv_frame.pack(fill=tk.X, pady=(0, 20))
        
        # Temp Cleaner
        ttk.Button(adv_frame, text=language_manager.get_text('btn_temp_clean'), command=self.run_temp_clean).pack(side=tk.LEFT, padx=10)
        
        # Path Editor
        ttk.Button(adv_frame, text=language_manager.get_text('btn_path_editor'), command=self.open_path_editor).pack(side=tk.LEFT, padx=10)

        # --- Shortcuts Grid ---
        grid_frame = ttk.LabelFrame(tab, text="System Shortcuts", padding=10)
        grid_frame.pack(fill=tk.BOTH, expand=True)

        tools = [
            # Original
            ('tool_task_mgr', 'task_mgr'),
            ('tool_dev_mgmt', 'dev_mgmt'),
            ('tool_disk_mgmt', 'disk_mgmt'),
            ('tool_services', 'services'),
            ('tool_event_vwr', 'event_vwr'),
            ('tool_dxdiag', 'dxdiag'),
            # New
            ('tool_renew_ip_p', 'cmd_renew_ip_p'),
            ('tool_sys_prop', 'sys_prop'),
            ('tool_regedit', 'regedit'),
            ('tool_control', 'control'),
            ('tool_add_remove', 'add_remove'),
            ('tool_firewall', 'firewall'),
            ('tool_hosts', 'hosts_file'),
            ('tool_msinfo', 'msinfo'),
            ('tool_cmd', 'cmd'),
            ('tool_powershell', 'powershell')
        ]

        row = 0
        col = 0
        cols_per_row = 3
        
        for label_key, tool_key in tools:
            btn = ttk.Button(
                grid_frame, 
                text=language_manager.get_text(label_key),
                command=lambda k=tool_key: WindowsUtils.launch_tool(k),
                width=30
            )
            btn.grid(row=row, column=col, padx=10, pady=5)
            
            col += 1
            if col >= cols_per_row:
                col = 0
                row += 1

    def run_temp_clean(self):
        if messagebox.askyesno("Confirm", language_manager.get_text('msg_confirm_clean')):
            result = WindowsUtils.clean_temp_files()
            messagebox.showinfo("Result", result + "\n\n" + language_manager.get_text('msg_clean_complete'))

    def open_path_editor(self):
        if self.path_editor is None or not self.path_editor.winfo_exists():
            self.path_editor = PathEditorWindow(self)
        else:
            self.path_editor.lift()

    def _setup_console_tab(self):
        tab = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(tab, text=language_manager.get_text('tab_console'))
        
        # --- Top: Category Selection ---
        top_frame = ttk.Frame(tab)
        top_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(top_frame, text="Category:").pack(side=tk.LEFT, padx=(0, 5))
        
        from core.command_library import COMMAND_CATEGORIES
        self.categories = list(COMMAND_CATEGORIES.keys())
        
        self.cat_var = tk.StringVar()
        self.cat_combo = ttk.Combobox(top_frame, textvariable=self.cat_var, values=self.categories, state="readonly", width=30)
        self.cat_combo.pack(side=tk.LEFT, padx=5)
        if self.categories:
            self.cat_combo.current(0)
        self.cat_combo.bind("<<ComboboxSelected>>", self._on_category_change)
        
        # --- Middle: Command List (Treeview) ---
        tree_frame = ttk.Frame(tab)
        tree_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        cols = ('name', 'cmd', 'desc')
        self.cmd_tree = ttk.Treeview(tree_frame, columns=cols, show='headings', height=8)
        
        self.cmd_tree.heading('name', text="Command Name")
        self.cmd_tree.heading('cmd', text="Command")
        self.cmd_tree.heading('desc', text="Description")
        
        self.cmd_tree.column('name', width=180)
        self.cmd_tree.column('cmd', width=220)
        self.cmd_tree.column('desc', width=350)
        
        sb = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.cmd_tree.yview)
        self.cmd_tree.configure(yscroll=sb.set)
        
        self.cmd_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Bind double click to run
        self.cmd_tree.bind("<Double-1>", lambda e: self._run_selected_command())

        # --- Bottom: Controls ---
        ctrl_frame = ttk.Frame(tab)
        ctrl_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.run_btn = ttk.Button(ctrl_frame, text="Run Command", command=self._run_selected_command)
        self.run_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(ctrl_frame, text="Clear Output", command=self._clear_output).pack(side=tk.LEFT)

        # --- Output Area ---
        out_frame = ttk.LabelFrame(tab, text="Console Output", padding=5)
        out_frame.pack(fill=tk.BOTH, expand=True)
        
        self.output_text = scrolledtext.ScrolledText(out_frame, state='disabled', height=10, font=("Consolas", 9))
        self.output_text.pack(fill=tk.BOTH, expand=True)
        self.output_text.config(bg="black", fg="#00FF00", insertbackground="white") # Matrix style green
        
        # Init list
        self._on_category_change(None)

    def _on_category_change(self, event):
        # Clear tree
        for item in self.cmd_tree.get_children():
            self.cmd_tree.delete(item)
            
        cat = self.cat_var.get()
        from core.command_library import COMMAND_CATEGORIES
        cmds = COMMAND_CATEGORIES.get(cat, [])
        
        current_lang = language_manager.get_current_language()
        
        for c in cmds:
            desc = c.get('desc_tr') if current_lang == 'tr' and 'desc_tr' in c else c.get('desc', '')
            self.cmd_tree.insert('', 'end', values=(c.get('name', ''), c.get('cmd', ''), desc))

    def _run_selected_command(self):
        sel = self.cmd_tree.selection()
        if not sel: return
        
        vals = self.cmd_tree.item(sel[0], 'values')
        cmd = vals[1] # Command is 2nd column
        
        self._append_output(f"\n> {cmd}\n")
        self.run_btn.config(state='disabled')
        
        # Run in thread
        threading.Thread(target=self._execute_thread, args=(cmd,), daemon=True).start()

    def _execute_thread(self, cmd):
        WindowsUtils.run_command_live(cmd, lambda line: self.after(0, self._append_output, line))
        self.after(0, lambda: self.run_btn.config(state='normal'))

    def _append_output(self, text):
        self.output_text.config(state='normal')
        self.output_text.insert(tk.END, text)
        self.output_text.see(tk.END)
        self.output_text.config(state='disabled')

    def _clear_output(self):
        self.output_text.config(state='normal')
        self.output_text.delete(1.0, tk.END)
        self.output_text.config(state='disabled')
