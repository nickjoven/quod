# Liveness

A read-only, single-page local process dashboard with a sparse, 32-bit-inspired
palette, square controls, monospace typography, and CPU history charts.
Python 3.10+ on Linux or WSL; no packages, build step, or external assets.

## Run

From the repository root:

```sh
python3 tools/liveness/server.py
```

Open http://localhost:8765. Stop the server with Ctrl+C.
Use `--port 8766` for another port or repeat `--pid 1234` to filter to selected
PIDs plus recognized vacuum processes. By default all readable processes
owned by the current user are listed. Run on the same host/process namespace
as the workload; an isolated sandbox cannot see host processes.

## Meaning of readings

CPU is the change in process CPU time between HTTP samples, with one core
equal to 100%; multithreaded processes can exceed 100%. The first reading is
unavailable. Memory is resident memory, not total allocation. Identity includes
the kernel start time to distinguish PID reuse. Charts retain 60 observations
in browser memory. Pause freezes the feed; it does not pause any process.

Vacuum counts come from the run index. Its modification age is shown separately
from the completion monitor heartbeat; neither CPU activity nor a heartbeat
proves numerical progress. No per-step solver progress is inferred. Missing
files and disconnected feeds are shown explicitly. The app never invokes,
restarts, samples stacks, or changes the registered solver.

## Local access

The server binds only to IPv4 loopback, validates the Host header, exposes two
fixed read-only routes, and does not transmit command arguments or environment
variables. No external services or browser storage are used.

## Verify

```sh
python3 -m unittest discover -s tools/liveness -p 'test_*.py'
```
