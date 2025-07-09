# proxy.py
import os
import sys
import argparse
import threading
import time
import subprocess

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
        self.subscription  # prevent unused variable warning

    def listener_callback(self, msg: String):
        if msg.data == 'test':
            self.get_logger().info('test robot arm')
            self.run_test_sequence()
        else:
            self.get_logger().info('unrecognized command')

    def run_test_sequence(self):
        # 1) Generate the CSV payload
        csv_payload = make_circle_commands(radius=100)
        self.get_logger().info(f"Generated CSV payload:\n{csv_payload}")

        if self.dry_run:
            self.get_logger().info("Dry run enabled; not sending to robot.")
            return

        # 2) Load robot IP/PORT from .env
        try:
            ip, port = load_config()
        except Exception as e:
            self.get_logger().error(f"Configuration error: {e}")
            return

        # 3) Send the payload
        try:
            send_to_robot(ip, port, csv_payload)
            self.get_logger().info(f"Payload sent to {ip}:{port}")
        except Exception as e:
            self.get_logger().error(f"Failed to send payload: {e}")

def self_trigger_loop():
    cmd = [
        sys.executable, '-m', 'ros2', 'topic', 'pub',
        '/abb_proxy', 'std_msgs/String', '{data: "test"}', '--once'
    ]
    while True:
        subprocess.run(cmd)
        time.sleep(60)

def main(args=None):
    parser = argparse.ArgumentParser(description="ROS2 proxy for ABB commands")
    parser.add_argument('--dry-run', action='store_true',
                        help="Only generate and log CSV; do not send over TCP")
    parser.add_argument('--self-trigger', action='store_true',
                        help="Every 60s, publish a test command to /abb_proxy")
    known, remaining = parser.parse_known_args()

    # start self-trigger thread if requested
    if known.self_trigger:
        t = threading.Thread(target=self_trigger_loop, daemon=True)
        t.start()

    rclpy.init(args=[sys.argv[0]] + remaining)
    node = DeviceNode(dry_run=known.dry_run)
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
