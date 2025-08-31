"""
Resource and Temperature Monitor Window for ResourceChecker application.

Provides real-time monitoring of CPU, GPU, and RAM usage with temperature tracking
and optional logging functionality.
"""

import os
import time
import threading
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
from typing import Optional, Tuple

from core.language import language_manager
from core.hardware import HardwareMonitor
from utils.logging import FileManager
import psutil


class ResourceTempMonitorWindow(tk.Toplevel):
    """Resource and Temperature Monitor window class."""

    def __init__(self, master):
        super().__init__(master)
        self.title(language_manager.get_text('resource_temp_title'))
        self.geometry("580x480")
        self.monitoring = False
        self.update_interval = 2  # seconds
        
        # Logging properties
        self.logging_enabled = False
        self.log_interval = 10  # Minimum 10 seconds
        self.last_log_time = 0
        self.log_file_path = None
        self.log_file_index = 0
        self.max_log_size = 500 * 1024  # 500KB

        # Min/Max value tracking
        self.cpu_temp_min = float('inf')
        self.cpu_temp_max = float('-inf')
        self.gpu_temp_min = float('inf')
        self.gpu_temp_max = float('-inf')

        self.setup_widgets()
        self.start_monitoring()

        # Handle window close event
        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def setup_widgets(self):
        """Setup window interface elements."""
        main_frame = ttk.Frame(self, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        # Setup label styles
        style = ttk.Style(self)
        style.configure("Monitor.TLabel", font=("Helvetica", 12))
        style.configure("Header.TLabel", font=("Helvetica", 14, "bold"))

        row = 0
        
        # --- Logging Controls ---
        log_frame = ttk.LabelFrame(main_frame, text=language_manager.get_text('log_settings'), padding="5")
        log_frame.grid(row=row, column=0, columnspan=4, sticky="ew", pady=(0, 10))
        
        # Log enable/disable checkbox
        self.log_enabled_var = tk.BooleanVar()
        self.log_checkbox = ttk.Checkbutton(log_frame, text=language_manager.get_text('enable_logging'), 
                                          variable=self.log_enabled_var, 
                                          command=self.toggle_logging)
        self.log_checkbox.grid(row=0, column=0, sticky="w", padx=5)
        
        # Log interval setting
        ttk.Label(log_frame, text=language_manager.get_text('log_interval')).grid(row=0, column=1, sticky="w", padx=(20, 5))
        self.log_interval_var = tk.StringVar(value="10")
        self.log_interval_entry = ttk.Entry(log_frame, textvariable=self.log_interval_var, width=5)
        self.log_interval_entry.grid(row=0, column=2, sticky="w", padx=5)
        self.log_interval_entry.bind('<FocusOut>', self.on_log_interval_change)
        
        # Log status
        self.log_status_label = ttk.Label(log_frame, text=language_manager.get_text('log_status_inactive'), foreground="red")
        self.log_status_label.grid(row=0, column=3, sticky="w", padx=(20, 5))
        
        # Open log folder button
        self.open_log_btn = ttk.Button(log_frame, text=language_manager.get_text('open_log_folder'), command=self.open_log_folder)
        self.open_log_btn.grid(row=0, column=4, sticky="w", padx=(10, 5))
        
        row += 1
        
        # --- CPU ---
        ttk.Label(main_frame, text=language_manager.get_text('cpu_header'), style="Header.TLabel").grid(row=row, column=0, columnspan=4, sticky="w",
                                                                      pady=(0, 5))
        row += 1
        self.cpu_usage_label = ttk.Label(main_frame, text=language_manager.get_text('usage'), style="Monitor.TLabel")
        self.cpu_usage_label.grid(row=row, column=0, columnspan=4, sticky="w", padx=10)
        row += 1
        self.cpu_temp_label = ttk.Label(main_frame, text=language_manager.get_text('temperature'), style="Monitor.TLabel")
        self.cpu_temp_label.grid(row=row, column=0, sticky="w", padx=10)
        self.cpu_temp_min_label = ttk.Label(main_frame, text=language_manager.get_text('min_temp'), style="Monitor.TLabel")
        self.cpu_temp_min_label.grid(row=row, column=1, sticky="w")
        self.cpu_temp_max_label = ttk.Label(main_frame, text=language_manager.get_text('max_temp'), style="Monitor.TLabel")
        self.cpu_temp_max_label.grid(row=row, column=2, sticky="w")
        row += 1

        # --- GPU ---
        ttk.Separator(main_frame, orient="horizontal").grid(row=row, column=0, columnspan=4, sticky="ew", pady=10)
        row += 1
        ttk.Label(main_frame, text=language_manager.get_text('gpu_header'), style="Header.TLabel").grid(row=row, column=0, columnspan=4, sticky="w",
                                                                      pady=(0, 5))
        row += 1
        self.gpu_usage_label = ttk.Label(main_frame, text=language_manager.get_text('usage'), style="Monitor.TLabel")
        self.gpu_usage_label.grid(row=row, column=0, columnspan=4, sticky="w", padx=10)
        row += 1
        self.gpu_temp_label = ttk.Label(main_frame, text=language_manager.get_text('temperature'), style="Monitor.TLabel")
        self.gpu_temp_label.grid(row=row, column=0, sticky="w", padx=10)
        self.gpu_temp_min_label = ttk.Label(main_frame, text=language_manager.get_text('min_temp'), style="Monitor.TLabel")
        self.gpu_temp_min_label.grid(row=row, column=1, sticky="w")
        self.gpu_temp_max_label = ttk.Label(main_frame, text=language_manager.get_text('max_temp'), style="Monitor.TLabel")
        self.gpu_temp_max_label.grid(row=row, column=2, sticky="w")
        row += 1

        # --- RAM ---
        ttk.Separator(main_frame, orient="horizontal").grid(row=row, column=0, columnspan=4, sticky="ew", pady=10)
        row += 1
        ttk.Label(main_frame, text=language_manager.get_text('ram_header'), style="Header.TLabel").grid(row=row, column=0, columnspan=4, sticky="w",
                                                                      pady=(0, 5))
        row += 1
        self.ram_usage_label = ttk.Label(main_frame, text=language_manager.get_text('usage_percent'), style="Monitor.TLabel")
        self.ram_usage_label.grid(row=row, column=0, columnspan=4, sticky="w", padx=10)
        row += 1
        self.ram_usage_mb_label = ttk.Label(main_frame, text=language_manager.get_text('usage_mb'), style="Monitor.TLabel")
        self.ram_usage_mb_label.grid(row=row, column=0, columnspan=4, sticky="w", padx=10)
        row += 1

    def start_monitoring(self):
        """Start monitoring in a separate thread."""
        if not self.monitoring:
            self.monitoring = True
            self.monitor_thread = threading.Thread(target=self._update_worker, daemon=True)
            self.monitor_thread.start()
    
    def toggle_logging(self):
        """Toggle log recording on/off."""
        self.logging_enabled = self.log_enabled_var.get()
        
        if self.logging_enabled:
            # Setup log file
            self._setup_log_file()
            self.log_status_label.config(text=language_manager.get_text('log_status_active'), foreground="green")
            self._write_log("=== Resource & Temperature Monitoring Log Started ===\n")
        else:
            self.log_status_label.config(text=language_manager.get_text('log_status_inactive'), foreground="red")
            if self.log_file_path:
                self._write_log("=== Resource & Temperature Monitoring Log Stopped ===\n")
    
    def on_log_interval_change(self, event=None):
        """Handle log interval change."""
        try:
            interval = int(self.log_interval_var.get())
            if interval < 10:
                interval = 10
                self.log_interval_var.set("10")
            self.log_interval = interval
        except ValueError:
            self.log_interval_var.set(str(self.log_interval))
    
    def _setup_log_file(self):
        """Setup log file."""
        try:
            FileManager.ensure_directory_exists("logs")
            
            # Find existing files and select highest index
            base_name = "logs/resource_temp_log"
            existing_indices = []
            try:
                for fname in os.listdir("logs"):
                    if fname.startswith("resource_temp_log_") and fname.endswith(".txt"):
                        try:
                            idx_part = fname[len("resource_temp_log_"):-4]
                            existing_indices.append(int(idx_part))
                        except ValueError:
                            pass
            except FileNotFoundError:
                pass
            
            self.log_file_index = max(existing_indices) if existing_indices else 0
            self._rotate_log_file(force_new=True)
            
        except Exception as e:
            print(f"Log file setup error: {e}")
    
    def _rotate_log_file(self, force_new=False):
        """Rotate log file."""
        if force_new or not self.log_file_path or self._get_log_file_size() >= self.max_log_size:
            self.log_file_index += 1
            self.log_file_path = f"logs/resource_temp_log_{self.log_file_index}.txt"
            
            # Add header
            header = (
                f"==== RESOURCE & TEMPERATURE LOG ==== {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                f"Log Interval: {self.log_interval} seconds\n"
                f"Max File Size: {self.max_log_size} bytes (500KB)\n"
                f"File: {os.path.basename(self.log_file_path)}\n"
                + "=" * 60 + "\n"
            )
            
            try:
                with open(self.log_file_path, 'w', encoding='utf-8') as f:
                    f.write(header)
            except Exception as e:
                print(f"Log file creation error: {e}")
    
    def _get_log_file_size(self):
        """Get log file size."""
        if self.log_file_path and os.path.exists(self.log_file_path):
            try:
                return os.path.getsize(self.log_file_path)
            except Exception:
                return 0
        return 0
    
    def _write_log(self, message):
        """Write log message."""
        if not self.logging_enabled or not self.log_file_path:
            return
            
        try:
            # Size check
            if self._get_log_file_size() >= self.max_log_size:
                self._rotate_log_file(force_new=True)
            
            with open(self.log_file_path, 'a', encoding='utf-8') as f:
                f.write(message)
        except Exception as e:
            print(f"Log write error: {e}")
    
    def open_log_folder(self):
        """Open log folder."""
        log_dir = "logs"
        
        if not os.path.exists(log_dir):
            messagebox.showwarning(
                language_manager.get_text('log_folder_not_found'),
                language_manager.get_text('log_folder_message')
            )
            return
        
        try:
            import platform
            if platform.system() == "Windows":
                os.startfile(os.path.abspath(log_dir))
            else:
                # Linux/Mac
                import subprocess
                subprocess.run(["xdg-open", log_dir])
        except Exception as e:
            messagebox.showerror(
                language_manager.get_text('error'),
                language_manager.get_text('log_folder_error').format(str(e))
            )
    
    def _should_log_now(self):
        """Check if it's time to log."""
        current_time = time.time()
        if current_time - self.last_log_time >= self.log_interval:
            self.last_log_time = current_time
            return True
        return False

    def _update_worker(self):
        """Data collection and GUI update worker thread."""
        while self.monitoring:
            # Collect data
            cpu_usage = psutil.cpu_percent(interval=None)
            mem_info = psutil.virtual_memory()
            ram_usage_percent = mem_info.percent
            ram_used_mb = mem_info.used / (1024 * 1024)
            ram_total_mb = mem_info.total / (1024 * 1024)

            # CPU Temperature (using new method)
            cpu_temp = HardwareMonitor.get_cpu_temperature()

            # GPU data (try our hidden nvidia-smi call first, then GPUtil fallback)
            gpu_usage, gpu_temp = "N/A", "N/A"
            n_util, n_temp = HardwareMonitor.get_nvidia_gpu_info()
            if isinstance(n_util, (int, float)) and isinstance(n_temp, (int, float)):
                gpu_usage, gpu_temp = n_util, n_temp
            else:
                gpu_usage_str, gpu_temp_str = HardwareMonitor.get_gpu_info_fallback()
                gpu_usage, gpu_temp = gpu_usage_str, gpu_temp_str

            # Update Min/Max values
            if isinstance(cpu_temp, (int, float)):
                self.cpu_temp_min = min(self.cpu_temp_min, cpu_temp)
                self.cpu_temp_max = max(self.cpu_temp_max, cpu_temp)
            if isinstance(gpu_temp, (int, float)):
                self.gpu_temp_min = min(self.gpu_temp_min, gpu_temp)
                self.gpu_temp_max = max(self.gpu_temp_max, gpu_temp)

            # Schedule GUI update
            data = {
                'cpu_usage': cpu_usage,
                'ram_usage_percent': ram_usage_percent,
                'ram_used_mb': ram_used_mb,
                'ram_total_mb': ram_total_mb,
                'cpu_temp': cpu_temp,
                'gpu_usage': gpu_usage,
                'gpu_temp': gpu_temp,
            }
            if self.monitoring:  # Check if window is still open to avoid errors
                self.after(0, self._update_gui, data)
            
            # Log recording check
            if self.logging_enabled and self._should_log_now():
                self._log_current_data(data)

            time.sleep(self.update_interval)

    def _log_current_data(self, data):
        """Log current data to file."""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # CPU temp format
        cpu_temp_str = f"{data['cpu_temp']:.1f}°C" if isinstance(data['cpu_temp'], (int, float)) else str(data['cpu_temp'])
        
        # GPU temp format
        gpu_temp_str = f"{data['gpu_temp']:.1f}°C" if isinstance(data['gpu_temp'], (int, float)) else str(data['gpu_temp'])
        
        # GPU usage format
        gpu_usage_str = f"{data['gpu_usage']:.1f}%" if isinstance(data['gpu_usage'], (int, float)) else str(data['gpu_usage'])
        
        log_line = (
            f"[{timestamp}] "
            f"CPU: {data['cpu_usage']:.1f}% | {cpu_temp_str} | "
            f"GPU: {gpu_usage_str} | {gpu_temp_str} | "
            f"RAM: {data['ram_usage_percent']:.1f}% ({data['ram_used_mb']:.0f}MB/{data['ram_total_mb']:.0f}MB)\n"
        )
        
        self._write_log(log_line)

    def _update_gui(self, data):
        """Update interface labels."""
        if not self.winfo_exists():
            return

        self.cpu_usage_label.config(text=f"Usage: {data['cpu_usage']:.1f} %")
        self.ram_usage_label.config(text=f"Usage (%): {data['ram_usage_percent']:.1f} %")
        self.ram_usage_mb_label.config(text=f"Usage (MB): {data['ram_used_mb']:.0f} / {data['ram_total_mb']:.0f} MB")

        cpu_temp = data['cpu_temp']
        if isinstance(cpu_temp, (int, float)):
            self.cpu_temp_label.config(text=f"Temperature: {cpu_temp:.1f} °C")
            self.cpu_temp_min_label.config(text=f"Min: {self.cpu_temp_min:.1f} °C")
            self.cpu_temp_max_label.config(text=f"Max: {self.cpu_temp_max:.1f} °C")
        else:
            self.cpu_temp_label.config(text="Temperature: Not Available")
            self.cpu_temp_min_label.config(text="Min: -")
            self.cpu_temp_max_label.config(text="Max: -")

        if isinstance(data['gpu_usage'], (int, float)):
            self.gpu_usage_label.config(text=f"Usage: {data['gpu_usage']:.1f} %")
        else:
            self.gpu_usage_label.config(text=f"Usage: {data['gpu_usage']}")

        if isinstance(data['gpu_temp'], (int, float)):
            self.gpu_temp_label.config(text=f"Temperature: {data['gpu_temp']:.1f} °C")
            self.gpu_temp_min_label.config(text=f"Min: {self.gpu_temp_min:.1f} °C")
            self.gpu_temp_max_label.config(text=f"Max: {self.gpu_temp_max:.1f} °C")
        else:
            self.gpu_temp_label.config(text=f"Temperature: {data['gpu_temp']}")
            self.gpu_temp_min_label.config(text="Min: -")
            self.gpu_temp_max_label.config(text="Max: -")

    def on_close(self):
        """Handle window close event."""
        # Stop logging
        if self.logging_enabled:
            self._write_log("=== Resource & Temperature Monitoring Log Ended (Window Closed) ===\n")
            self.logging_enabled = False
        
        self.monitoring = False
        self.destroy()