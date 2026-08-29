# ⚡ Context Switching Overhead Analyzer
A performance-analysis tool and scheduling simulator that quantifies CPU context-switching overhead and measures system-level resource allocation under process contention. 

## 📊 Interactive Simulation Dashboard
![Round Robin Simulation](./screenshots/IMG-20260416-WA0016.jpg)).

## ⚙️ Supported Algorithms
The simulator dynamically adapts Gantt chart visualizations and calculates exact performance loss for First-Come-First-Serve (FCFS), Shortest Job First (SJF), and Round Robin (RR).

| FCFS Scheduling | SJF Scheduling |
| :---: | :---: |
| ![FCFS](./screenshots/IMG-20260416-WA0019.jpg) | ![SJF](./screenshots/IMG-20260416-WA0021.jpg) |

## 📈 Key Metrics Calculated
*   **Context Switches:** Total number of times the CPU switches between active processes.
*   **CS Overhead:** Exact millisecond delay introduced by process swapping.
*   **Performance Loss:** Percentage of overall CPU time consumed by context switching.
*   **Turnaround & Waiting Time:** Granular per-process efficiency metrics.
