"""
Wi-Fi Analyzer Window.
Displays real-time and scanned Wi-Fi network information.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import threading
from core.language import language_manager
from core.wifi_analyzer import WifiAnalyzer

class WifiWindow(tk.Toplevel):
    def __init__(self, master):
        super().__init__(master)
        self.title(language_manager.get_text('wifi_title'))
        self.geometry("900x600")
        
        self.setup_ui()
        self.refresh_data()

    def setup_ui(self):
        # Notebook
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self._setup_live_tab()
        self._setup_saved_tab()

    def _setup_live_tab(self):
        tab = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(tab, text=language_manager.get_text('wifi_title')) # Default title for live view
        
        # --- Top Section: Current Connection ---
        top_frame = ttk.LabelFrame(tab, text=language_manager.get_text('wifi_current_con'), padding="10")
        top_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.current_labels = {}
        
        # Row 1
        self._add_info_label(top_frame, 0, 0, 'lbl_ssid', 'ssid_val')
        self._add_info_label(top_frame, 0, 2, 'lbl_signal', 'signal_val', color=True)
        self._add_info_label(top_frame, 0, 4, 'lbl_channel', 'channel_val')
        
        # Row 2
        self._add_info_label(top_frame, 1, 0, 'lbl_bssid', 'bssid_val')
        self._add_info_label(top_frame, 1, 2, 'lbl_radio', 'radio_val')
        self._add_info_label(top_frame, 1, 4, 'lbl_security', 'auth_val') 

        # --- Bottom Section: Scanner ---
        bottom_frame = ttk.LabelFrame(tab, text=language_manager.get_text('wifi_scan_results'), padding="10")
        bottom_frame.pack(fill=tk.BOTH, expand=True)
        
        # Controls
        ctrl_frame = ttk.Frame(bottom_frame)
        ctrl_frame.pack(fill=tk.X, pady=(0, 5))
        
        self.refresh_btn = ttk.Button(ctrl_frame, text=language_manager.get_text('btn_refresh_wifi'), command=self.refresh_data)
        self.refresh_btn.pack(side=tk.RIGHT)
        
        self.status_lbl = ttk.Label(ctrl_frame, text="")
        self.status_lbl.pack(side=tk.LEFT)

        # Treeview
        columns = ('ssid', 'signal', 'channel', 'radio', 'auth', 'bssid')
        self.tree = ttk.Treeview(bottom_frame, columns=columns, show='headings')
        
        # Headers
        headers = ['ssid', 'signal', 'channel', 'radio', 'auth', 'bssid']
        for col in headers:
            key = f'wifi_col_{col}' if col != 'auth' else 'wifi_col_auth' # Handle naming if specific
            # Using specific keys from lang file
            if col == 'auth': key = 'wifi_col_auth' 
            
            # Direct mapping check from previous file or lang file keys
            # 'wifi_col_ssid', 'wifi_col_signal'...
            self.tree.heading(col, text=language_manager.get_text(f'wifi_col_{col}'))
            
        # Column width adjustments
        self.tree.column('ssid', width=180)
        self.tree.column('signal', width=60)
        self.tree.column('channel', width=60)
        self.tree.column('radio', width=80)
        self.tree.column('auth', width=120)
        self.tree.column('bssid', width=120)
        
        scrollbar = ttk.Scrollbar(bottom_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def _setup_saved_tab(self):
        tab = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(tab, text=language_manager.get_text('tab_saved_wifi'))
        
        # Controls
        ctrl_frame = ttk.Frame(tab)
        ctrl_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Button(ctrl_frame, text=language_manager.get_text('btn_load_saved'), command=self.load_saved_profiles).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(ctrl_frame, text=language_manager.get_text('btn_show_pass'), command=self.show_selected_password).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(ctrl_frame, text=language_manager.get_text('btn_delete_profile'), command=self.delete_selected_profile).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(ctrl_frame, text=language_manager.get_text('btn_export_pass'), command=self.export_passwords).pack(side=tk.RIGHT)

        self.saved_status = ttk.Label(ctrl_frame, text="")
        self.saved_status.pack(side=tk.LEFT, padx=10)

        # Saved Networks Tree
        # Cols: SSID, Security, Password, Connection Mode
        columns = ('ssid', 'auth', 'password', 'mode')
        self.saved_tree = ttk.Treeview(tab, columns=columns, show='headings')
        
        self.saved_tree.heading('ssid', text="SSID")
        self.saved_tree.heading('auth', text=language_manager.get_text('wifi_col_auth'))
        self.saved_tree.heading('password', text=language_manager.get_text('col_password'))
        self.saved_tree.heading('mode', text=language_manager.get_text('col_mode'))
        
        self.saved_tree.column('ssid', width=200)
        self.saved_tree.column('auth', width=150)
        self.saved_tree.column('password', width=200)
        self.saved_tree.column('mode', width=150)
        
        sb = ttk.Scrollbar(tab, orient=tk.VERTICAL, command=self.saved_tree.yview)
        self.saved_tree.configure(yscroll=sb.set)
        
        self.saved_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb.pack(side=tk.RIGHT, fill=tk.Y)

    def _add_info_label(self, parent, row, col, label_key, val_key, color=False):
        ttk.Label(parent, text=language_manager.get_text(label_key), font=("Helvetica", 9, "bold")).grid(row=row, column=col, sticky="w", padx=(0, 10), pady=5)
        lbl = ttk.Label(parent, text="--", font=("Helvetica", 11))
        lbl.grid(row=row, column=col+1, sticky="w", padx=(0, 30), pady=5)
        self.current_labels[val_key] = lbl
        if color:
            self.current_labels[val_key + '_color'] = True

    def refresh_data(self):
        self.refresh_btn.config(state='disabled')
        self.status_lbl.config(text=language_manager.get_text('loading'))
        threading.Thread(target=self._fetch_and_update, daemon=True).start()

    def _fetch_and_update(self):
        current = WifiAnalyzer.get_current_interface_info()
        networks = WifiAnalyzer.scan_networks()
        self.after(0, self._update_ui, current, networks)

    def _update_ui(self, current, networks):
        # Update Current Section
        if current and 'ssid' in current:
            self.current_labels['ssid_val'].config(text=current.get('ssid', 'Unknown'))
            self.current_labels['bssid_val'].config(text=current.get('bssid', 'Unknown'))
            self.current_labels['channel_val'].config(text=current.get('channel', 'Unknown'))
            self.current_labels['radio_val'].config(text=current.get('radio', 'Unknown'))
            
            sig = current.get('signal', '0')
            self.current_labels['signal_val'].config(text=f"{sig}%")
            self._colorize_signal(self.current_labels['signal_val'], sig)
            self.current_labels['auth_val'].config(text=current.get('state', 'Connected'))
        else:
            self.current_labels['ssid_val'].config(text=language_manager.get_text('wifi_disconnected'))
            for k, lbl in self.current_labels.items():
                if "_color" not in k and lbl != self.current_labels['ssid_val']:
                    lbl.config(text="--")

        # Update Live Tree
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        for net in networks:
            sig = net.get('signal', '0')
            tags = ('high_sig',) if int(sig) > 70 else ('med_sig',) if int(sig) > 40 else ('low_sig',)
            self.tree.insert('', 'end', values=(
                net.get('ssid', ''), f"{sig}%", net.get('channel', ''),
                net.get('radio', ''), net.get('auth', ''), net.get('mac', '')
            ), tags=tags)
            
        self.status_lbl.config(text="")
        self.refresh_btn.config(state='normal')

    def _colorize_signal(self, label, signal_str):
        try:
            val = int(signal_str)
            label.config(foreground="green" if val >= 80 else "#D4AF37" if val >= 50 else "red")
        except:
            label.config(foreground="black")

    # --- Saved Networks Logic ---
    def load_saved_profiles(self):
        self.saved_status.config(text=language_manager.get_text('loading'))
        for item in self.saved_tree.get_children():
            self.saved_tree.delete(item)
            
        threading.Thread(target=self._fetch_saved_profiles_thread, daemon=True).start()

    def _fetch_saved_profiles_thread(self):
        # Only fetch list first
        profiles = WifiAnalyzer.get_saved_profiles()
        self.after(0, self._populate_saved_tree, profiles)

    def _populate_saved_tree(self, profiles):
        for p in profiles:
            # We don't have details yet, just list them. Passwords hidden.
            self.saved_tree.insert('', 'end', values=(p, "...", "******", "..."))
        self.saved_status.config(text=f"{len(profiles)} Profiles")

    def show_selected_password(self):
        sel = self.saved_tree.selection()
        if not sel: return
        
        item = sel[0]
        vals = self.saved_tree.item(item, 'values')
        ssid = vals[0]
        
        # Async fetch details
        def fetch():
            details = WifiAnalyzer.get_profile_details(ssid)
            self.after(0, update_row, item, details)
            
        def update_row(item_id, details):
            # Update the row with fetched details
            self.saved_tree.item(item_id, values=(
                details['ssid'],
                details.get('auth', 'Unknown'),
                details.get('password', '<No Key>'),
                details.get('connection_mode', 'Unknown')
            ))
            
        threading.Thread(target=fetch, daemon=True).start()

    def delete_selected_profile(self):
        sel = self.saved_tree.selection()
        if not sel: return
        ssid = self.saved_tree.item(sel[0], 'values')[0]
        
        if messagebox.askyesno("Delete Profile", f"Delete Wi-Fi profile '{ssid}'?"):
            if WifiAnalyzer.delete_profile(ssid):
                self.saved_tree.delete(sel[0])
                messagebox.showinfo("Success", "Profile deleted.")
            else:
                messagebox.showerror("Error", "Failed to delete profile (Admin rights?)")

    def export_passwords(self):
        # Fetch all passwords and save to file
        if not messagebox.askyesno("Export", "This will fetch all saved passwords. It may take some time. Continue?"):
            return
            
        def run_export():
            profiles = WifiAnalyzer.get_saved_profiles()
            lines = []
            for p in profiles:
                d = WifiAnalyzer.get_profile_details(p)
                line = f"SSID: {d['ssid']} | Pass: {d.get('password', 'N/A')} | Auth: {d.get('auth', 'N/A')}"
                lines.append(line)
            
            try:
                with open("wifi_passwords_export.txt", "w", encoding='utf-8') as f:
                    f.write("\n".join(lines))
                self.after(0, lambda: messagebox.showinfo("Export", "Saved to wifi_passwords_export.txt"))
            except Exception as e:
                self.after(0, lambda: messagebox.showerror("Export Error", str(e)))

        threading.Thread(target=run_export, daemon=True).start()
