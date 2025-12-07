import subprocess
import os
import shutil
import winreg

class WindowsUtils:
    
    # Tool Command Mappings
    TOOLS = {
        'task_mgr': 'taskmgr',
        'dev_mgmt': 'devmgmt.msc',
        'disk_mgmt': 'diskmgmt.msc',
        'services': 'services.msc',
        'event_vwr': 'eventvwr',
        'dxdiag': 'dxdiag',
        'msinfo': 'msinfo32',
        'regedit': 'regedit',
        'control': 'control',
        'cmd': 'start cmd', 
        'powershell': 'start powershell',
        # New Tools & Commands (Shortcuts Tab)
        'hosts_file': 'notepad C:\\Windows\\System32\\drivers\\etc\\hosts',
        'firewall': 'wf.msc',
        'add_remove': 'appwiz.cpl',
        'sys_prop': 'SystemPropertiesAdvanced',
        'win_update_log': 'powershell Get-WindowsUpdateLog',
        # Console Tools (Keep Open)
        'cmd_netstat_p': 'start cmd /k netstat -ano',
        'cmd_flushdns_p': 'start cmd /k "ipconfig /flushdns & pause"',
        'cmd_renew_ip_p': 'start cmd /k "ipconfig /release & ipconfig /renew & pause"',
        'cmd_sfc_p': 'start cmd /k sfc /scannow',
        'cmd_dism_p': 'start cmd /k DISM /Online /Cleanup-Image /RestoreHealth',
    }

    @staticmethod
    def launch_tool(tool_key: str):
        """Launch a Windows system tool."""
        cmd = WindowsUtils.TOOLS.get(tool_key)
        if cmd:
            try:
                subprocess.Popen(cmd, shell=True)
            except Exception as e:
                print(f"Error launching {tool_key}: {e}")

    @staticmethod
    def clean_temp_files() -> str:
        """
        Delete files in %TEMP% and C:\\Windows\\Temp.
        Returns a status message.
        """
        log = []
        
        # 1. User Temp
        user_temp = os.environ.get('TEMP')
        if user_temp:
            log.append(WindowsUtils._clean_dir(user_temp))
            
        # 2. System Temp (Requires Admin usually)
        sys_temp = "C:\\Windows\\Temp"
        if os.path.exists(sys_temp):
            log.append(WindowsUtils._clean_dir(sys_temp))
            
        return "\n".join(log)

    @staticmethod
    def _clean_dir(folder_path):
        count = 0
        errors = 0
        try:
            for filename in os.listdir(folder_path):
                file_path = os.path.join(folder_path, filename)
                try:
                    if os.path.isfile(file_path) or os.path.islink(file_path):
                        os.unlink(file_path)
                        count += 1
                    elif os.path.isdir(file_path):
                        shutil.rmtree(file_path)
                        count += 1
                except Exception:
                    errors += 1
            return f"{folder_path}: Deleted {count}, Skipped {errors}"
        except Exception as e:
            return f"{folder_path}: Error accessing ({e})"

    @staticmethod
    def get_path_variable(scope='user') -> list:
        """Get PATH variable as list. Scope: 'user' or 'system'."""
        try:
            if scope == 'user':
                key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Environment", 0, winreg.KEY_READ)
            else:
                key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\CurrentControlSet\Control\Session Manager\Environment", 0, winreg.KEY_READ)
            
            value, type_ = winreg.QueryValueEx(key, "Path")
            winreg.CloseKey(key)
            
            if not value: return []
            return [p for p in value.split(';') if p]
        except Exception as e:
            print(f"Error reading {scope} PATH: {e}")
            return []

    @staticmethod
    def set_path_variable(scope, path_list) -> bool:
        """Set PATH variable. Scope: 'user' or 'system'."""
        try:
            new_path_str = ";".join(path_list)
            
            if scope == 'user':
                key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Environment", 0, winreg.KEY_SET_VALUE)
            else:
                key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\CurrentControlSet\Control\Session Manager\Environment", 0, winreg.KEY_SET_VALUE)
                
            winreg.SetValueEx(key, "Path", 0, winreg.REG_EXPAND_SZ, new_path_str)
            winreg.CloseKey(key)
            
            # Broadcast change (optional, but good practice)
            # ctypes.windll.user32.SendMessageTimeoutW(0xFFFF, 0x001A, 0, "Environment", 0x0002, 5000, ctypes.byref(ctypes.c_ulonglong()))
            return True
        except Exception as e:
            print(f"Error writing {scope} PATH: {e}")
            return False

    @staticmethod
    def run_command_live(command: str, output_callback):
        """
        Run a shell command and stream output to a callback function.
        Blocking call - should be run in a thread.
        """
        try:
            process = subprocess.Popen(
                command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                errors='replace'  # Handle decoding errors gracefully
            )
            
            # Read stdout
            for line in process.stdout:
                output_callback(line)
            
            # Read stderr
            for line in process.stderr:
                output_callback(f"[Error] {line}")
                
            process.wait()
        except Exception as e:
            output_callback(f"Execution Error: {e}\n")
