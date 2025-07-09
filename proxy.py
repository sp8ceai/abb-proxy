# proxy.py
import os
import sys
import argparse
import rclpy
from rclpy.node import Node
from std_msgs.msg import String

# Direct imports from test.py
from test import load_config, make_circle_commands, send_to_robot

# If connecting to a remote ROS2 domain, you may need to set DDS discovery environment variables:
# os.environ['ROS_DISCOVERY_SERVER'] = 'remote_server_ip:11811'
# os.environ['ROS_DOMAIN_ID'] = '0'

class DeviceNode(Node):
    def __init__(self, dry_run: bool):
        super().__init__('device_node')
        self.dry_run = dry_run

        self.subscription = self.create_subscription(
            String,
            'abb_proxy',      # replace with your topic
            self.listener_callback,
            10                # QoS history depth
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
            # Skip sending
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

def main(args=None):
    parser = argparse.ArgumentParser(description="ROS2 proxy for ABB commands")
    parser.add_argument('--dry-run', action='store_true',
                        help="Only generate and log CSV; do not send over TCP")
    # Allow ROS2 remapping arguments to pass through
    known, remaining = parser.parse_known_args()
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
