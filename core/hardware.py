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
        """Advanced CPU temperature reading with prioritized strategies."""
        
        # Priority 1: OpenHardwareMonitor WMI (Best if running)
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
                pass

        # Priority 2: LibreHardwareMonitor WMI (Best if running)
        if IS_WINDOWS and wmi:
            try:
                w_lhm = wmi.WMI(namespace="root\\LibreHardwareMonitor")
                sensors = w_lhm.Sensor()
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
                pass

        # Priority 3: Intel 'Esif_Temperature' (Best Native Driver)
        if IS_WINDOWS and wmi:
            try:
                # Ensure COM is initialized for this thread
                if pythoncom and not getattr(_wmi_thread_local, "com_initialized", False):
                    pythoncom.CoInitialize()
                    _wmi_thread_local.com_initialized = True

                w_intel = wmi.WMI(namespace="root\\Intel\\Esif")
                sensors = w_intel.Esif_Temperature()
                esif_temps = []
                for s in sensors:
                    if hasattr(s, 'Temperature') and s.Temperature > 0:
                        temp_val = float(s.Temperature)
                        # Heuristic to detect scale
                        if temp_val > 2000: # millidegrees?
                            temp_c = temp_val / 1000.0
                        elif temp_val > 200: # tenths?
                            temp_c = temp_val / 10.0
                        else:
                            temp_c = temp_val
                            
                        if 0 < temp_c < 120:
                            esif_temps.append(temp_c)
                if esif_temps:
                    return sum(esif_temps) / len(esif_temps)
            except Exception:
                pass

        # Priority 4: Windows Performance Counters (Native OS)
        if IS_WINDOWS and wmi:
            try:
                w_cimv2 = wmi.WMI(namespace="root\\cimv2")
                thermals = w_cimv2.Win32_PerfFormattedData_Counters_ThermalZoneInformation()
                perf_temps = []
                for t in thermals:
                    # 'Temperature' is usually in Kelvin
                    if hasattr(t, 'Temperature') and t.Temperature > 0:
                        temp_k = float(t.Temperature)
                        temp_c = temp_k - 273.15
                        if 0 < temp_c < 120:
                            perf_temps.append(temp_c)
                if perf_temps:
                    return sum(perf_temps) / len(perf_temps)
            except Exception:
                pass

        # Priority 5: psutil sensors (Cross-platform standard)
        try:
            temps = getattr(psutil, 'sensors_temperatures', lambda: {})()
            cpu_temps = []
            for sensor_name, entries in temps.items():
                for entry in entries:
                    if hasattr(entry, 'current') and entry.current:
                        temp = entry.current
                        label = getattr(entry, 'label', '').lower()
                        if (any(keyword in label for keyword in ['cpu', 'core', 'processor', 'package']) or 
                            any(keyword in sensor_name.lower() for keyword in ['cpu', 'core', 'coretemp'])):
                            if 0 < temp < 120:
                                cpu_temps.append(temp)
            if cpu_temps:
                return sum(cpu_temps) / len(cpu_temps)
        except Exception:
            pass

        # Priority 6: Win32_TemperatureProbe (Legacy WMI)
        if IS_WINDOWS and wmi:
            try:
                w = wmi.WMI()
                temp_probes = w.Win32_TemperatureProbe()
                cpu_temps = []
                for probe in temp_probes:
                    if probe.CurrentReading and probe.CurrentReading > 0:
                        temp_c = (probe.CurrentReading / 10.0) - 273.15
                        if 0 < temp_c < 120:
                            cpu_temps.append(temp_c)
                if cpu_temps:
                    return sum(cpu_temps) / len(cpu_temps)
            except Exception:
                pass

        # Priority 7: MSAcpi_ThermalZoneTemperature (Last Resort - often static)
        if IS_WINDOWS and wmi:
            try:
                w_acpi = wmi.WMI(namespace="root\\wmi")
                sensors = w_acpi.MSAcpi_ThermalZoneTemperature()
                acpi_temps = []
                for s in sensors:
                    try:
                        if hasattr(s, 'CurrentTemperature') and s.CurrentTemperature:
                            temp_c = (s.CurrentTemperature / 10.0) - 273.15
                            # Filter out suspicious exact static values if possible?
                            # 27.9 is 3010.5 Kelvin. hard to hardcode ban.
                            if 0 < temp_c < 120:
                                acpi_temps.append(temp_c)
                    except Exception:
                        continue
                if acpi_temps:
                    return sum(acpi_temps) / len(acpi_temps)
            except Exception:
                pass
                
        return None



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