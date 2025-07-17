#!/usr/bin/env python3
import sys
import argparse
import threading
import time
import subprocess
import signal

import rclpy
from rclpy.node import Node
from std_msgs.msg import String

from interpreter import interpret_command
from sender import send_to_robot


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

    def listener_callback(self, msg: String):
        cmd = msg.data.strip()
        self.get_logger().info(f"Received command: '{cmd}'")
        csv_payload = interpret_command(cmd)
        self.get_logger().info(f"CSV Payload:\n{csv_payload}")

        if self.dry_run:
            self.get_logger().info("Dry run enabled; not sending to robot.")
            return

        try:
            send_to_robot(csv_payload)
            self.get_logger().info("Payload sent successfully.")
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
        for _ in range(60):
            if stop_event.is_set():
                break
            time.sleep(1)


def main():
    parser = argparse.ArgumentParser(
        description="ROS2 proxy for ABB commands"
    )
    parser.add_argument(
        '--dry-run', action='store_true',
        help="Only generate/log CSV; do not send"
    )
    parser.add_argument(
        '--self-trigger', action='store_true',
        help="Publish a test message every 60s"
    )
    args, ros_args = parser.parse_known_args()

    stop_event = threading.Event()
    if args.self_trigger:
        thread = threading.Thread(
            target=self_trigger_loop,
            args=(stop_event,),
            daemon=True
        )
        thread.start()

    def shutdown_handler(signum, frame):
        stop_event.set()
        rclpy.shutdown()

    signal.signal(signal.SIGINT, shutdown_handler)
    signal.signal(signal.SIGTERM, shutdown_handler)

    rclpy.init(args=[sys.argv[0]] + ros_args)
    node = DeviceNode(dry_run=args.dry_run)
    try:
        rclpy.spin(node)
    finally:
        stop_event.set()
        node.destroy_node()


if __name__ == '__main__':
    main()
