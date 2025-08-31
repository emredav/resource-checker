"""
Hardware monitoring utilities for CPU and GPU temperature and usage.

Provides cross-platform hardware monitoring capabilities with multiple fallback strategies.
"""

import os
import threading
import platform
import subprocess
from typing import Optional, Tuple

import psutil

# Platform detection
IS_WINDOWS = platform.system() == "Windows"

if IS_WINDOWS:
    # Windows specific imports
    CREATE_NO_WINDOW = 0x08000000  # subprocess.CREATE_NO_WINDOW
    try:
        import wmi
    except ImportError:
        wmi = None
    try:
        import pythoncom  # pywin32
    except ImportError:
        pythoncom = None
else:
    CREATE_NO_WINDOW = 0
    wmi = None
    pythoncom = None

# Try to import GPUtil
try:
    import GPUtil
except ImportError:
    GPUtil = None

# WMI CoInitialize state tracking per thread
_wmi_thread_local = threading.local()


class HardwareMonitor:
    """Hardware monitoring utilities for CPU and GPU."""

    @staticmethod
    def get_cpu_temperature() -> Optional[float]:
        """Advanced CPU temperature reading with multiple fallback strategies."""
        
        # 1) WMI Win32_TemperatureProbe (more dynamic)
        if IS_WINDOWS and wmi:
            try:
                if pythoncom and not getattr(_wmi_thread_local, "com_initialized", False):
                    pythoncom.CoInitialize()
                    _wmi_thread_local.com_initialized = True
                    
                # Try Win32_TemperatureProbe
                w = wmi.WMI()
                temp_probes = w.Win32_TemperatureProbe()
                cpu_temps = []
                for probe in temp_probes:
                    if probe.CurrentReading and probe.CurrentReading > 0:
                        # Win32_TemperatureProbe usually in Kelvin * 10 format
                        temp_c = (probe.CurrentReading / 10.0) - 273.15
                        if 0 < temp_c < 120:  # Reasonable temperature range
                            cpu_temps.append(temp_c)
                            
                if cpu_temps:
                    return sum(cpu_temps) / len(cpu_temps)
                    
            except Exception:
                pass  # Silent fail
                
        # 2) psutil sensors_temperatures (Linux/Windows sensor drivers)
        try:
            temps = getattr(psutil, 'sensors_temperatures', lambda: {})()
            cpu_temps = []
            for sensor_name, entries in temps.items():
                for entry in entries:
                    if hasattr(entry, 'current') and entry.current:
                        temp = entry.current
                        label = getattr(entry, 'label', '').lower()
                        # Filter CPU related temperatures
                        if (any(keyword in label for keyword in ['cpu', 'core', 'processor', 'package']) or 
                            any(keyword in sensor_name.lower() for keyword in ['cpu', 'core', 'coretemp'])):
                            if 0 < temp < 120:  # Reasonable temperature range
                                cpu_temps.append(temp)
                                
            if cpu_temps:
                return sum(cpu_temps) / len(cpu_temps)
        except Exception:
            pass
            
        # 3) WMI ACPI ThermalZone (last resort, usually static)
        if IS_WINDOWS and wmi:
            try:
                if pythoncom and not getattr(_wmi_thread_local, "com_initialized", False):
                    pythoncom.CoInitialize()
                    _wmi_thread_local.com_initialized = True
                    
                w_acpi = wmi.WMI(namespace="root\\wmi")
                sensors = w_acpi.MSAcpi_ThermalZoneTemperature()
                acpi_temps = []
                for s in sensors:
                    try:
                        if hasattr(s, 'CurrentTemperature') and s.CurrentTemperature:
                            temp_c = (s.CurrentTemperature / 10.0) - 273.15
                            if 0 < temp_c < 120:
                                acpi_temps.append(temp_c)
                    except Exception:
                        continue
                        
                if acpi_temps:
                    return sum(acpi_temps) / len(acpi_temps)
                    
            except Exception:
                pass
                
        # 4) OpenHardwareMonitor WMI (if OHM is running)
        if IS_WINDOWS and wmi:
            try:
                w_ohm = wmi.WMI(namespace="root\\OpenHardwareMonitor")
                sensors = w_ohm.Sensor()
                cpu_temps = []
                for sensor in sensors:
                    if (sensor.SensorType == 'Temperature' and 
                        sensor.Name and 'cpu' in sensor.Name.lower() and
                        sensor.Value is not None):
                        temp = float(sensor.Value)
                        if 0 < temp < 120:
                            cpu_temps.append(temp)
                            
                if cpu_temps:
                    return sum(cpu_temps) / len(cpu_temps)
                    
            except Exception:
                pass  # OHM not installed or no access
                
        return None  # No method succeeded

    @staticmethod
    def get_nvidia_gpu_info() -> Tuple[Optional[float], Optional[float]]:
        """Get NVIDIA GPU usage and temperature using nvidia-smi (hidden console window).

        Returns:
            Tuple of (usage_percent, temperature_celsius) or (None, None) if unavailable
        """
        if not IS_WINDOWS:
            return None, None  # Currently Windows-focused; other platforms use GPUtil
            
        try:
            # Quick check if nvidia-smi exists
            cmd = ['nvidia-smi', '--query-gpu=utilization.gpu,temperature.gpu', '--format=csv,noheader,nounits']
            startupinfo = None
            if IS_WINDOWS:
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            
            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=2,
                startupinfo=startupinfo,
                creationflags=CREATE_NO_WINDOW
            )
            
            if result.returncode != 0:
                return None, None
                
            line = result.stdout.strip().splitlines()[0]
            util_str, temp_str = [p.strip() for p in line.split(',')[:2]]
            util = float(util_str)
            temp = float(temp_str)
            return util, temp
            
        except Exception:
            return None, None

    @staticmethod
    def get_gpu_info_fallback() -> Tuple[str, str]:
        """Get GPU info using GPUtil as fallback.
        
        Returns:
            Tuple of (usage_display, temperature_display)
        """
        if not GPUtil:
            return "GPUtil library not installed.", "pip install gputil"
            
        try:
            gpus = GPUtil.getGPUs()
            if gpus:
                gpu = gpus[0]
                usage = gpu.load * 100
                temp = gpu.temperature
                return f"{usage:.1f} %", f"{temp:.1f} °C"
            else:
                return "No GPU found", "No GPU found"
        except Exception:
            return "Error", "Error"