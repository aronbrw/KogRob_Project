#!/usr/bin/env python3

import math

import rclpy
from rclpy.node import Node

from nav_msgs.msg import Odometry
from std_msgs.msg import Bool


class LapDetectorNode(Node):

    def __init__(self):
        super().__init__('lap_detector_node')

        self.min_x = -0.2
        self.max_x = 0.2

        self.min_y = -0.2
        self.max_y = 0.2

        self.armed = True
        self.lap_count = 0

        self.odom_subscriber = self.create_subscription(
            Odometry,
            '/odom',
            self.odom_callback,
            10
        )

        self.lap_publisher = self.create_publisher(
            Bool,
            '/lap_finished',
            10
        )

        self.get_logger().info('Lap detector started.')

    def odom_callback(self, msg):
        x = msg.pose.pose.position.x
        y = msg.pose.pose.position.y

        inside_start_zone = (
            self.min_x <= x <= self.max_x
            and
            self.min_y <= y <= self.max_y
        )

        if not inside_start_zone:
            self.armed = True

        if inside_start_zone and self.armed:
            self.lap_count += 1
            self.armed = False

            for _ in range(5):
                lap_msg = Bool()
                lap_msg.data = True
                self.lap_publisher.publish(lap_msg)

            self.get_logger().info(
                f'LAP FINISHED! lap_count={self.lap_count}'
            )


def main(args=None):
    rclpy.init(args=args)

    node = LapDetectorNode()
    rclpy.spin(node)

    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
