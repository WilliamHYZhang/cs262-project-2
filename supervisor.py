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

if __name__ == "__main__":
    num_trials = 5
    duration = 600  # seconds per trial

    # Run each trial.
    for trial in range(1, num_trials + 1):
        print(f"\n--- Starting Trial {trial} ---")
        run_trial(trial, duration)
        # pause between trials
        time.sleep(5)