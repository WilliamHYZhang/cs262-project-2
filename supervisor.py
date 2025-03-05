import subprocess
import time
import os
import re
import matplotlib.pyplot as plt
import numpy as np

def run_trial(trial, duration=60):
    processes = []
    # Start three processes concurrently for VM id 1, 2, and 3
    for vm_id in [1, 2, 3]:
        cmd = ["python3", "vm.py", f"--id={vm_id}", f"--trial={trial}", f"--duration={duration}"]
        print(f"Starting: {' '.join(cmd)}")
        p = subprocess.Popen(cmd)
        processes.append(p)
    # Wait for all processes to complete
    for p in processes:
        p.wait()

def parse_log_file(filename):
    """
    Parses a log file with lines like:
      {timestamp:.3f} - {event_type} - Logical Clock: {logical_clock} - {details}
    Returns:
      - rel_times: list of times (relative to the first event)
      - logical_clocks: list of logical clock values
      - queue_lengths: list of queue length values (or None if not available)
      - avg_inter_event: average time difference between consecutive events
    """
    timestamps = []
    logical_clocks = []
    queue_lengths = []
    event_times = []
    
    with open(filename, "r") as f:
        for line in f:
            parts = line.strip().split(" - ")
            if len(parts) < 4:
                continue
            try:
                ts = float(parts[0])
                event_type = parts[1]
                # Parse logical clock from string "Logical Clock: {num}"
                logical_clock = int(parts[2].split(":")[1].strip())
                detail = parts[3]
                timestamps.append(ts)
                logical_clocks.append(logical_clock)
                event_times.append(ts)
                # Check for queue length in the details (only for RECEIVE events)
                ql = None
                m = re.search(r"Queue length: (\d+)", detail)
                if m:
                    ql = int(m.group(1))
                queue_lengths.append(ql)
            except Exception as e:
                continue
    if timestamps:
        start = timestamps[0]
        rel_times = [t - start for t in timestamps]
    else:
        rel_times = []
    if len(event_times) > 1:
        inter_event_times = [j - i for i, j in zip(event_times[:-1], event_times[1:])]
        avg_inter_event = sum(inter_event_times) / len(inter_event_times)
    else:
        avg_inter_event = None
    return rel_times, logical_clocks, queue_lengths, avg_inter_event

def plot_queue_lengths(data):
    """
    data: dict with keys (trial, vm_id) -> (rel_times, queue_lengths)
    Only plots points where a queue length was logged.
    """
    plt.figure(figsize=(12, 8))
    for (trial, vm_id), (times, ql_list) in data.items():
        # Only include points where a queue length value is available
        times_filtered = [t for t, q in zip(times, ql_list) if q is not None]
        ql_filtered = [q for q in ql_list if q is not None]
        if times_filtered:
            plt.plot(times_filtered, ql_filtered, label=f"Trial {trial} - VM {vm_id}")
    plt.xlabel("Time (s)")
    plt.ylabel("Queue Length")
    plt.title("Queue Length over Time")
    plt.legend()
    plt.tight_layout()
    plt.savefig("queue_length.png")
    plt.show()

def plot_logical_clocks(data):
    """
    data: dict with keys (trial, vm_id) -> (rel_times, logical_clock values)
    """
    plt.figure(figsize=(12, 8))
    for (trial, vm_id), (times, lc_list) in data.items():
        plt.plot(times, lc_list, label=f"Trial {trial} - VM {vm_id}")
    plt.xlabel("Time (s)")
    plt.ylabel("Logical Clock")
    plt.title("Logical Clock Progression over Time")
    plt.legend()
    plt.tight_layout()
    plt.savefig("logical_clock.png")
    plt.show()

def plot_avg_inter_event(avg_data):
    """
    avg_data: dict with keys (trial, vm_id) -> avg_inter_event (in seconds)
    Produces a grouped bar chart: each trial is a group with one bar per VM.
    """
    trials = sorted(set(trial for (trial, _) in avg_data.keys()))
    vm_ids = [1, 2, 3]
    x = np.arange(len(trials))
    width = 0.2
    plt.figure(figsize=(10, 6))
    for idx, vm_id in enumerate(vm_ids):
        means = []
        for trial in trials:
            mean_val = avg_data.get((trial, vm_id), 0)
            means.append(mean_val if mean_val is not None else 0)
        plt.bar(x + idx * width, means, width, label=f"VM {vm_id}")
    plt.xlabel("Trial")
    plt.ylabel("Avg Inter-Event Time (s)")
    plt.title("Average Inter-Event Time per VM per Trial")
    plt.xticks(x + width, [str(t) for t in trials])
    plt.legend()
    plt.tight_layout()
    plt.savefig("avg_inter_event.png")
    plt.show()

if __name__ == "__main__":
    num_trials = 5
    duration = 60  # seconds per trial

    # Run each trial.
    for trial in range(1, num_trials + 1):
        print(f"\n--- Starting Trial {trial} ---")
        run_trial(trial, duration)
        # Optional: pause between trials
        time.sleep(5)

    # Data dictionaries for plotting.
    queue_data = {}   # key: (trial, vm_id) -> (rel_times, queue_lengths)
    clock_data = {}   # key: (trial, vm_id) -> (rel_times, logical_clocks)
    avg_data = {}     # key: (trial, vm_id) -> avg inter-event time

    # Process each log file.
    for trial in range(1, num_trials + 1):
        for vm_id in [1, 2, 3]:
            filename = f"vm_{vm_id}_trial{trial}.log"
            if os.path.exists(filename):
                times, clocks, ql_list, avg_ie = parse_log_file(filename)
                queue_data[(trial, vm_id)] = (times, ql_list)
                clock_data[(trial, vm_id)] = (times, clocks)
                avg_data[(trial, vm_id)] = avg_ie
            else:
                print(f"Warning: {filename} not found.")

    # Plot the graphs.
    plot_queue_lengths(queue_data)
    plot_logical_clocks(clock_data)
    plot_avg_inter_event(avg_data)
