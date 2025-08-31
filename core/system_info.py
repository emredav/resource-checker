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