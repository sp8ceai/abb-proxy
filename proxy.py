# proxy.py
import os
import sys
import argparse
import threading
import time
import subprocess
import signal

import rclpy
from rclpy.node import Node
from std_msgs.msg import String

# Direct imports from test.py
from test import load_config, make_circle_commands, send_to_robot

class DeviceNode(Node):
    def __init__(self, dry_run: bool):
        super().__init__('device_node')
        self.dry_run = dry_run

        self.subscription = self.create_subscription(
            String,
            'abb_proxy',
            self.listener_callback,
            10
        )
        self.subscription

    def listener_callback(self, msg: String):
        if msg.data == 'test':
            self.get_logger().info('test robot arm')
            self.run_test_sequence()
        else:
            self.get_logger().info('unrecognized command')

    def run_test_sequence(self):
        csv_payload = make_circle_commands(radius=100)
        self.get_logger().info(f"Generated CSV payload:\n{csv_payload}")

        if self.dry_run:
            self.get_logger().info("Dry run enabled; not sending to robot.")
            return

        try:
            ip, port = load_config()
        except Exception as e:
            self.get_logger().error(f"Configuration error: {e}")
            return

        try:
            send_to_robot(ip, port, csv_payload)
            self.get_logger().info(f"Payload sent to {ip}:{port}")
        except Exception as e:
            self.get_logger().error(f"Failed to send payload: {e}")

def self_trigger_loop(stop_event: threading.Event):
    cmd = [
        "ros2", "topic", "pub",
        "/abb_proxy", "std_msgs/String",
        "{data: 'test'}", "--once"
    ]
    while not stop_event.is_set():
        subprocess.run(cmd)
        # wait with early exit support
        for _ in range(60):
            if stop_event.is_set():
                break
            time.sleep(1)

def main():
    parser = argparse.ArgumentParser(description="ROS2 proxy for ABB commands")
    parser.add_argument('--dry-run', action='store_true',
                        help="Only generate and log CSV; do not send over TCP")
    parser.add_argument('--self-trigger', action='store_true',
                        help="Publish a test message every 60s")
    args, remaining = parser.parse_known_args()

    # Prepare shutdown event
    stop_event = threading.Event()

    # Start self-trigger thread if requested
    if args.self_trigger:
        thread = threading.Thread(target=self_trigger_loop, args=(stop_event,), daemon=True)
        thread.start()

    # Ensure that Ctrl+C in the main thread will also stop our loop
    def shutdown_handler(signum, frame):
        stop_event.set()
        rclpy.shutdown()
    signal.signal(signal.SIGINT, shutdown_handler)
    signal.signal(signal.SIGTERM, shutdown_handler)

    # Init and spin ROS2
    rclpy.init(args=[sys.argv[0]] + remaining)
    node = DeviceNode(dry_run=args.dry_run)
    try:
        rclpy.spin(node)
    finally:
        # Mark the thread to stop and wait briefly
        stop_event.set()
        node.destroy_node()

if __name__ == '__main__':
    main()
