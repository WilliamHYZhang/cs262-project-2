# Engineering Notebook: Asynchronous Distributed Logical Clocks

**Date:** March 3, 2025

## Project Overview
The goal of this project was to simulate a small asynchronous distributed system using three virtual machines (VMs) that communicate via WebSocket using JSON messages. Each VM has its own “clock rate” (randomly chosen between 1 and 6 ticks per second) and a Lamport-style logical clock that is incremented on internal events, send events, and updated on message receipt. During initialization, each VM establishes connections with the other VMs and logs all events (internal, send, and receive) with the system time, the logical clock value, and additional details (such as the length of the message queue).

## Design Decisions
- **Asynchronous Simulation & WebSocket Communication:**  
  Each VM runs on its own port (8001, 8002, and 8003) and uses the `websockets` library along with asyncio for concurrency. Connections between the VMs are established during initialization, and messages are transmitted in JSON format.

- **Clock Rate and Logical Clock Implementation:**  
  Every VM picks a random clock rate (between 1 and 6 ticks per second). For every tick:
  - If there is an incoming message, the VM processes it and updates its logical clock using the rule:  
    **new_clock = max(local_clock, received_clock) + 1**.
  - Otherwise, the VM performs either a send event or an internal event—both of which increment the logical clock by one.

- **Logging and Trials:**  
  Each event is logged to a file with a timestamp, event type, logical clock value, and details such as the message queue length. A `--trial` parameter was introduced so that each simulation run (trial) produces separate log files (e.g., `vm_1_trial1.log`, `vm_1_trial2.log`, etc.) for analysis.

- **Randomized Behavior:**  
  A random number (between 1 and 10) is used to decide whether a tick results in a send event (which might involve sending to one or both peers) or an internal event. This randomness introduces variability in the logs and demonstrates how messages cause the logical clocks to “jump” when they are received.

## Observations from Trials

Here we focus specifically on Trials 1 and 2, but we observe similar behavior across all trials.

### Trial 1
- **VM1 Observations:**  
  VM1 has a tick rate of approximately **1 tick/sec**, evidenced by consistent ~1-second intervals between internal events. The log for VM1 begins with send events (logical clock values 1 and 2). Shortly thereafter, a receive event causes the clock to jump to 11 (demonstrating the Lamport update rule). Several receive events follow (e.g., jumps from 14 to 27 and then to 33), indicating that messages arriving from VM2 carried higher clock values. Internal events then increment the clock gradually.

- **VM2 Observations:**  
  VM2 exhibits a significantly higher tick rate (~4 ticks/sec), logging frequent events at shorter intervals. Its log starts with internal events and proceeds to send messages to both VM3 and VM1. Its logical clock increases smoothly, with occasional bursts in the message queue length, suggesting it sometimes receives messages faster than it can process them.

- **VM3 Observations:**  
  VM3 also operates at about **1 tick/sec**, initially logging internal events and later starting to receive messages from both VM1 and VM2. Its logical clock increments modestly during early events and later shows send events propagating its own clock values. The slower tick rate leads to notable clock jumps when receiving messages from the faster VM2.

### Trial 2
- **VM1 Observations:**  
  VM1 increases its tick rate to approximately **5 ticks/sec**, resulting in frequent internal and send events. It exhibits a rhythmic pattern initially—with early send events (clock values 1–2) followed by internal and additional send events (clock values 4–5). Message receptions (e.g., at logical clocks 19 and 22) show visible jumps. Although pacing differs slightly from Trial 1, the underlying mechanism remains consistent.

- **VM2 Observations:**  
  VM2's tick rate decreases significantly to about **1 tick/sec**, becoming the slowest node and experiencing significant message queue backlogs. Logs indicate higher incoming message rates with longer queues (sometimes exceeding 20 messages), signifying burstier traffic.

- **VM3 Observations:**  
  VM3 operates at a moderate tick rate (~3 ticks/sec), showing a balanced event-processing rate and queue management. It demonstrates a mix of internal, send, and receive events. The logical clock increments steadily until significant jumps occur upon message reception.

### General Findings
Across all trials—including Trials 1 and 2—the core behavior remains consistent:
- **Logical Clock Updates:** Internal events increment the clock by one, while receiving messages updates the clock to one more than the maximum of the local and received clocks.
- **Asynchronous Processing:** Logical clocks “drift” apart based solely on causal ordering and randomized event selection, despite underlying physical time synchronization.
- **Message Queue Dynamics:** Variations in message queue lengths reflect differences in how fast VMs process messages relative to their arrival rates. This affects the magnitude of logical clock jumps when messages are processed.

### Running with Smaller Variations and Lower Event Probabilities
We reran the simulation with the following modifications from the original design:
- **Reduced Clock Rate Variation:** Adjusted tick rates to a smaller range (1–2 ticks/sec) to limit the clock frequency disparity among VMs.
- **Lower Internal Event Probability:** Increased the likelihood of send events (reduced probability of internal events), making interactions between VMs more frequent.

```python
# Original code:
self.clock_rate = random.randint(1, 6)  # Original tick rate range
rand_val = random.randint(1, 10)        # Original event probability

# Modified for rerun with smaller variations and lower internal event probability:
self.clock_rate = random.randint(1, 2)  # Reduced tick rate variation (1–2 ticks/sec)
rand_val = random.randint(1, 5)         # Increased send event probability (e.g., internal events less likely)
```

Under these new conditions, logical clocks remained closer to each other with fewer and smaller jumps in logical clock values. The message queues maintained shorter lengths, reflecting a smoother flow of messages between VMs. This resulted in increased synchronization and decreased message congestion compared to trials with higher variation and internal event probabilities.

This rerun highlights the sensitivity of logical clock behavior to timing parameters and event probabilities, demonstrating how even modest parameter adjustments significantly improve overall synchronization and message-handling efficiency.

### Other Settings

We explored further variations to evaluate system behavior under extreme conditions, particularly focusing on scenarios with significantly higher variability in tick rates and event probabilities:

```python
# Extreme variation simulation:
self.clock_rate = random.randint(1, 50)  # High variability in tick rate (1-50 ticks/sec)
rand_val = random.randint(1, 50)         # Wide range of event probabilities
```

Under these extreme conditions, the following observations were noted:

- **Highly Irregular Logical Clock Progression:**
  The vast disparity in clock rates caused some VMs to rapidly outpace others, leading to significant differences in logical clock values. This resulted in dramatic clock "jumps" when slower VMs received messages from faster counterparts.

- **Message Queue Instability:**
  VM nodes with lower clock rates struggled to handle incoming message traffic, often experiencing message queues that quickly grew beyond manageable limits. This resulted in message processing delays, further exacerbating clock discrepancies.

- **Increased Network Congestion:**
  With a wide event probability range, frequent bursts of simultaneous send events occurred. These bursts generated temporary network congestion and further imbalanced workload distribution across VMs.

- **Reduced Predictability:**
  The randomness of the high variability scenario significantly lowered the predictability of system behavior, making analysis more challenging but also clearly demonstrating the robustness of the Lamport logical clock mechanism under highly asynchronous conditions.

## Conclusions
All trials demonstrate consistent underlying behavior:
- The system reliably adheres to the Lamport clock mechanism despite variations in tick rates.
- Tick rate differences significantly influence logical clock progression, message traffic patterns, and queue congestion.
- Observed variations (message bursts, queue lengths) underscore the importance of timing and synchronization in distributed systems.

