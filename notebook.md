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

Here we focus on specifically Trials 1 and 2, but we observe that all of the trials show similar behavior, discussed more in the conclusion.

### Trial 1
- **VM1 Observations:**  
  The log for VM1 begins with send events (logical clock values 1 and 2). Shortly thereafter, a receive event causes the clock to jump to 11 (demonstrating the Lamport update rule). Several receive events follow (e.g., jumps from 14 to 27 and then to 33), which indicate that messages arriving from VM2 carried higher clock values. Internal events then increment the clock gradually.

- **VM2 Observations:**  
  VM2’s log starts with a series of internal events and then proceeds to send messages to both VM3 and VM1. Its logical clock increases smoothly, with occasional bursts in the message queue length suggesting that it sometimes receives messages faster than it can process them.

- **VM3 Observations:**  
  VM3 initially logs internal events and later starts receiving messages from both VM1 and VM2. Its logical clock increments modestly during early events and later shows send events that propagate its own clock values. The overall behavior reflects a combination of internal progression and influences from incoming messages.

### Trial 2
- **VM1 Observations (Trial 2):**  
  In this trial, VM1 exhibits a more rhythmic pattern at the beginning—with early send events (clock values 1–2) followed by internal events and additional send events (clock values 4–5). When messages are received (e.g., at logical clocks 19 and 22), the clock jumps are clearly visible. Although the pacing differs slightly from Trial 1, the underlying mechanism is the same.

- **VM2 and VM3 Observations (Trial 2):**  
  - **VM2:** The log shows a higher rate of incoming messages, with longer queue lengths (sometimes exceeding 20 messages), indicating burstier message traffic.  
  - **VM3:** The log demonstrates a mix of internal events and both send and receive events. Its logical clock increments steadily until significant jumps occur during send events.
  
### General Findings
Across all trials—including Trials 1 and 2—the core behavior remains consistent:
- **Logical Clock Updates:** Internal events increment the clock by one, while receiving a message updates the clock to one more than the maximum of the local and received clocks.
- **Asynchronous Processing:** The logical clocks “drift” apart based solely on the causal ordering of events and the randomized nature of event selection, even though the underlying physical time remains essentially the same.
- **Message Queue Dynamics:** Variations in message queue lengths reflect differences in how fast a VM processes messages compared to the rate at which they arrive. This, in turn, affects the size of the clock jumps when messages are processed.

## Conclusions
All trials (as evidenced by Trials 1 and 2) demonstrate the same underlying behavior:
- The system reliably adheres to the Lamport clock mechanism.
- Despite variations in the timing and size of clock jumps, all VMs maintain a consistent causal ordering.
- The observed differences (such as the burstiness of message traffic and varying queue lengths) are due to the inherent randomness in event selection and clock rate, not any flaws in the logical clock algorithm.
- Overall, while the specific numerical values differ between trials, the fundamental behavior is the same across all trials.
