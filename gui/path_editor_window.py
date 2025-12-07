"""
Environment Path Variable Editor.
Author: ResourceChecker
"""

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from core.language import language_manager
from core.windows_utils import WindowsUtils

class PathEditorWindow(tk.Toplevel):
    def __init__(self, master):
        super().__init__(master)
        self.title("Environment Path Editor")
        self.geometry("600x500")
        
        self.scope_var = tk.StringVar(value='user')
        self.current_paths = []
        
        self.setup_ui()
        self.load_paths()

    def setup_ui(self):
        # Scope Selection
        top_frame = ttk.Frame(self, padding="10")
        top_frame.pack(fill=tk.X)
        
        ttk.Label(top_frame, text="Scope:").pack(side=tk.LEFT)
        ttk.Radiobutton(top_frame, text="User (Current User)", variable=self.scope_var, value='user', command=self.load_paths).pack(side=tk.LEFT, padx=10)
        ttk.Radiobutton(top_frame, text="System (All Users - Requires Admin)", variable=self.scope_var, value='system', command=self.load_paths).pack(side=tk.LEFT)

        # List
        list_frame = ttk.Frame(self, padding="10")
        list_frame.pack(fill=tk.BOTH, expand=True)
        
        self.listbox = tk.Listbox(list_frame, selectmode=tk.SINGLE)
        self.listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.listbox.config(yscrollcommand=scrollbar.set)

        # Buttons
        btn_frame = ttk.Frame(self, padding="10")
        btn_frame.pack(fill=tk.X)
        
        ttk.Button(btn_frame, text="Add New", command=self.add_path).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Edit", command=self.edit_path).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Delete", command=self.delete_path).pack(side=tk.LEFT, padx=5)
        
        ttk.Separator(btn_frame, orient=tk.VERTICAL).pack(side=tk.LEFT, padx=10, fill=tk.Y)
        
        ttk.Button(btn_frame, text="Save Changes", command=self.save_changes).pack(side=tk.RIGHT, padx=5)

    def load_paths(self):
        scope = self.scope_var.get()
        self.current_paths = WindowsUtils.get_path_variable(scope)
        self.listbox.delete(0, tk.END)
        for p in self.current_paths:
            self.listbox.insert(tk.END, p)
            
    def add_path(self):
        new_path = simpledialog.askstring("Add Path", "Enter new path:")
        if new_path:
            self.current_paths.append(new_path)
            self.listbox.insert(tk.END, new_path)

    def edit_path(self):
        sel = self.listbox.curselection()
        if not sel: return
        idx = sel[0]
        old_val = self.current_paths[idx]
        
        new_val = simpledialog.askstring("Edit Path", "Edit path:", initialvalue=old_val)
        if new_val:
            self.current_paths[idx] = new_val
            self.listbox.delete(idx)
            self.listbox.insert(idx, new_val)

    def delete_path(self):
        sel = self.listbox.curselection()
        if not sel: return
        if messagebox.askyesno("Delete", "Remove this path?"):
            idx = sel[0]
            del self.current_paths[idx]
            self.listbox.delete(idx)

    def save_changes(self):
        scope = self.scope_var.get()
        if scope == 'system':
            if not messagebox.askyesno("Admin Warning", "Writing to System PATH requires Administrator privileges.\nIf this app is not running as Admin, this will fail.\nProceed?"):
                return
        
        success = WindowsUtils.set_path_variable(scope, self.current_paths)
        if success:
            messagebox.showinfo("Success", "PATH updated successfully.\nYou may need to restart apps to see changes.")
        else:
            messagebox.showerror("Error", "Failed to write to Registry.\nEnsure you are running as Administrator.")
