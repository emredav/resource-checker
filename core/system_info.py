"""
System information and process monitoring utilities.

Provides functionality to gather CPU, memory, and network usage information,
as well as monitor top consuming processes.
"""

import time
import psutil
from typing import List, Dict, Tuple


class SystemInfo:
    """System information gathering class."""

    @staticmethod
    def get_cpu_usage(interval: float = 1.0) -> float:
        """Get CPU usage percentage."""
        return psutil.cpu_percent(interval=interval)

    @staticmethod
    def get_memory_info():
        """Get memory information."""
        return psutil.virtual_memory()

    @staticmethod
    def get_public_ip() -> str:
        """Get public IP address (blocking call)."""
        try:
            import urllib.request
            with urllib.request.urlopen('https://api.ipify.org', timeout=3) as response:
                return response.read().decode('utf-8')
        except Exception:
            return "Unreachable"

    @staticmethod
    def get_detailed_specs() -> Dict[str, str]:
        """Get detailed static system specifications."""
        import platform
        import os
        import datetime
        
        specs = {
            'os': f"{platform.system()} {platform.release()} ({platform.version()})",
            'cpu': platform.processor(),
            'ram': "Unknown",
            'mobo': "Unknown",
            'gpu': "Unknown",
            'bios': "Unknown",
            'uptime': "Unknown",
            'ram_detail': [],
            'disk_detail': [],
            'adapters': []
        }

        # Boot time / Uptime
        try:
            boot_time = psutil.boot_time()
            bt = datetime.datetime.fromtimestamp(boot_time)
            now = datetime.datetime.now()
            uptime = now - bt
            days = uptime.days
            hours, remainder = divmod(uptime.seconds, 3600)
            minutes, _ = divmod(remainder, 60)
            specs['uptime'] = f"{days}d {hours}h {minutes}m"
        except:
            pass

        # Improve CPU and other info via WMI on Windows
        if platform.system() == "Windows":
             try:
                 import wmi
                 c = wmi.WMI()
                 
                 # CPU
                 try:
                     for processor in c.Win32_Processor():
                         specs['cpu'] = processor.Name.strip()
                         break
                 except: pass

                 # BIOS
                 try:
                     for bios in c.Win32_BIOS():
                         specs['bios'] = f"{bios.Manufacturer} ({bios.SMBIOSBIOSVersion or bios.Version})"
                         break
                 except: pass

                 # Motherboard
                 try:
                    for board in c.Win32_BaseBoard():
                        manufacturer = board.Manufacturer
                        product = board.Product
                        specs['mobo'] = f"{manufacturer} - {product}"
                        break
                 except: pass

                 # GPU
                 try:
                    gpus = []
                    for gpu in c.Win32_VideoController():
                        gpus.append(gpu.Name)
                    if gpus:
                        specs['gpu'] = ", ".join(gpus)
                 except: pass

                 # RAM Details (Physical Memory)
                 try:
                    ram_sticks = []
                    for mem in c.Win32_PhysicalMemory():
                        capacity_gb = int(mem.Capacity) / (1024**3)
                        speed = mem.Speed
                        manufacturer = mem.Manufacturer
                        part_num = mem.PartNumber.strip() if mem.PartNumber else ""
                        ram_sticks.append(f"{manufacturer} {part_num} ({capacity_gb:.0f}GB @ {speed}MHz)")
                    specs['ram_detail'] = ram_sticks
                 except: pass

                 # Disk Details (Physical Drives)
                 try:
                    disks_phys = []
                    for drive in c.Win32_DiskDrive():
                        model = drive.Model
                        size_gb = int(drive.Size) / (1024**3)
                        disks_phys.append(f"{model} ({size_gb:.0f} GB)")
                    specs['disk_detail'] = disks_phys
                 except: pass

             except:
                 pass
        
        # Network Adapters (Interface + IP)
        try:
            adapters_data = []
            import socket
            if_addrs = psutil.net_if_addrs()
            for name, addrs in if_addrs.items():
                for addr in addrs:
                    if addr.family == socket.AF_INET and addr.address != "127.0.0.1":
                        adapters_data.append((name, addr.address))
            specs['adapters'] = adapters_data
        except:
            pass
        
        # Fallback/Additional logic for non-WMI or general
        
        # RAM Total (Simple)
        try:
             mem = psutil.virtual_memory()
             total_gb = mem.total / (1024**3)
             specs['ram'] = f"{total_gb:.2f} GB"
        except:
             pass

        # Disk Partitions (Logical) if Physical failed or requested
        # We keep the old 'disk' key for partitions for backward compatibility or extra info
        disks_log = []
        try:
            for partition in psutil.disk_partitions():
                try:
                    usage = psutil.disk_usage(partition.mountpoint)
                    total_gb = usage.total / (1024**3)
                    free_gb = usage.free / (1024**3)
                    disks_log.append(f"{partition.device} ({partition.mountpoint}) - {total_gb:.1f} GB Total")
                except PermissionError:
                    continue
        except:
             pass
        specs['disk'] = disks_log if disks_log else []

        # Network Info (IP & MAC)
        import socket
        import uuid
        
        # Local IP
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            s.close()
        except:
            local_ip = "127.0.0.1"
        specs['ip'] = local_ip

        # MAC Address
        try:
            mac_num = uuid.getnode()
            mac = ':'.join(['{:02x}'.format((mac_num >> elements) & 0xff) for elements in range(0,2*6,2)][::-1])
            specs['mac'] = mac.upper()
        except:
             specs['mac'] = "Unknown"
        
        specs['public_ip'] = "Loading..." # Will be fetched async by UI

        return specs

    @staticmethod
    def get_network_usage() -> Tuple[int, int, int]:
        """Get network usage (sent, recv, total)."""
        try:
            net_io_1 = psutil.net_io_counters()
            time.sleep(1)
            net_io_2 = psutil.net_io_counters()

            bytes_sent = net_io_2.bytes_sent - net_io_1.bytes_sent
            bytes_recv = net_io_2.bytes_recv - net_io_1.bytes_recv
            total = bytes_sent + bytes_recv

            return bytes_sent, bytes_recv, total
        except Exception:
            return 0, 0, 0


class ProcessMonitor:
    """Process monitoring class."""

    def __init__(self, top_count: int = 3):
        self.top_count = top_count

    def set_top_count(self, count: int):
        """Set the number of top consuming applications to track."""
        self.top_count = count

    def get_top_cpu_processes(self) -> List[Dict]:
        """Get top CPU consuming processes."""
        processes = []

        try:
            process_list = []
            # Get all processes
            for proc in psutil.process_iter(['pid', 'name', 'memory_info']):
                try:
                    process_list.append(proc)
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    continue

            # First CPU measurement
            cpu_measurements = {}
            for proc in process_list:
                try:
                    cpu_measurements[proc.pid] = proc.cpu_percent()
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    continue

            # Wait for accurate measurement
            time.sleep(1.0)

            # Second CPU measurement
            for proc in process_list:
                try:
                    cpu_usage = proc.cpu_percent()

                    # Filter low CPU usage and system processes
                    if (cpu_usage is not None and cpu_usage > 0.1 and
                            proc.info['name'].lower() not in ['system idle process', 'system', '[system process]']):
                        cpu_display = cpu_usage / 10

                        processes.append({
                            'name': proc.info['name'],
                            'cpu': cpu_display,
                            'memory': proc.info['memory_info'].rss / 1024 / 1024,  # MB
                            'pid': proc.info['pid']
                        })
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    continue

        except Exception as e:
            print(f"Error getting CPU process list: {str(e)}")

        # Sort by CPU usage and return specified count
        processes.sort(key=lambda x: x['cpu'], reverse=True)
        return processes[:self.top_count]

    def get_top_network_processes(self) -> List[Dict]:
        """Get top network consuming processes."""
        network_processes = []

        for proc in psutil.process_iter(['pid', 'name']):
            try:
                proc_info = proc.info
                connections = proc.net_connections()

                if connections:
                    connection_count = len(connections)
                    established_connections = len([c for c in connections if c.status == 'ESTABLISHED'])

                    # Calculate network usage score
                    network_score = established_connections * 10 + connection_count

                    if network_score > 0:
                        network_processes.append({
                            'name': proc_info['name'],
                            'network_score': network_score,
                            'connections': established_connections,
                            'pid': proc_info['pid']
                        })

            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass

        # Sort by network score and return specified count
        network_processes.sort(key=lambda x: x['network_score'], reverse=True)
        return network_processes[:self.top_count]

    def get_top_memory_processes(self) -> List[Dict]:
        """Get top memory consuming processes."""
        processes = []

        try:
            # Get all processes
            for proc in psutil.process_iter(['pid', 'name', 'memory_info']):
                try:
                    mem_info = proc.info['memory_info']
                    if mem_info:
                        memory_mb = mem_info.rss / 1024 / 1024  # Convert to MB
                        
                        # Filter system processes if needed, similar to CPU
                        if memory_mb > 10: # Filter very small processes
                             processes.append({
                                'name': proc.info['name'],
                                'memory': memory_mb,
                                'pid': proc.info['pid']
                            })

                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    continue

        except Exception as e:
            print(f"Error getting memory process list: {str(e)}")

        # Sort by memory usage and return specified count
        processes.sort(key=lambda x: x['memory'], reverse=True)
        return processes[:self.top_count]
