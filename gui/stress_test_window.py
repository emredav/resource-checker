"""
CPU Stress Test Window for ResourceChecker application.

Provides a dedicated window for running CPU stress tests with performance scoring.
"""

import time
import threading
import multiprocessing as mp
import tkinter as tk
from tkinter import ttk
import psutil
import math

from core.language import language_manager

# --- Workload size & weighting (stabilized constants) ---
# Loop iteration counts per batch (keep these constant for comparable runs)
INT_INNER = 400    # integer arithmetic iterations
BIT_INNER = 300    # bitwise iterations
FLOAT_INNER = 300  # floating point iterations

# Relative weight (cost normalization). Adjust if profiling shows imbalance.
WEIGHT_INT = 1.0
WEIGHT_BIT = 1.0
WEIGHT_FLOAT = 1.0


# --- CPU intensive worker (runs in a separate process) ---
def _process_stress_worker(stop_event, counter):
    """CPU intensive loop executed in its own separate process.

    Purpose: measure per-core raw computational throughput of a mixed synthetic workload
    and expose an approximate operations-per-second figure (Million Ops / s) to the GUI.

    Workload components in each batch:
            - Integer arithmetic (square + add)
            - Bitwise / rotate / xor mixing sequence
            - Floating point math (sin + fused multiply-add) on a small float array

    We treat one iteration of each inner loop as one abstract operation. The combined
    abstract op count per batch is (INT_INNER + BIT_INNER + FLOAT_INNER). Once the
    accumulated local_count reaches FLUSH_THRESHOLD we atomically add it to the shared
    mp.Value counter. The monitor thread samples the counter delta over time to compute
    MOp/s.

    Notes:
        - This is NOT a hardware FLOPS benchmark; it is a relative Python-level synthetic
          throughput indicator sensitive to core count, frequency, and interpreter overhead.
        - Keep environment comparable (background load, power plan) for meaningful comparisons.
    """
    local_count = 0
    # Diversified workload parameters (use global stabilized constants)
    FLUSH_THRESHOLD = 50_000  # accumulated abstract ops before sharing

    # Pre-create float data to work on
    floats = [i * 0.001 for i in range(50)]
    f_len = len(floats)
    angle = 0.0
    while not stop_event.is_set():
        acc = 0
        # Integer arithmetic block
        for i in range(INT_INNER):
            acc += i * i + (acc & 0xFFFF)
        # Bitwise rotate / xor / mix
        x = acc & 0xffffffff
        for _ in range(BIT_INNER):
            x = ((x << 5) | (x >> 27)) & 0xffffffff
            x ^= 0xA5A5A5A5
        acc ^= x
        # Floating point trig/mul/add
        for j in range(FLOAT_INNER):
            idx = j % f_len
            angle += 0.0005
            floats[idx] = math.fma(math.sin(angle), floats[idx] + 1.0001, 0.00001)
        # Approximate operation cost counting using weights
        batch_ops = int(
            INT_INNER * WEIGHT_INT +
            BIT_INNER * WEIGHT_BIT +
            FLOAT_INNER * WEIGHT_FLOAT
        )  # ensure integer for atomic counter (mp.Value 'Q')
        local_count += batch_ops  # stays int
        if local_count >= FLUSH_THRESHOLD:
            with counter.get_lock():
                # local_count guaranteed int
                counter.value += int(local_count)
            local_count = 0
    # Flush remainder
    if local_count:
        with counter.get_lock():
            counter.value += local_count


class CPUStressTestWindow(tk.Toplevel):
    """CPU Stress Test window class."""

    def __init__(self, master, app):
        super().__init__(master)
        self.title(language_manager.get_text('stress_test_title'))
        self.geometry("420x350")
        self.app = app
        self.resizable(False, False)
        
        self.testing = False
        self.processes = []  # multiprocessing.Process list
        self.stop_events = []  # Per-process mp.Event objects
        self.cpu_count = psutil.cpu_count(logical=True)
        
        # Performance scoring variables
        self.test_start_time = None
        self.performance_scores = []
        self.score_interval = 2  # Calculate score every 2 seconds
        self.last_score_time = 0
        # Raw ops tracking
        self.counters = []  # list[mp.Value]
        self.last_total_ops = 0
        self.last_ops_time = None
        self.peak_score = 0.0
        self.recent_scores = []  # for sustainability (last few samples)

        self.setup_widgets()
        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def setup_widgets(self):
        """Setup window widgets."""
        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Core selection
        options_frame = ttk.Frame(main_frame)
        options_frame.pack(fill=tk.X, pady=5)
        ttk.Label(options_frame, text=language_manager.get_text('core_count')).pack(side=tk.LEFT, padx=(0, 10))

        self.thread_var = tk.StringVar()
        thread_options = [str(i) for i in range(1, self.cpu_count + 1)]
        self.thread_combo = ttk.Combobox(options_frame, textvariable=self.thread_var, values=thread_options,
                                         state="readonly", width=5)
        self.thread_combo.pack(side=tk.LEFT)
        self.thread_combo.set(str(self.cpu_count))  # Default to all cores

        # Control buttons
        self.start_button = ttk.Button(main_frame, text=language_manager.get_text('start_test'), command=self.start_test)
        self.start_button.pack(pady=10, fill=tk.X)

        self.stop_button = ttk.Button(main_frame, text=language_manager.get_text('stop_test'), command=self.stop_test, state=tk.DISABLED)
        self.stop_button.pack(pady=5, fill=tk.X)

        # Status label
        self.status_label = ttk.Label(main_frame, text=language_manager.get_text('status_waiting'), anchor=tk.CENTER)
        self.status_label.pack(pady=10, fill=tk.X)
        
        # Performance scoring frame
        performance_frame = ttk.LabelFrame(main_frame, text=language_manager.get_text('performance_scores'), padding="5")
        performance_frame.pack(fill=tk.X, pady=(10, 0))
        
    # Current score
        self.current_score_label = ttk.Label(performance_frame, text=language_manager.get_text('current_score'), font=("Arial", 10, "bold"))
        self.current_score_label.pack(anchor=tk.W)
        
        # Per-core score label (added)
        self.per_core_label = ttk.Label(performance_frame, text=language_manager.get_text('per_core_score'))
        self.per_core_label.pack(anchor=tk.W)

        # Average score
        self.avg_score_label = ttk.Label(performance_frame, text=language_manager.get_text('average_score'))
        self.avg_score_label.pack(anchor=tk.W)
        
        # Max score
        self.max_score_label = ttk.Label(performance_frame, text=language_manager.get_text('max_score'))
        self.max_score_label.pack(anchor=tk.W)

        # Sustainability (thermal throttling indicator)
        self.sustain_label = ttk.Label(performance_frame, text=language_manager.get_text('sustainability'))
        self.sustain_label.pack(anchor=tk.W)
        
        # Test duration
        self.test_duration_label = ttk.Label(performance_frame, text=language_manager.get_text('test_duration'))
        self.test_duration_label.pack(anchor=tk.W)

    def start_test(self):
        """Start the stress test."""
        if self.testing:
            return

        self.testing = True
        self.processes.clear()
        self.stop_events.clear()
        self.performance_scores.clear()
        self.test_start_time = time.time()
        self.last_score_time = 0

        try:
            num_threads = int(self.thread_var.get())
        except ValueError:
            num_threads = self.cpu_count

        # Spawn processes (separate Python interpreter instances) to avoid GUI freeze
        mp_ctx = mp.get_context("spawn")  # explicit for Windows compatibility
        for i in range(num_threads):
            stop_event = mp_ctx.Event()
            counter = mp_ctx.Value('Q', 0, lock=True)  # 64-bit unsigned
            proc = mp_ctx.Process(target=_process_stress_worker, args=(stop_event, counter), daemon=True)
            proc.start()
            self.stop_events.append(stop_event)
            self.processes.append(proc)
            self.counters.append(counter)

        self.last_total_ops = 0
        self.last_ops_time = time.time()
        self.peak_score = 0.0
        self.recent_scores.clear()

        self.status_label.config(text=language_manager.get_text('status_running').format(num_threads))
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.thread_combo.config(state=tk.DISABLED)
        self.app.logger.log(language_manager.get_text('stress_test_started').format(num_threads), "normal")
        
        # Start performance monitoring thread
        self.performance_thread = threading.Thread(target=self._performance_monitor, daemon=True)
        self.performance_thread.start()

    def stop_test(self):
        """Stop the stress test."""
        if not self.testing:
            return

        self.testing = False
        # Signal processes to stop
        for ev in self.stop_events:
            ev.set()
        # Allow processes a brief moment to exit without blocking UI excessively
        def _cleanup_processes(procs):
            # Join with timeout slices to keep UI responsive
            end_time = time.time() + 2  # 2s grace
            for p in procs:
                remaining = end_time - time.time()
                if remaining <= 0:
                    break
                try:
                    p.join(timeout=min(0.2, remaining))
                except Exception:
                    pass
            # Terminate any stragglers
            for p in procs:
                if p.is_alive():
                    try:
                        p.terminate()
                    except Exception:
                        pass
        threading.Thread(target=_cleanup_processes, args=(self.processes,), daemon=True).start()

        self.processes.clear()
        self.stop_events.clear()
        self.counters.clear()
        
        # Final score report
        if self.performance_scores:
            avg_score = sum(self.performance_scores) / len(self.performance_scores)
            max_score = max(self.performance_scores)
            test_duration = time.time() - self.test_start_time
            
            final_report = (
                language_manager.get_text('stress_test_completed').format(
                    int(test_duration//60), int(test_duration%60), avg_score, max_score
                )
            )
            self.status_label.config(text=final_report)
            self.app.logger.log(final_report, "success")
        else:
            self.status_label.config(text=language_manager.get_text('status_stopped'))
            self.app.logger.log(language_manager.get_text('stress_test_stopped'), "normal")
        
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.thread_combo.config(state=tk.NORMAL)

    def _performance_monitor(self):
        """Performance monitoring thread."""
        while self.testing:
            try:
                current_time = time.time()
                if current_time - self.last_score_time >= self.score_interval:
                    self.last_score_time = current_time

                    # Aggregate operation counts from processes
                    total_ops = 0
                    for c in self.counters:
                        try:
                            with c.get_lock():
                                total_ops += c.value
                        except Exception:
                            pass

                    if self.last_ops_time is None:
                        self.last_ops_time = current_time
                        self.last_total_ops = total_ops
                        continue

                    elapsed = current_time - self.last_ops_time
                    ops_diff = max(0, total_ops - self.last_total_ops)
                    ops_per_sec = ops_diff / elapsed if elapsed > 0 else 0

                    # Score: Million Ops / second (MOp/s) of mixed workload
                    power_score = ops_per_sec / 1_000_000
                    if power_score > self.peak_score:
                        self.peak_score = power_score

                    # Track recent scores for sustainability (window of 5)
                    self.recent_scores.append(power_score)
                    if len(self.recent_scores) > 5:
                        self.recent_scores.pop(0)

                    self.last_total_ops = total_ops
                    self.last_ops_time = current_time

                    # Store raw ops_per_sec as basis for averages
                    self.performance_scores.append(power_score)
                    if len(self.performance_scores) > 100:
                        self.performance_scores.pop(0)

                    self.after(0, self._update_performance_display, power_score)

                time.sleep(0.2)
            except Exception as e:
                print(f"Performance monitoring error: {e}")
                time.sleep(0.5)
    
    def _update_performance_display(self, current_score):
        """Update performance display."""
        if not self.winfo_exists() or not self.testing:
            return
        try:
            # Current score (Million Ops / second)
            self.current_score_label.config(text=language_manager.get_text('current_cpu_score').format(current_score))
            active_cores = max(1, len(self.processes))
            per_core = current_score / active_cores
            self.per_core_label.config(text=language_manager.get_text('per_core_cpu_score').format(per_core))
            # Average score
            if self.performance_scores:
                avg_score = sum(self.performance_scores) / len(self.performance_scores)
                self.avg_score_label.config(text=language_manager.get_text('average_cpu_score').format(avg_score))
                # Max score
                max_score = max(self.performance_scores)
                self.max_score_label.config(text=language_manager.get_text('peak_cpu_score').format(max_score))
                # Sustainability
                if self.peak_score > 0 and self.recent_scores:
                    recent_avg = sum(self.recent_scores) / len(self.recent_scores)
                    sustain_pct = (recent_avg / self.peak_score) * 100
                    self.sustain_label.config(text=language_manager.get_text('sustainability_value').format(sustain_pct))
            # Test duration
            if self.test_start_time:
                elapsed = time.time() - self.test_start_time
                minutes = int(elapsed // 60)
                seconds = int(elapsed % 60)
                self.test_duration_label.config(text=language_manager.get_text('test_duration_label').format(minutes, seconds))
        except Exception as e:
            print(f"Display update error: {e}")

    def on_close(self):
        """Handle window close event."""
        if self.testing:
            self.stop_test()
        self.destroy()