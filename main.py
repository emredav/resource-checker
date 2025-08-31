#!/usr/bin/env python3
"""
ResourceChecker - System Monitor

A System monitoring application that tracks CPU, GPU, and RAM usage,
performs network health checks, and provides detailed logging capabilities.

Author: Emre Daver
Version: 1.0.0
"""

import tkinter as tk
from gui.main_window import SystemMonitorGUI


def main():

    root = tk.Tk()
    SystemMonitorGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()