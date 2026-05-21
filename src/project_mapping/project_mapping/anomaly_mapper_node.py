#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from nav_msgs.msg import Odometry
from std_msgs.msg import Bool


class AnomalyMapperNode(Node):
    def __init__(self):
        super().__init__('anomaly_mapper_node')

        self.odom_subscriber = self.create_subscription(
            Odometry,
            '/odom',
            self.odom_callback,
            10
        )

        self.get_logger().info('Anomaly mapper node started. Listening to /odom...')

        self.current_x = 0.0
        self.current_y = 0.0

        self.break_subscriber = self.create_subscription(
            Bool,
            '/break_detected',
            self.break_callback,
            10
        )

    def odom_callback(self, msg):
        self.current_x = msg.pose.pose.position.x
        self.current_y = msg.pose.pose.position.y

        self.get_logger().info(
            f'Robot position: x={self.current_x:.2f}, y={self.current_y:.2f}'
        )

    def break_callback(self, msg):

        # If break/anomaly detected
        if msg.data:

            self.get_logger().info(
                f'BREAK DETECTED AT x={self.current_x:.2f}, y={self.current_y:.2f}'
            )


def main(args=None):
    rclpy.init(args=args)
    node = AnomalyMapperNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
