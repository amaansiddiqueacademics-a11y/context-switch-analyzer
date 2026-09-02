# ⚡ Context Switch Overhead Analyzer

> A full-stack, interactive CPU process scheduling simulator that visualizes context switching overhead in real time — built with a FastAPI Python backend and a React-powered single-page frontend.

---

## 📸 Overview

The **Context Switch Overhead Analyzer** lets you simulate, visualize, and compare classic CPU scheduling algorithms side by side. Watch processes compete for CPU time on an animated Gantt chart, measure the exact performance cost of every context switch, and export results — all in a premium dark-mode UI.

---

## 🗂️ Project Structure

```
context-switch-analyzer/
└── context-Switching-2/
    ├── backend/
    │   └── main.py          # FastAPI simulation engine (Python)
    └── frontend/
        └── Context-Switch.html  # React SPA (CDN-loaded, zero-build)
```

---

## 🛠️ Tech Stack

### Backend
| Layer | Technology |
|---|---|
| Runtime | Python 3.10+ |
| Framework | FastAPI v3.0.0 |
| Validation | Pydantic v2 |
| Server | Uvicorn (ASGI) |
| CORS | FastAPI CORSMiddleware |

### Frontend
| Layer | Technology |
|---|---|
| UI Library | React 18 (CDN UMD build) |
| Transpiler | Babel Standalone |
| Fonts | Syne + JetBrains Mono (Google Fonts) |
| Styling | Vanilla CSS (CSS Custom Properties, animations) |
| Charts | Pure SVG / DOM (no chart library dependency) |

---

## ✨ Features

### 🔀 Scheduling Algorithms
- **FCFS** — First Come, First Served (non-preemptive, arrival-time ordered)
- **SJF** — Shortest Job First (non-preemptive, greedy shortest-burst)
- **RR** — Round Robin with a configurable **time quantum** (1–∞ units)

### 📊 Real-Time Simulation
- Animated **Gantt chart** with process blocks and golden context-switch markers
- Live **CPU visual** — shows the currently running process, idle state, or context-switch flash
- **Process queue viewer** with per-process status (running / waiting / done)
- Adjustable **simulation speed** slider
- Step-by-step execution (frame-by-frame stepping)

### 📈 Performance Metrics
- Average **Waiting Time** & **Turnaround Time**
- **CPU Utilization %** with animated sparkline history
- Total **Context Switches** count
- **Context Switch Overhead** (ms) based on configurable overhead per switch
- **Performance Loss %** due to context switching

### ⚖️ Algorithm Comparison Mode
- Run FCFS, SJF, and RR **simultaneously** against the same process set
- Side-by-side comparison grid for all key metrics

### 🔌 Backend API Integration
- Optional FastAPI backend provides **server-side simulation** via POST /simulate
- /compare endpoint runs all three algorithms in one request
- /presets endpoint returns curated named process sets
- Backend connectivity health indicator (auto-polls every 5 s)

### 🎛️ Other Capabilities
- **Preset workloads**: Low Load, High Load, Burst Storm
- **Add / Remove / Edit** processes dynamically (up to 20)
- **CSV Export** of per-process metrics
- **Dark / Light mode** toggle
- Configurable **context-switch overhead** value (ms)

---

## 🚀 Getting Started

### 1. Backend Setup

```bash
# Navigate to the backend directory
cd context-Switching-2/backend

# Create and activate a virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS / Linux

# Install dependencies
pip install fastapi uvicorn pydantic

# Start the development server
uvicorn main:app --reload --port 8000
```

The API will be available at http://localhost:8000
Interactive docs: http://localhost:8000/docs

### 2. Frontend Setup

No build step required. Simply open the file in your browser:

```bash
# Open directly in your default browser (Windows)
start context-Switching-2/frontend/Context-Switch.html
```

> **Note:** The frontend runs scheduling algorithms locally (in-browser) by default. Click the **"⚡ Run via Backend"** button to use the FastAPI engine instead.

---

## 🌐 API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /health | Service health check |
| POST | /simulate | Run a single scheduling simulation |
| POST | /compare | Compare all three algorithms simultaneously |
| GET | /presets | Retrieve preset process configurations |

### Example — POST /simulate

```json
{
  "processes": [
    { "id": 1, "name": "P1", "arrival_time": 0, "burst_time": 6, "priority": 1 },
    { "id": 2, "name": "P2", "arrival_time": 2, "burst_time": 4, "priority": 2 }
  ],
  "algorithm": "RR",
  "quantum": 3,
  "cs_overhead_ms": 2.0
}
```

### Response (excerpt)
```json
{
  "algorithm": "RR",
  "context_switches": 3,
  "cs_overhead_total_ms": 6.0,
  "perf_loss_pct": 0.09,
  "metrics": {
    "avg_waiting_ms": 4.0,
    "avg_turnaround_ms": 8.0,
    "cpu_utilization_pct": 100.0
  }
}
```

---

## 🎨 UI Design Highlights

- **Dark-mode first** design with a deep navy (#06090f) canvas
- **Animated grid background** with slow-drifting radial orbs
- **Glassmorphism** cards with backdrop-filter: blur
- Micro-animations: pulse-glow, fadeSlideUp, cpu-run, switch-flash, bar-grow
- Monospaced **JetBrains Mono** for all numeric/code values
- Color-coded process palette — each process gets a distinct hue across the Gantt, queue, and metrics table

---

## 📋 Validation Rules

- Minimum **1 process**, maximum **20 processes** per simulation
- arrival_time >= 0; burst_time >= 1; priority >= 1
- Algorithm must be one of: FCFS, SJF, RR
- Time quantum (quantum) >= 1 (only used for RR)

---

## 📄 License

This project is released for educational and research purposes.

---

*Built with ❤️ using FastAPI + React*
