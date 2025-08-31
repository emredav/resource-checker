"""
Logging utilities for ResourceChecker application.

Provides logging capabilities with file rotation and GUI integration.
"""

import os
import time
import threading
from datetime import datetime
from tkinter import scrolledtext, filedialog, messagebox

from core.language import language_manager


class FileManager:
    """File operations utility class."""

    @staticmethod
    def ensure_directory_exists(directory: str):
        """Create directory if it doesn't exist."""
        if not os.path.exists(directory):
            os.makedirs(directory)

    @staticmethod
    def save_to_file(content: str, filepath: str, encoding: str = 'utf-8'):
        """Save content to file."""
        with open(filepath, 'w', encoding=encoding) as f:
            f.write(content)

    @staticmethod
    def export_log_dialog(content: str, title: str = "Save Log File"):
        """Show log export dialog."""
        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
            title=title
        )

        if file_path:
            FileManager.save_to_file(content, file_path)
            messagebox.showinfo(
                language_manager.get_text('success'), 
                language_manager.get_text('export_success').format(file_path)
            )
            return file_path
        return None


class Logger:
    """Logger class for system log operations."""

    def __init__(self, text_widget: scrolledtext.ScrolledText):
        self.text_widget = text_widget
        self.setup_tags()
        # File logging properties
        self.file_logging_enabled = False
        self.base_path = None
        self.current_file_path = None
        self.file_index = 0
        self.max_size_bytes = 500 * 1024  # 500KB limit

    def setup_tags(self):
        """Setup log color tags."""
        self.text_widget.tag_configure("error", foreground="red")
        self.text_widget.tag_configure("success", foreground="green")
        self.text_widget.tag_configure("normal", foreground="black")

    def log(self, message: str, tag: str = "normal"):
        """Add log message."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"
        self.text_widget.insert('end', log_entry, tag)
        self.text_widget.see('end')
        
        # Write to file
        if self.file_logging_enabled:
            try:
                self._write_to_file(log_entry)
            except Exception:
                # Silent error handling to avoid breaking GUI
                pass

    def clear(self):
        """Clear logs."""
        self.text_widget.delete(1.0, 'end')
        self.log(language_manager.get_text('log_cleared'))

    def enable_file_logging(self, base_path: str):
        """Enable continuous file logging with rotation.

        Args:
            base_path: Base path without extension like 'logs/system_log'
            Creates files: base_path_1.txt, base_path_2.txt ...
        """
        FileManager.ensure_directory_exists(os.path.dirname(base_path) or '.')
        self.base_path = base_path
        
        # Find existing files and select highest index
        directory = os.path.dirname(base_path) or '.'
        prefix = os.path.basename(base_path)
        existing = []
        try:
            for fname in os.listdir(directory):
                if fname.startswith(prefix + '_') and fname.endswith('.txt'):
                    try:
                        idx_part = fname[len(prefix) + 1:-4]
                        existing.append(int(idx_part))
                    except ValueError:
                        pass
        except FileNotFoundError:
            pass
        
        self.file_index = max(existing) if existing else 0
        self._rotate_file_if_needed(force_new=True)
        self.file_logging_enabled = True

    def disable_file_logging(self):
        """Disable file logging."""
        self.file_logging_enabled = False

    def _current_size(self) -> int:
        """Get current log file size."""
        if self.current_file_path and os.path.exists(self.current_file_path):
            try:
                return os.path.getsize(self.current_file_path)
            except Exception:
                return 0
        return 0

    def _rotate_file_if_needed(self, force_new: bool = False):
        """Rotate log file if needed."""
        if force_new or not self.current_file_path or self._current_size() >= self.max_size_bytes:
            self.file_index += 1
            self.current_file_path = f"{self.base_path}_{self.file_index}.txt"
            
            # Add header to new file
            header = (
                f"==== LOG FILE START ==== {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                f"Maximum file size: {self.max_size_bytes} bytes (500KB)\n"
                f"File: {os.path.basename(self.current_file_path)}\n"
                + "=" * 60 + "\n"
            )
            try:
                with open(self.current_file_path, 'w', encoding='utf-8') as f:
                    f.write(header)
            except Exception:
                pass

    def _write_to_file(self, log_entry: str):
        """Write log entry to file."""
        if not self.file_logging_enabled or not self.base_path:
            return
            
        # Rotation check (before writing new entry)
        if not self.current_file_path or self._current_size() >= self.max_size_bytes:
            self._rotate_file_if_needed(force_new=True)
        
        try:
            with open(self.current_file_path, 'a', encoding='utf-8') as f:
                f.write(log_entry)
        except Exception:
            pass


class NetworkLogger:
    """Network logger class for network log operations."""

    def __init__(self, text_widget: scrolledtext.ScrolledText):
        self.text_widget = text_widget
        self.setup_tags()
        self.file_logging_enabled = False
        self.base_path = None
        self.current_file_path = None
        self.file_index = 0
        self.max_size_bytes = 500 * 1024

    def setup_tags(self):
        """Setup network log color tags."""
        self.text_widget.tag_configure("error", foreground="red")
        self.text_widget.tag_configure("success", foreground="green")
        self.text_widget.tag_configure("normal", foreground="black")

    def log(self, message: str, tag: str = "normal"):
        """Add network log message."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"
        self.text_widget.insert('end', log_entry, tag)
        self.text_widget.see('end')
        
        if self.file_logging_enabled:
            try:
                self._write_to_file(log_entry)
            except Exception:
                pass

    def clear(self):
        """Clear network logs."""
        self.text_widget.delete(1.0, 'end')
        self.log(language_manager.get_text('log_cleared'))

    def enable_file_logging(self, base_path: str):
        """Enable file logging for network logs."""
        FileManager.ensure_directory_exists(os.path.dirname(base_path) or '.')
        self.base_path = base_path
        directory = os.path.dirname(base_path) or '.'
        prefix = os.path.basename(base_path)
        existing = []
        try:
            for fname in os.listdir(directory):
                if fname.startswith(prefix + '_') and fname.endswith('.txt'):
                    try:
                        idx_part = fname[len(prefix) + 1:-4]
                        existing.append(int(idx_part))
                    except ValueError:
                        pass
        except FileNotFoundError:
            pass
        
        self.file_index = max(existing) if existing else 0
        self._rotate_file_if_needed(force_new=True)
        self.file_logging_enabled = True

    def disable_file_logging(self):
        """Disable file logging."""
        self.file_logging_enabled = False

    def _current_size(self) -> int:
        """Get current log file size."""
        if self.current_file_path and os.path.exists(self.current_file_path):
            try:
                return os.path.getsize(self.current_file_path)
            except Exception:
                return 0
        return 0

    def _rotate_file_if_needed(self, force_new: bool = False):
        """Rotate log file if needed."""
        if force_new or not self.current_file_path or self._current_size() >= self.max_size_bytes:
            self.file_index += 1
            self.current_file_path = f"{self.base_path}_{self.file_index}.txt"
            header = (
                f"==== NETWORK LOG FILE START ==== {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                f"Maximum file size: {self.max_size_bytes} bytes (500KB)\n"
                f"File: {os.path.basename(self.current_file_path)}\n"
                + "=" * 60 + "\n"
            )
            try:
                with open(self.current_file_path, 'w', encoding='utf-8') as f:
                    f.write(header)
            except Exception:
                pass

    def _write_to_file(self, log_entry: str):
        """Write log entry to file."""
        if not self.file_logging_enabled or not self.base_path:
            return
        if not self.current_file_path or self._current_size() >= self.max_size_bytes:
            self._rotate_file_if_needed(force_new=True)
        try:
            with open(self.current_file_path, 'a', encoding='utf-8') as f:
                f.write(log_entry)
        except Exception:
            pass


class AutoLogger:
    """Automatic log saving class."""

    def __init__(self, system_text_widget, network_text_widget):
        self.system_text_widget = system_text_widget
        self.network_text_widget = network_text_widget
        self.enabled = False
        self.system_thread = None
        self.network_thread = None
        self.current_system_start_time = None
        self.current_network_start_time = None

    def start(self):
        """Start automatic log saving."""
        if not self.enabled:
            self.enabled = True
            self.current_system_start_time = datetime.now()
            self.current_network_start_time = datetime.now()

            # System log thread
            self.system_thread = threading.Thread(target=self._system_log_worker, daemon=True)
            self.system_thread.start()

            # Network log thread
            self.network_thread = threading.Thread(target=self._network_log_worker, daemon=True)
            self.network_thread.start()

    def stop(self):
        """Stop automatic log saving."""
        self.enabled = False

    def _system_log_worker(self):
        """System log worker thread."""
        while self.enabled:
            time.sleep(60)  # Wait 1 minutes
            if self.enabled:
                self._save_system_log()

    def _network_log_worker(self):
        """Network log worker thread."""
        while self.enabled:
            time.sleep(60)  # Wait 1 minutes
            if self.enabled:
                self._save_network_log()

    def _save_system_log(self):
        """Save system log."""
        try:
            FileManager.ensure_directory_exists("logs")

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"logs/system_log_{timestamp}.txt"

            log_content = self.system_text_widget.get(1.0, 'end')
            header = f"System Monitor Log - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            header += "=" * 80 + "\n"

            FileManager.save_to_file(header + log_content, filename)

        except Exception as e:
            print(f"Auto system log save error: {str(e)}")

    def _save_network_log(self):
        """Save network log."""
        try:
            FileManager.ensure_directory_exists("logs")

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"logs/network_log_{timestamp}.txt"

            log_content = self.network_text_widget.get(1.0, 'end')
            header = f"Network Monitor Log - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            header += "=" * 80 + "\n"

            FileManager.save_to_file(header + log_content, filename)

        except Exception as e:
            print(f"Auto network log save error: {str(e)}")

    def save_hourly_logs(self):
        """Save hourly logs."""
        if self.enabled:
            try:
                FileManager.ensure_directory_exists("logs")

                # System hourly log
                system_timestamp = self.current_system_start_time.strftime("%Y%m%d_%H%M%S")
                system_filename = f"logs/hourly_system_log_{system_timestamp}.txt"
                system_content = self.system_text_widget.get(1.0, 'end')
                system_header = f"Hourly System Log - {self.current_system_start_time.strftime('%Y-%m-%d %H:%M:%S')} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                system_header += "=" * 80 + "\n"
                FileManager.save_to_file(system_header + system_content, system_filename)

                # Network hourly log
                network_timestamp = self.current_network_start_time.strftime("%Y%m%d_%H%M%S")
                network_filename = f"logs/hourly_network_log_{network_timestamp}.txt"
                network_content = self.network_text_widget.get(1.0, 'end')
                network_header = f"Hourly Network Log - {self.current_network_start_time.strftime('%Y-%m-%d %H:%M:%S')} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                network_header += "=" * 80 + "\n"
                FileManager.save_to_file(network_header + network_content, network_filename)

                # Start new period
                self.current_system_start_time = datetime.now()
                self.current_network_start_time = datetime.now()

                # Clear logs
                self.system_text_widget.delete(1.0, 'end')
                self.network_text_widget.delete(1.0, 'end')

            except Exception as e:
                print(f"Hourly log save error: {str(e)}")