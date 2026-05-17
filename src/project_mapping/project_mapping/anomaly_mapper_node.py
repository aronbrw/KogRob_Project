#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from nav_msgs.msg import Odometry


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

    def odom_callback(self, msg):
        x = msg.pose.pose.position.x
        y = msg.pose.pose.position.y

        self.get_logger().info(f'Robot position: x={x:.2f}, y={y:.2f}')


def main(args=None):
    rclpy.init(args=args)
    node = AnomalyMapperNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
