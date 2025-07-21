# ABB Proxy & Test Script

This repository contains two Python scripts to integrate ROS 2 topic commands with an ABB robot controller over TCP/IP:

- **`test.py`** — builds and (optionally) sends simple circle-scan CSV commands to the robot.
- **`proxy.py`** — runs a ROS 2 node that listens on `/abb_proxy`; when it receives `"test"`, it generates (and, unless in dry-run mode, sends) the CSV via `test.py` functions.

---

## Features

- **CSV Command Generator**  
  - Approximates a circle by four straight-line segments.
  - Configurable radius and EOL terminator.
- **TCP Sender**  
  - Loads `ROBOT_IP` and `ROBOT_PORT` from a `.env` file.
  - Sends newline-terminated CSV commands over TCP.
- **ROS 2 Integration**  
  - Subscribes to `/abb_proxy` (`std_msgs/String`).
  - On `"test"`: logs “test robot arm”, then runs the circle command sequence.
  - On other data: logs “unrecognized command”.
- **Dry-Run Support**  
  - In both scripts you can enable `--dry-run` to only print CSV without opening any socket.

---

## Getting Started

### Prerequisites

- Python 3.10+
- To run proxy: ROS 2 (e.g., Foxy, Galactic, Humble) installed and sourced
- `python-dotenv` for loading `.env` files

```bash
pip install python-dotenv
```

### Run test.py

On a computer connect the ABB robot controller using tcp/ip

First chagne .env on ip and port of the robot controller


#### Command-Line Options

**`--dry-run`**
Only print the generated CSV commands; do not open a TCP connection or send anything.

**`--radius <mm>`**
Set the circle radius in millimeters (default: 100).

**`--timeout <ms>`**
Set the TCP connect/send timeout in milliseconds (default: 500).

#### Examples

```bash
python3 test.py --dry-run
python3 test.py
python3 test.py --radius 150 --timeout 1000
```

### Run proxy.py

Receive ROS2 command and send ABB commands


#### Command-Line Options

**`--dry-run`**
Only print the generated CSV commands; do not open a TCP connection or send anything.

**`--self-trigger`**
fire ros2 command to test the proxy script itself every 60s, useful for debugging.

#### Examples

```bash
python3 proxy.py
python3 proxy.py --dry-run
python3 proxy.py --self-trigger --dry-run
```

### Test on ROS2 server

```bash
ros2 topic pub /abb_proxy std_msgs/String "{data: 'test'}" --once
# → should see "[INFO] ... test robot arm"

ros2 topic pub /abb_proxy std_msgs/String "{data: 'foo'}" --once
# → should see "[INFO] ... unrecognized command"
```
