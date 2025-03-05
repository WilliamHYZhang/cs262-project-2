import os
import re
import matplotlib.pyplot as plt
import numpy as np

NUM_TRIALS = 5

def parse_log_file(filename):
    """
    Parses a log file with lines formatted as:
      {timestamp:.3f} - {event_type} - Logical Clock: {logical_clock} - {details}
    Returns:
      - rel_times: list of times (relative to the first event)
      - logical_clocks: list of logical clock values
      - queue_lengths: list of queue length values (or None if not logged)
      - avg_inter_event: average time difference between consecutive events (or None)
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
                # Extract logical clock from string "Logical Clock: {num}"
                logical_clock = int(parts[2].split(":")[1].strip())
                detail = parts[3]
                timestamps.append(ts)
                logical_clocks.append(logical_clock)
                event_times.append(ts)
                # Look for "Queue length: {num}" in details (for RECEIVE events)
                ql = None
                m = re.search(r"Queue length: (\d+)", detail)
                if m:
                    ql = int(m.group(1))
                queue_lengths.append(ql)
            except Exception:
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

def plot_individual_trial(trial, queue_data, clock_data, avg_data):
    """
    For a given trial, create one figure with 3 subplots:
      1. Queue Length vs. Time (3 VMs)
      2. Logical Clock vs. Time (3 VMs)
      3. Avg Inter-Event Time as a bar chart (3 VMs)
    """
    fig, axs = plt.subplots(3, 1, figsize=(8, 12))
    
    # Queue Length subplot
    ax = axs[0]
    for vm_id in [1, 2, 3]:
        if (trial, vm_id) in queue_data:
            times, qls = queue_data[(trial, vm_id)]
            # Filter only events with a logged queue length
            times_filt = [t for t, q in zip(times, qls) if q is not None]
            qls_filt = [q for q in qls if q is not None]
            if times_filt:
                ax.plot(times_filt, qls_filt, label=f"VM {vm_id}")
    ax.set_title(f"Trial {trial} - Queue Length")
    ax.set_xlabel("Time (s)")
    ax.set_ylabel("Queue Length")
    ax.legend()

    # Logical Clock subplot
    ax = axs[1]
    for vm_id in [1, 2, 3]:
        if (trial, vm_id) in clock_data:
            times, clocks = clock_data[(trial, vm_id)]
            ax.plot(times, clocks, label=f"VM {vm_id}")
    ax.set_title(f"Trial {trial} - Logical Clock")
    ax.set_xlabel("Time (s)")
    ax.set_ylabel("Logical Clock")
    ax.legend()

    # Average Inter-Event Time subplot (bar chart)
    ax = axs[2]
    vm_labels = []
    values = []
    for vm_id in [1, 2, 3]:
        if (trial, vm_id) in avg_data:
            vm_labels.append(f"VM {vm_id}")
            avg_val = avg_data[(trial, vm_id)]
            values.append(avg_val if avg_val is not None else 0)
    ax.bar(vm_labels, values)
    ax.set_title(f"Trial {trial} - Avg Inter-Event Time")
    ax.set_xlabel("VM")
    ax.set_ylabel("Avg Inter-Event Time (s)")

    plt.tight_layout()
    plt.savefig(f"trial_{trial}_composite.png")
    plt.show()

def plot_composite_queue(queue_data, num_trials):
    """Composite figure for Queue Length: one subplot per trial (3 VMs per subplot)."""
    fig, axs = plt.subplots(1, num_trials, figsize=(4 * num_trials, 4), sharey=False)
    for trial in range(1, num_trials + 1):
        ax = axs[trial - 1]
        for vm_id in [1, 2, 3]:
            if (trial, vm_id) in queue_data:
                times, qls = queue_data[(trial, vm_id)]
                times_filt = [t for t, q in zip(times, qls) if q is not None]
                qls_filt = [q for q in qls if q is not None]
                if times_filt:
                    ax.plot(times_filt, qls_filt, label=f"VM {vm_id}")
        ax.set_title(f"Trial {trial}")
        ax.set_xlabel("Time (s)")
        ax.set_ylabel("Queue Length")
        ax.legend()
    plt.suptitle("Composite Queue Length per Trial", fontsize=16)
    plt.tight_layout(rect=[0, 0, 1, 0.95])
    plt.savefig("composite_queue_length.png")
    plt.show()

def plot_composite_clock(clock_data, num_trials):
    """Composite figure for Logical Clock: one subplot per trial (3 VMs per subplot)."""
    fig, axs = plt.subplots(1, num_trials, figsize=(4 * num_trials, 4), sharey=False)
    for trial in range(1, num_trials + 1):
        ax = axs[trial - 1]
        for vm_id in [1, 2, 3]:
            if (trial, vm_id) in clock_data:
                times, clocks = clock_data[(trial, vm_id)]
                ax.plot(times, clocks, label=f"VM {vm_id}")
        ax.set_title(f"Trial {trial}")
        ax.set_xlabel("Time (s)")
        ax.set_ylabel("Logical Clock")
        ax.legend()
    plt.suptitle("Composite Logical Clock per Trial", fontsize=16)
    plt.tight_layout(rect=[0, 0, 1, 0.95])
    plt.savefig("composite_logical_clock.png")
    plt.show()

def plot_composite_avg(avg_data, num_trials):
    """Composite figure for Avg Inter-Event Time: one subplot per trial (bar chart per trial)."""
    fig, axs = plt.subplots(1, num_trials, figsize=(4 * num_trials, 4), sharey=False)
    for trial in range(1, num_trials + 1):
        ax = axs[trial - 1]
        vm_labels = []
        values = []
        for vm_id in [1, 2, 3]:
            if (trial, vm_id) in avg_data:
                vm_labels.append(f"VM {vm_id}")
                avg_val = avg_data[(trial, vm_id)]
                values.append(avg_val if avg_val is not None else 0)
        ax.bar(vm_labels, values)
        ax.set_title(f"Trial {trial}")
        ax.set_xlabel("VM")
        ax.set_ylabel("Avg Inter-Event (s)")
    plt.suptitle("Composite Avg Inter-Event Time per Trial", fontsize=16)
    plt.tight_layout(rect=[0, 0, 1, 0.95])
    plt.savefig("composite_avg_inter_event.png")
    plt.show()

if __name__ == "__main__":
    # Dictionaries to hold data from logs:
    # Keys: (trial, vm_id) -> Values: (times, metric data)
    queue_data = {}
    clock_data = {}
    avg_data = {}

    for trial in range(1, NUM_TRIALS + 1):
        for vm_id in [1, 2, 3]:
            filename = f"vm_{vm_id}_trial{trial}.log"
            if os.path.exists(filename):
                times, clocks, ql_list, avg_ie = parse_log_file(filename)
                queue_data[(trial, vm_id)] = (times, ql_list)
                clock_data[(trial, vm_id)] = (times, clocks)
                avg_data[(trial, vm_id)] = avg_ie
            else:
                print(f"Warning: Log file {filename} not found.")

    # Produce individual trial graphs (each with 3 subplots for the 3 VMs)
    for trial in range(1, NUM_TRIALS + 1):
        plot_individual_trial(trial, queue_data, clock_data, avg_data)

    # Produce composite graphs for each metric across all 5 trials.
    plot_composite_queue(queue_data, NUM_TRIALS)
    plot_composite_clock(clock_data, NUM_TRIALS)
    plot_composite_avg(avg_data, NUM_TRIALS)
