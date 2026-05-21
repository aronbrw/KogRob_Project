#!/usr/bin/env python3

import rclpy
from rclpy.node import Node

from nav_msgs.msg import Odometry
from std_msgs.msg import Bool
from visualization_msgs.msg import Marker, MarkerArray


class AnomalyMapperNode(Node):

    def __init__(self):
        super().__init__('anomaly_mapper_node')

        self.current_x = 0.0
        self.current_y = 0.0
        self.anomalies = []

        self.odom_subscriber = self.create_subscription(
            Odometry,
            '/odom',
            self.odom_callback,
            10
        )

        self.break_subscriber = self.create_subscription(
            Bool,
            '/break_detected',
            self.break_callback,
            10
        )

        self.marker_publisher = self.create_publisher(
            MarkerArray,
            '/anomaly_markers',
            10
        )

        self.get_logger().info(
            'Anomaly mapper node started. Listening to /odom and /break_detected...'
        )

    def odom_callback(self, msg):
        self.current_x = msg.pose.pose.position.x
        self.current_y = msg.pose.pose.position.y

    def break_callback(self, msg):
        if msg.data:
            self.anomalies.append((self.current_x, self.current_y))

            self.get_logger().info(
                f'BREAK DETECTED AT x={self.current_x:.2f}, y={self.current_y:.2f}'
            )

            self.publish_markers()

    def publish_markers(self):
        marker_array = MarkerArray()

        for i, (x, y) in enumerate(self.anomalies):
            marker = Marker()

            marker.header.frame_id = 'odom'
            marker.header.stamp = self.get_clock().now().to_msg()

            marker.ns = 'anomalies'
            marker.id = i
            marker.type = Marker.SPHERE
            marker.action = Marker.ADD

            marker.pose.position.x = x
            marker.pose.position.y = y
            marker.pose.position.z = 0.1

            marker.pose.orientation.w = 1.0

            marker.scale.x = 0.2
            marker.scale.y = 0.2
            marker.scale.z = 0.2

            marker.color.r = 1.0
            marker.color.g = 0.0
            marker.color.b = 0.0
            marker.color.a = 1.0

            marker_array.markers.append(marker)

        self.marker_publisher.publish(marker_array)


def main(args=None):
    rclpy.init(args=args)
    node = AnomalyMapperNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()