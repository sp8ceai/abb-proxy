# test.py
import os
import socket
import argparse
from dotenv import load_dotenv

def load_config():
    """
    Reads ROBOT_IP and ROBOT_PORT from .env and returns (ip, port).
    Raises RuntimeError if missing or invalid.
    """
    load_dotenv()  # expects a .env file in the same directory
    ip = os.getenv('ROBOT_IP')
    port = int(os.getenv('ROBOT_PORT', '0'))
    if not ip or port == 0:
        raise RuntimeError("ROBOT_IP and ROBOT_PORT must be set in .env")
    return ip, port

def make_circle_commands(radius=100):
    """
    Approximate a circle by 4 straight-line segments:
    Right -> Top -> Left -> Bottom -> Back to Right
    Returns a multi-line CSV string.
    """
    points = [
        ( radius,   0, 0),
        (   0,  radius, 0),
        (-radius,   0, 0),
        (   0, -radius, 0),
        ( radius,   0, 0),  # close loop
    ]
    cmds = []
    for idx, (x, y, z) in enumerate(points, start=1):
        if idx == 1:
            sx, sy, sz = points[-1]
        else:
            sx, sy, sz = points[idx-2]
        ex, ey, ez = x, y, z
        csv_str = (
            f"VisualInspection,1,"
            f"{sx},{sy},{sz},"
            f"{ex},{ey},{ez},"
            f"-100,150,EOL"
        )
        cmds.append(csv_str)
    return "\n".join(cmds)

def send_to_robot(ip: str, port: int, payload: str, timeout_ms: int = 500):
    """
    Opens a TCP connection to the robot controller and sends the payload.
    If the send or connect operation times out, prints an error.
    """
    timeout_sec = timeout_ms / 1000.0
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(timeout_sec)
        try:
            sock.connect((ip, port))
            if not payload.endswith("\n"):
                payload += "\n"
            sock.sendall(payload.encode('utf-8'))
            print(f"Sent payload ({len(payload)} bytes) to {ip}:{port}")
        except socket.timeout:
            print(f"Timeout error: could not connect/send to {ip}:{port} within {timeout_ms}ms")
        except Exception as e:
            print(f"Failed to send payload to {ip}:{port}: {e}")

def main():
    parser = argparse.ArgumentParser(description="Generate and send circle CSV commands to ABB robot")
    parser.add_argument('--dry-run', action='store_true',
                        help="Only print the CSV, do not send over TCP")
    parser.add_argument('--radius', type=int, default=100,
                        help="Circle radius in mm (default: 100)")
    parser.add_argument('--timeout', type=int, default=500,
                        help="Send/connect timeout in milliseconds (default: 500)")
    args = parser.parse_args()

    # Generate commands
    cmds = make_circle_commands(radius=args.radius)
    print("=== Generated CSV Commands ===")
    print(cmds)

    if args.dry_run:
        print("Dry run enabled; not sending to robot.")
        return

    # Send for real
    try:
        ip, port = load_config()
    except RuntimeError as e:
        print(f"Configuration error: {e}")
        return

    send_to_robot(ip, port, cmds, timeout_ms=args.timeout)

if __name__ == "__main__":
    main()
