import os
import socket
from dotenv import load_dotenv

# Load .env and read robot connection settings
load_dotenv()
ROBOT_IP = os.getenv("ROBOT_IP")
ROBOT_PORT = int(os.getenv("ROBOT_PORT", "0"))
# ROBOT_TIMEOUT_MS is the send/connect timeout in milliseconds
ROBOT_TIMEOUT_MS = int(os.getenv("ROBOT_TIMEOUT_MS", "500"))


def _validate_config():
    """
    Ensure ROBOT_IP and ROBOT_PORT are set.
    """
    if not ROBOT_IP or ROBOT_PORT == 0:
        raise RuntimeError("ROBOT_IP and ROBOT_PORT must be set in .env")


def send_to_robot(payload: str) -> None:
    """
    Opens a TCP connection to the robot controller and sends the payload.
    Uses ROBOT_TIMEOUT_MS (in .env) for connect/send timeout.
    """
    _validate_config()
    timeout_sec = ROBOT_TIMEOUT_MS / 1000.0
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(timeout_sec)
        try:
            sock.connect((ROBOT_IP, ROBOT_PORT))
            if not payload.endswith("\n"):
                payload += "\n"
            sock.sendall(payload.encode("utf-8"))
            print(f"Sent payload ({len(payload)} bytes) to {ROBOT_IP}:{ROBOT_PORT}")
        except socket.timeout:
            print(f"Timeout: could not connect/send to {ROBOT_IP}:{ROBOT_PORT} within {ROBOT_TIMEOUT_MS}ms")
        except Exception as e:
            print(f"Failed to send payload to {ROBOT_IP}:{ROBOT_PORT}: {e}")
