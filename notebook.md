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

After running five trials, we parsed each VM’s log and generated **three composite plots**, each containing side‐by‐side subplots for Trials 1 through 5:

1. **Composite Average Inter‐Event Time (Figure 1)**  
2. **Composite Logical Clock Progression (Figure 2)**  
3. **Composite Queue Length (Figure 3)**  

> **Figure 1:** *Composite Avg Inter‐Event Time per Trial*  
> Each subplot shows the average time between consecutive log entries for VM1, VM2, and VM3 in a single trial.

![Composite Avg Inter‐Event Time per Trial](graphs/normal/composite_avg_inter_event.png)

> **Figure 2:** *Composite Logical Clock per Trial*  
> Each subplot shows how the logical clocks of VM1, VM2, and VM3 progress over time (0–60s) within one trial.

![Composite Logical Clock per Trial](graphs/normal/composite_logical_clock.png)

> **Figure 3:** *Composite Queue Length per Trial*  
> Each subplot shows how often each VM’s message queue grows, reflecting periods when messages arrive faster (or slower) than they can be processed.

![Composite Queue Length per Trial](graphs/normal/composite_queue_length.png)

Below is a summary of the key behaviors visible in the new plots:

### 1. Average Inter‐Event Time
- In **Figure 1**, each bar chart subplot shows that VM1, VM2, and VM3 have different average inter‐event times (ranging roughly from 0.1 s to 0.7 s in these trials). 
- These differences mainly stem from each VM’s randomly assigned **clock rate** and the proportion of internal vs. send events.
- When a VM has a higher clock rate, it tends to log more frequent events, leading to a smaller average inter‐event time. Conversely, slower VMs have fewer events per second and thus larger gaps between log entries.

### 2. Logical Clock Progression
- In **Figure 2**, you can see that all three VMs’ logical clocks start near 0 s on the time axis and grow steadily until around 60 s. 
- Some trials show very close (almost overlapping) lines for the three VMs, indicating that their tick rates and message exchange rates were similar. Other trials have one VM outpacing the others (its line on the chart climbs more steeply), showing it incremented its clock more frequently—either from faster internal ticks or from receiving higher‐clock messages from peers.
- Notice occasional “crossovers” or abrupt vertical separations when a VM receives a message carrying a significantly larger clock value, forcing it to jump to match that clock + 1.

### 3. Queue Length Dynamics
- In **Figure 3**, each subplot corresponds to a single trial. Most VMs maintain a queue length near zero, but some show sudden spikes (up to 3–5 or more) when messages arrive in rapid bursts. 
- These spikes often happen if a VM’s clock rate is slower or if random event generation leads to multiple sends from other VMs in quick succession. The slower VM may accumulate incoming messages before it processes them, temporarily inflating its queue length.

## Detailed Per‐Trial Highlights

Even though each trial has unique random seeds, the patterns are consistent:

- **Trial 1**: 
  - VM1: Moderate clock rate; occasional queue spikes.
  - VM2: Slightly faster rate, sending more messages, often forcing VM1 and VM3 to “catch up” on their logical clocks.
  - VM3: Slower clock, experiences some queue buildup when VM2 bursts messages.

- **Trial 2**: 
  - VM1: Faster clock rate, leading to more frequent send events and smaller average inter‐event times.
  - VM2: Slowest clock here, building up its queue occasionally and having more “jumps” upon receiving high‐clock messages from VM1.
  - VM3: Intermediate rate, balancing both sends and receives, with moderate queue spikes.

- **Trials 3, 4, 5**: 
  - Similar patterns emerge—random differences in tick rates cause varying degrees of clock divergence. 
  - Some trials show large queue spikes for VM2 (when it’s slower or receiving bursts), while others have VM1 or VM3 as the bottleneck. 
  - The average inter‐event time can shift drastically if a VM’s random clock rate is at the high end (6 ticks/sec) or low end (1 tick/sec).

### General Findings
Across all trials—including Trials 1 and 2—the core behavior remains consistent:
- **Logical Clock Updates:** Internal events increment the clock by one, while receiving messages updates the clock to one more than the maximum of the local and received clocks.
- **Asynchronous Processing:** Logical clocks “drift” apart based solely on causal ordering and randomized event selection, despite underlying physical time synchronization.
- **Message Queue Dynamics:** Variations in message queue lengths reflect differences in how fast VMs process messages relative to their arrival rates. This affects the magnitude of logical clock jumps when messages are processed.

## Observations from the Described Parameters

1. **Clock Rates Restricted to 1–2 ticks/sec**  
   By limiting each VM’s clock rate to either 1 or 2 ticks/sec, we remove the extreme disparities seen in the original 1–6 ticks/sec range. This narrower range yields more similar event frequencies across all three VMs, helping them stay more closely “in sync.”

```python
self.clock_rate = random.randint(1, 2)
```

2. **Higher Send Probability (Fewer Internal Events)**  
   Reducing `rand_val` from a 1–10 range down to 1–5 increases the chance of a send event at each tick (and thus lowers the chance of an internal event). This leads to:
   - More frequent cross‐VM communication, which helps synchronize logical clocks more tightly (fewer large clock “jumps”).  
   - Fewer purely local increments of the logical clock (internal events), so we see a steadier progression of the clocks as messages flow among the three VMs.

```python
rand_val = random.randint(1, 5)
```

---

### 1. Composite Average Inter‐Event Time

> **Figure: Composite Avg Inter‐Event Time**  
> Each subplot corresponds to one trial, with three bars for VM1, VM2, and VM3.

![Composite Avg Inter‐Event Time per Trial](graphs/described/composite_avg_inter_event.png)

- **Closer Ranges Across VMs:**  
  Because the clock rates are all between 1 and 2, the average inter‐event times for the three VMs typically fall within a narrower band—often around 0.6 s to 1.2 s.
- **More Consistent Across Trials:**  
  Compared to the original runs (1–6 ticks/sec), these new trials show smaller differences from trial to trial. We no longer see one VM with a significantly higher frequency of events, so the bar heights are more comparable.

---

### 2. Composite Logical Clock Progression

> **Figure: Composite Logical Clock**  
> Each subplot shows the logical clocks of VM1, VM2, and VM3 from time 0 to ~60 s for a single trial.

![Composite Logical Clock per Trial](graphs/described/composite_logical_clock.png)

- **Nearly Overlapping Lines:**  
  With more frequent sends and closer tick rates, all three lines for each trial often appear tightly grouped. One VM may still outpace the others slightly, but big divergences are rare.
- **Fewer Sudden Jumps:**  
  Because messages are exchanged more steadily, no single VM gets “far ahead” in logical clock value. Consequently, when a slower VM receives a message from a faster one, the update is modest (e.g., going from 20 to 22) rather than huge leaps.
- **Smoother Increments:**  
  We still see an overall upward slope, but with fewer “plateaus” because the probability of sending is higher, prompting more frequent cross‐VM synchronization.

---

### 3. Composite Queue Length

> **Figure: Composite Queue Length**  
> Each subplot shows how the queue length evolves for VM1, VM2, and VM3 over 60 s in a single trial.

![Composite Queue Length per Trial](graphs/described/composite_queue_length.png)

- **Shorter Spikes:**  
  With more balanced event frequencies, most VMs rarely accumulate large message backlogs. Typical queue lengths stay in the 0–3 range, compared to earlier trials where one VM might spike above 10 if it was significantly slower.
- **Smoother Message Flow:**  
  Because messages are exchanged more frequently, arrivals are more evenly distributed, preventing big surges of unprocessed messages. The queue length lines still have some small peaks, but they’re notably smaller than in the original runs.

---

### Overall Impact of the New Parameters

- **Better Synchronization:**  
  The frequent cross‐VM communication (fewer internal events) causes the VMs’ logical clocks to remain more closely aligned throughout the 60 s runs.
- **Reduced Congestion:**  
  Narrower tick‐rate ranges help avoid the scenario of one VM sending an overwhelming number of messages to slower peers, so queue lengths remain smaller and more stable.
- **Improved Predictability:**  
  With fewer extremes in event timing, it becomes easier to anticipate how the system will behave. The Lamport clocks progress in a more uniform fashion, and analyzing the logs is simpler.

## Other Settings: Highly Variable Clock Rates and Event Probabilities

To explore extreme conditions, we modified the simulation parameters as follows:

```python
# Extreme variation simulation:
self.clock_rate = random.randint(1, 20)  # High variability in tick rate
rand_val = random.randint(1, 20)         # Wide range of event probabilities
```

Under these settings, each VM might tick as slowly as 1 tick/sec or as quickly as 20 ticks/sec, and it can choose send vs. internal events with highly variable probabilities. This creates a **highly asynchronous** environment where some VMs can rapidly outpace others, potentially leading to large logical clock discrepancies and significant queue buildup.

After running five such trials, we again collected the logs from VM1, VM2, and VM3, then generated three **composite plots**:

1. **Composite Average Inter‐Event Time (Figure 1)**  
2. **Composite Logical Clock Progression (Figure 2)**  
3. **Composite Queue Length (Figure 3)**  

> **Figure 1:** *Composite Avg Inter‐Event Time per Trial*  
> Each subplot shows the average time between consecutive log entries for VM1, VM2, and VM3 in a single trial under extreme variability.

![Composite Avg Inter‐Event Time per Trial](graphs/other/composite_avg_inter_event.png)

> **Figure 2:** *Composite Logical Clock per Trial*  
> Each subplot shows how the logical clocks of VM1, VM2, and VM3 progress over time (0–60 s) in each of the five trials.

![Composite Logical Clock per Trial](graphs/other/composite_logical_clock.png)

> **Figure 3:** *Composite Queue Length per Trial*  
> Each subplot shows how often each VM’s message queue grows, reflecting the bursts of message arrivals and how quickly (or slowly) they are processed.

![Composite Queue Length per Trial](graphs/other/composite_queue_length.png)

Below is a summary of key behaviors in these “other settings” runs:

### 1. Composite Average Inter‐Event Time
- **Large Disparities Across VMs:**  
  Because a VM might tick at 20 ticks/sec while another is at 1 tick/sec, the difference in event frequencies can be enormous. Fast VMs may log events every 0.05 s on average, while slower ones might log events closer to 1.0 s apart.
- **High Variance Among Trials:**  
  The random selection of clock rates for each trial leads to unpredictable distributions of average inter‐event times. One trial may have two VMs at high rates and one at low, while another has the opposite distribution.

### 2. Logical Clock Progression
- **Highly Irregular Progression:**  
  In **Figure 2**, you can see some trials where one VM’s logical clock climbs **much faster** than the others, sometimes reaching hundreds more ticks by the end of the 60 s run.
- **Large Jumps for Slower VMs:**  
  When a slower VM receives messages from a much faster VM, it must jump its clock to match. These jumps can be very large, e.g., from 50 up to 200 in one event, if the faster VM’s clock is far ahead.
- **Occasional Overlaps:**  
  If two or three VMs happen to draw similar clock rates, their lines overlap more closely, but that’s largely a matter of chance with the 1–20 range.

### 3. Queue Length Dynamics
- **Burstiness and Backlogs:**  
  In **Figure 3**, we see some subplots where a single VM’s queue length spikes to very high levels (e.g., 5–10 or more) if it’s ticking slowly and multiple sends arrive in quick succession from faster VMs.
- **Variable Stability:**  
  Some trials remain relatively stable if the VMs’ random rates happen to be similar, while others show repeated large queue spikes. This underscores how the random selection of tick rates can drastically affect system behavior.

## Conclusions
All trials demonstrate consistent underlying behavior:
- The system reliably adheres to the Lamport clock mechanism despite variations in tick rates.
- Tick rate differences significantly influence logical clock progression, message traffic patterns, and queue congestion.
- Observed variations (message bursts, queue lengths) underscore the importance of timing and synchronization in distributed systems.

