"""
Main System Monitor GUI for ResourceChecker application.
"""

import time
import threading
import tkinter as tk
from tkinter import ttk, scrolledtext

from core.language import language_manager
from core.system_info import SystemInfo, ProcessMonitor
from core.network import NetworkHealthChecker, WebhookConfig, WebhookNotifier
from utils.logging import Logger, NetworkLogger, AutoLogger, FileManager
from gui.resource_monitor_window import ResourceTempMonitorWindow
from gui.stress_test_window import CPUStressTestWindow
from gui.webhook_settings_window import WebhookSettingsWindow
from gui.network_settings_window import NetworkSettingsWindow  # Added import


class SystemMonitorGUI:
    """Main GUI class for the system monitor."""

    def __init__(self, root):
        self.root = root
        self.root.title(language_manager.get_text('main_title'))
        self.root.geometry("1400x850")

        # Main components
        self.monitoring = False
        self.network_monitoring = False
        self.system_interval = 60
        self.network_interval = 300
        self.top_apps_count = 3
        self.temp_monitor_window = None
        self.stress_test_window = None
        self.webhook_settings_window = None
        self.network_settings_window = None  # Added attribute

        # Class instances
        self.process_monitor = ProcessMonitor(self.top_apps_count)
        self.network_health_checker = NetworkHealthChecker()
        self.webhook_config = WebhookConfig()

        # GUI setup
        self.setup_gui()

        # Create loggers (after GUI setup)
        # Ensure logs directory exists
        FileManager.ensure_directory_exists("logs")
        
        self.logger = Logger(self.log_text)
        self.network_logger = NetworkLogger(self.network_log_text)
        self.auto_logger = AutoLogger(self.log_text, self.network_log_text)
        self.webhook_notifier = WebhookNotifier(self.webhook_config)
        self._last_network_check_ts = 0.0

    def setup_gui(self):
        """Setup main GUI interface."""
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        self._setup_settings_frame(main_frame)
        self._setup_control_buttons(main_frame)
        self._setup_info_frame(main_frame)
        self._setup_processes_frame(main_frame)
        self._setup_log_frames(main_frame)
        self._configure_grid_weights(main_frame)

    def _setup_settings_frame(self, parent):
        """Setup settings frame."""
        self.settings_frame = ttk.LabelFrame(parent, text=language_manager.get_text('settings_frame'), padding="10")
        self.settings_frame.grid(row=0, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))

        # System and Network intervals
        self.system_interval_label = ttk.Label(self.settings_frame, text=language_manager.get_text('system_interval'))
        self.system_interval_label.grid(row=0, column=0, sticky=tk.W)
        self.system_interval_var = tk.StringVar(value="60")
        ttk.Entry(self.settings_frame, textvariable=self.system_interval_var, width=10).grid(row=0, column=1, padx=(5, 20))

        self.network_interval_label = ttk.Label(self.settings_frame, text=language_manager.get_text('network_interval'))
        self.network_interval_label.grid(row=0, column=2, sticky=tk.W)
        self.network_interval_var = tk.StringVar(value="300")
        ttk.Entry(self.settings_frame, textvariable=self.network_interval_var, width=10).grid(row=0, column=3, padx=(5, 5))

        # Top apps count
        self.top_apps_label = ttk.Label(self.settings_frame, text=language_manager.get_text('top_apps_count'))
        self.top_apps_label.grid(row=1, column=0, sticky=tk.W, pady=(10, 0))
        self.top_apps_var = tk.StringVar(value="3")
        top_apps_combo = ttk.Combobox(self.settings_frame, textvariable=self.top_apps_var, values=["3", "4", "5", "6"], width=5, state="readonly")
        top_apps_combo.grid(row=1, column=1, padx=(5, 20), sticky=tk.W, pady=(10, 0))
        top_apps_combo.bind("<<ComboboxSelected>>", self._on_top_apps_changed)

        # Auto log checkbox
        self.auto_log_var = tk.BooleanVar()
        self.auto_log_checkbox = ttk.Checkbutton(self.settings_frame, text=language_manager.get_text('auto_log'), variable=self.auto_log_var, command=self.toggle_auto_log)
        self.auto_log_checkbox.grid(row=1, column=2, sticky=tk.W, pady=(10, 0))

        # Network settings button
        self.network_settings_btn = ttk.Button(self.settings_frame, text="⚙", command=self.open_network_settings, width=3)
        self.network_settings_btn.grid(row=0, column=4, padx=(5, 20), sticky=tk.W)

        # Language selection
        self.language_label = ttk.Label(self.settings_frame, text="Dil / Language:")
        self.language_label.grid(row=1, column=3, sticky=tk.W, pady=(10, 0), padx=(10, 5))
        
        current_lang = language_manager.get_current_language()
        button_text = language_manager.get_text('language_english') if current_lang == 'en' else language_manager.get_text('language_turkish')
        
        self.language_button = ttk.Button(
            self.settings_frame, 
            text=button_text,
            command=self._toggle_language,
            width=10
        )
        self.language_button.grid(row=1, column=4, sticky=tk.W, pady=(10, 0))

        # Webhook settings button
        self.webhook_button = ttk.Button(self.settings_frame, text=language_manager.get_text('webhook_settings'), command=self.open_webhook_settings)
        self.webhook_button.grid(row=2, column=0, pady=(10, 0), sticky=tk.W)

    def _setup_control_buttons(self, parent):
        """Setup control buttons."""
        button_frame = ttk.Frame(parent)
        button_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))

        self.start_btn = ttk.Button(button_frame, text=language_manager.get_text('start_monitoring'), command=self.start_monitoring)
        self.start_btn.pack(side=tk.LEFT, padx=(0, 5))

        self.stop_btn = ttk.Button(button_frame, text=language_manager.get_text('stop_monitoring'), command=self.stop_monitoring, state='disabled')
        self.stop_btn.pack(side=tk.LEFT, padx=(0, 10))

        self.health_btn = ttk.Button(button_frame, text=language_manager.get_text('network_health_check'), command=self.network_health_check)
        self.health_btn.pack(side=tk.LEFT, padx=(0, 10))

        self.network_auto_btn = ttk.Button(button_frame, text=language_manager.get_text('auto_network_monitoring'), command=self.toggle_network_monitoring)
        self.network_auto_btn.pack(side=tk.LEFT, padx=(0, 10))

        self.temp_monitor_btn = ttk.Button(button_frame, text=language_manager.get_text('resource_temp_monitor'), command=self.open_resource_temp_monitor)
        self.temp_monitor_btn.pack(side=tk.LEFT, padx=(10, 0))

        self.stress_test_btn = ttk.Button(button_frame, text=language_manager.get_text('cpu_stress_test'), command=self.open_cpu_stress_test)
        self.stress_test_btn.pack(side=tk.LEFT, padx=(10, 0))

    def _setup_info_frame(self, parent):
        """Setup system information frame."""
        self.info_frame = ttk.LabelFrame(parent, text=language_manager.get_text('system_info_frame'), padding="10")
        self.info_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))

        self.cpu_label = ttk.Label(self.info_frame, text=language_manager.get_text('cpu_usage'))
        self.cpu_label.grid(row=0, column=0, sticky=tk.W)

        self.memory_label = ttk.Label(self.info_frame, text=language_manager.get_text('ram_usage'))
        self.memory_label.grid(row=1, column=0, sticky=tk.W)

        self.network_label = ttk.Label(self.info_frame, text=language_manager.get_text('network_status'))
        self.network_label.grid(row=2, column=0, sticky=tk.W)

    def _setup_processes_frame(self, parent):
        """Setup process tables."""
        processes_container = ttk.Frame(parent)
        processes_container.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))

        self.cpu_processes_frame = ttk.LabelFrame(processes_container, text=language_manager.get_text('top_cpu_apps'), padding="10")
        self.cpu_processes_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 5))

        cpu_columns = ('Application', 'CPU %', 'RAM MB')
        self.cpu_tree = ttk.Treeview(self.cpu_processes_frame, columns=cpu_columns, show='headings', height=6)
        for col in cpu_columns:
            self.cpu_tree.heading(col, text=col)
            self.cpu_tree.column(col, width=120, anchor='center')
        self.cpu_tree.grid(row=0, column=0, sticky=(tk.W, tk.E))

        self.network_processes_frame = ttk.LabelFrame(processes_container, text=language_manager.get_text('top_network_apps'), padding="10")
        self.network_processes_frame.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(5, 0))

        network_columns = ('Application', 'Upload KB/s', 'Download KB/s', 'Total KB/s', 'Connection')
        self.network_tree = ttk.Treeview(self.network_processes_frame, columns=network_columns, show='headings', height=6)
        for col in network_columns:
            self.network_tree.heading(col, text=col)
            self.network_tree.column(col, width=100, anchor='center')
        self.network_tree.grid(row=0, column=0, sticky=(tk.W, tk.E))

    def _setup_log_frames(self, parent):
        """Setup log areas."""
        log_container = ttk.Frame(parent)
        log_container.grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))

        self.system_log_frame = ttk.LabelFrame(log_container, text=language_manager.get_text('system_logs'), padding="10")
        self.system_log_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 5))
        
        system_log_buttons = ttk.Frame(self.system_log_frame)
        system_log_buttons.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 5))
        self.clear_system_btn = ttk.Button(system_log_buttons, text=language_manager.get_text('clear_system_logs'), command=self.clear_system_logs)
        self.clear_system_btn.pack(side=tk.LEFT, padx=(0, 5))
        self.export_system_btn = ttk.Button(system_log_buttons, text=language_manager.get_text('export_system_logs'), command=self.export_system_logs)
        self.export_system_btn.pack(side=tk.LEFT)
        
        self.log_text = scrolledtext.ScrolledText(self.system_log_frame, height=12, width=50)
        self.log_text.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        self.network_log_frame = ttk.LabelFrame(log_container, text=language_manager.get_text('network_logs'), padding="10")
        self.network_log_frame.grid(row=0, column=1, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(5, 0))
        
        network_log_buttons = ttk.Frame(self.network_log_frame)
        network_log_buttons.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 5))
        self.clear_network_btn = ttk.Button(network_log_buttons, text=language_manager.get_text('clear_network_logs'), command=self.clear_network_logs)
        self.clear_network_btn.pack(side=tk.LEFT, padx=(0, 5))
        self.export_network_btn = ttk.Button(network_log_buttons, text=language_manager.get_text('export_network_logs'), command=self.export_network_logs)
        self.export_network_btn.pack(side=tk.LEFT)
        
        self.network_log_text = scrolledtext.ScrolledText(self.network_log_frame, height=12, width=50)
        self.network_log_text.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Grid configuration
        log_container.columnconfigure(0, weight=1)
        log_container.columnconfigure(1, weight=1)
        log_container.rowconfigure(0, weight=1)
        self.system_log_frame.columnconfigure(0, weight=1)
        self.system_log_frame.rowconfigure(1, weight=1)
        self.network_log_frame.columnconfigure(0, weight=1)
        self.network_log_frame.rowconfigure(1, weight=1)

    def _configure_grid_weights(self, main_frame):
        """Configure grid weights."""
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(2, weight=1)
        main_frame.rowconfigure(4, weight=1)

    def _on_top_apps_changed(self, event):
        """Handle top apps count change."""
        try:
            new_count = int(self.top_apps_var.get())
            self.top_apps_count = new_count
            self.process_monitor.set_top_count(new_count)
            self.logger.log(language_manager.get_text('top_apps_updated').format(new_count))
        except ValueError:
            pass

    def start_monitoring(self):
        """Start monitoring."""
        if not self.monitoring:
            try:
                self.system_interval = int(self.system_interval_var.get())
                if self.system_interval < 5:
                    self.system_interval = 5
            except ValueError:
                self.system_interval = 60

            self.monitoring = True
            self.start_btn.config(state='disabled')
            self.stop_btn.config(state='normal')
            self.monitor_thread = threading.Thread(target=self._monitor_system_worker, daemon=True)
            self.monitor_thread.start()
            self.logger.log(language_manager.get_text('monitoring_started').format(self.system_interval))

    def stop_monitoring(self):
        """Stop monitoring."""
        self.monitoring = False
        self.start_btn.config(state='normal')
        self.stop_btn.config(state='disabled')
        self.logger.log(language_manager.get_text('monitoring_stopped'))

    def _monitor_system_worker(self):
        """System monitoring worker thread."""
        while self.monitoring:
            try:
                cpu_percent = SystemInfo.get_cpu_usage()
                memory = SystemInfo.get_memory_info()
                net_sent, net_recv, net_total = SystemInfo.get_network_usage()
                top_cpu_processes = self.process_monitor.get_top_cpu_processes()
                top_network_processes = self.process_monitor.get_top_network_processes()

                self.root.after(0, lambda: self._update_system_gui(cpu_percent, memory, net_sent, net_recv, net_total))
                self.root.after(0, lambda: self._update_process_trees(top_cpu_processes, top_network_processes))
                self.webhook_notifier.check_and_notify_cpu(cpu_percent)

                log_msg = f"CPU: {cpu_percent:.1f}%, RAM: {memory.percent:.1f}%, Network: ↑{net_sent / 1024:.1f} KB/s ↓{net_recv / 1024:.1f} KB/s"
                self.root.after(0, lambda msg=log_msg: self.logger.log(msg))
                time.sleep(self.system_interval)
            except Exception as e:
                self.root.after(0, lambda: self.logger.log(f"Error: {str(e)}", "error"))
                time.sleep(self.system_interval)

    def _update_system_gui(self, cpu_percent, memory, net_sent, net_recv, net_total):
        """Update system GUI."""
        self.cpu_label.config(text=f"CPU Usage: {cpu_percent:.1f}%")
        self.memory_label.config(text=f"RAM Usage: {memory.percent:.1f}%")
        self.network_label.config(text=f"Network: ↑{net_sent / 1024:.1f} KB/s ↓{net_recv / 1024:.1f} KB/s")

    def _update_process_trees(self, cpu_processes, network_processes):
        """Update process tables."""
        for item in self.cpu_tree.get_children():
            self.cpu_tree.delete(item)
        for proc in cpu_processes:
            self.cpu_tree.insert('', 'end', values=(proc['name'], f"{proc['cpu']:.1f}%", f"{proc['memory']:.1f} MB"))

        for item in self.network_tree.get_children():
            self.network_tree.delete(item)
        for proc in network_processes:
            upload_kb, download_kb = proc['network_score'] * 0.3, proc['network_score'] * 0.7
            self.network_tree.insert('', 'end', values=(proc['name'], f"{upload_kb:.1f}", f"{download_kb:.1f}", f"{(upload_kb + download_kb):.1f}", f"{proc['connections']} active"))

    def toggle_auto_log(self):
        """Toggle auto log functionality."""
        if self.auto_log_var.get():
            self.auto_logger.start()
            FileManager.ensure_directory_exists("logs")
            self.logger.log(language_manager.get_text('auto_logging_enabled'))
            self.network_logger.log(language_manager.get_text('auto_logging_enabled'))
        else:
            self.auto_logger.stop()
            self.logger.log(language_manager.get_text('auto_logging_disabled'))
            self.network_logger.log(language_manager.get_text('auto_logging_disabled'))

    def toggle_network_monitoring(self):
        """Toggle network monitoring on/off."""
        if not self.network_monitoring:
            try:
                self.network_interval = int(self.network_interval_var.get())
                if self.network_interval < 1: 
                    self.network_interval = 1
            except ValueError:
                self.network_interval = 300

            self.network_monitoring = True
            self.network_auto_btn.config(text=language_manager.get_text('stop_auto_network'))
            self.network_thread = threading.Thread(target=self._monitor_network_worker, daemon=True)
            self.network_thread.start()
            self.network_logger.log(language_manager.get_text('network_monitoring_started').format(self.network_interval))
        else:
            self.network_monitoring = False
            self.network_auto_btn.config(text=language_manager.get_text('auto_network_monitoring'))
            self.network_logger.log(language_manager.get_text('network_monitoring_stopped'))

    def _monitor_network_worker(self):
        """Network monitoring worker thread."""
        while self.network_monitoring:
            self._network_health_check_internal(auto_mode=True)
            time.sleep(self.network_interval)

    def network_health_check(self):
        """Manual network health check."""
        threading.Thread(target=self._network_health_check_internal, daemon=True).start()

    def _network_health_check_internal(self, auto_mode=False):
        """Internal network health check."""
        results, successful_count = self.network_health_checker.check_health()
        network_ok = successful_count > 0
        self.webhook_notifier.check_and_notify_network(network_ok)

        self.root.after(0, lambda: self.network_logger.log(language_manager.get_text('network_health_header')))
        for result in results:
            self.root.after(0, lambda r=result: self.network_logger.log(r))
        
        if successful_count == 0:
            self.root.after(0, lambda: self.network_logger.log(language_manager.get_text('network_connection_error'), "error"))
        elif successful_count == len(self.network_health_checker.test_hosts):
            self.root.after(0, lambda: self.network_logger.log(language_manager.get_text('all_connections_ok'), "success"))

    def open_resource_temp_monitor(self):
        """Open Resource & Temperature Monitor window."""
        if self.temp_monitor_window is None or not self.temp_monitor_window.winfo_exists():
            self.temp_monitor_window = ResourceTempMonitorWindow(self.root)
            self.logger.log(language_manager.get_text('resource_monitor_opened'))
        else:
            self.temp_monitor_window.lift()

    def open_cpu_stress_test(self):
        """Open CPU Stress Test window."""
        if self.stress_test_window is None or not self.stress_test_window.winfo_exists():
            self.stress_test_window = CPUStressTestWindow(self.root, self)
        else:
            self.stress_test_window.lift()

    def clear_system_logs(self):
        """Clear system logs."""
        self.logger.clear()

    def export_system_logs(self):
        """Export system logs."""
        content = self.log_text.get(1.0, 'end')
        FileManager.export_log_dialog(content, language_manager.get_text('export_system_logs'))

    def clear_network_logs(self):
        """Clear network logs."""
        self.network_logger.clear()

    def export_network_logs(self):
        """Export network logs."""
        content = self.network_log_text.get(1.0, 'end')
        FileManager.export_log_dialog(content, language_manager.get_text('export_network_logs'))

    def _toggle_language(self):
        """Language toggle function."""
        current_lang = language_manager.get_current_language()
        new_lang = 'tr' if current_lang == 'en' else 'en'
        language_manager.set_language(new_lang)
        
        # Update all UI elements
        self._update_all_texts()
        # Açık network ayar penceresi varsa güncelle
        if self.network_settings_window and self.network_settings_window.winfo_exists():
            self.network_settings_window.update_texts()

        # Log the language change
        if hasattr(self, 'logger'):
            if new_lang == 'en':
                self.logger.log("Language changed to English")
            else:
                self.logger.log("Dil Türkçe olarak değiştirildi")

    def _update_all_texts(self):
        """Update all text elements."""
        # Update window title
        self.root.title(language_manager.get_text('main_title'))
        
        # Update all UI elements with new language
        self._update_settings_frame_texts()
        self._update_control_buttons_texts()
        self._update_info_frame_texts()
        self._update_processes_frame_texts()
        self._update_log_frames_texts()

    def _update_settings_frame_texts(self):
        """Update settings frame texts."""
        self.settings_frame.config(text=language_manager.get_text('settings_frame'))
        self.system_interval_label.config(text=language_manager.get_text('system_interval'))
        self.network_interval_label.config(text=language_manager.get_text('network_interval'))
        self.top_apps_label.config(text=language_manager.get_text('top_apps_count'))
        self.auto_log_checkbox.config(text=language_manager.get_text('auto_log'))
        self.webhook_button.config(text=language_manager.get_text('webhook_settings'))
        
        # Update language button text
        current_lang = language_manager.get_current_language()
        button_text = language_manager.get_text('language_english') if current_lang == 'en' else language_manager.get_text('language_turkish')
        self.language_button.config(text=button_text)

    def _update_control_buttons_texts(self):
        """Update control buttons texts."""
        self.start_btn.config(text=language_manager.get_text('start_monitoring'))
        self.stop_btn.config(text=language_manager.get_text('stop_monitoring'))
        self.health_btn.config(text=language_manager.get_text('network_health_check'))
        
        # Network monitoring button text depends on current state
        if self.network_monitoring:
            self.network_auto_btn.config(text=language_manager.get_text('stop_auto_network'))
        else:
            self.network_auto_btn.config(text=language_manager.get_text('auto_network_monitoring'))
            
        self.temp_monitor_btn.config(text=language_manager.get_text('resource_temp_monitor'))
        self.stress_test_btn.config(text=language_manager.get_text('cpu_stress_test'))

    def _update_info_frame_texts(self):
        """Update system information frame texts."""
        self.info_frame.config(text=language_manager.get_text('system_info_frame'))
        # Don't update the dynamic values, just reset the base text if showing defaults
        if "--" in self.cpu_label.cget('text'):
            self.cpu_label.config(text=language_manager.get_text('cpu_usage'))
        if "--" in self.memory_label.cget('text'):
            self.memory_label.config(text=language_manager.get_text('ram_usage'))
        if "--" in self.network_label.cget('text'):
            self.network_label.config(text=language_manager.get_text('network_status'))

    def _update_processes_frame_texts(self):
        """Update process frame texts."""
        self.cpu_processes_frame.config(text=language_manager.get_text('top_cpu_apps'))
        self.network_processes_frame.config(text=language_manager.get_text('top_network_apps'))

    def _update_log_frames_texts(self):
        """Update log frame texts."""
        self.system_log_frame.config(text=language_manager.get_text('system_logs'))
        self.network_log_frame.config(text=language_manager.get_text('network_logs'))
        self.clear_system_btn.config(text=language_manager.get_text('clear_system_logs'))
        self.export_system_btn.config(text=language_manager.get_text('export_system_logs'))
        self.clear_network_btn.config(text=language_manager.get_text('clear_network_logs'))
        self.export_network_btn.config(text=language_manager.get_text('export_network_logs'))

    def open_network_settings(self):
        """Open network settings dialog (management window)."""
        if self.network_settings_window is None or not self.network_settings_window.winfo_exists():
            self.network_settings_window = NetworkSettingsWindow(self.root, self.network_health_checker)
        else:
            self.network_settings_window.lift()
            self.network_settings_window.focus_force()

    def open_webhook_settings(self):
        """Open (or focus) webhook settings window."""
        if self.webhook_settings_window is None or not self.webhook_settings_window.winfo_exists():
            self.webhook_settings_window = WebhookSettingsWindow(self.root, self.webhook_config, self.webhook_notifier)
        else:
            self.webhook_settings_window.lift()
            self.webhook_settings_window.focus_force()

