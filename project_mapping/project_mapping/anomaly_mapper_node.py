#!/usr/bin/env python3

import math
import time
import rclpy
from rclpy.node import Node

from nav_msgs.msg import Odometry
from std_msgs.msg import Bool
from visualization_msgs.msg import Marker, MarkerArray


class AnomalyMapperNode(Node):

    def __init__(self):
        super().__init__('anomaly_mapper_node')

        # A robot aktuális pozíciója az /odom topic alapján
        self.current_x = 0.0
        self.current_y = 0.0

        # Az eltárolt anomáliák listája
        self.anomalies = []

        # Ha egy új detektálás ennél közelebb van egy régi anomáliához,
        # akkor ugyanannak az anomáliának tekintjük
        self.match_distance = 0.35

        self.forward_offset = 0.28
        self.current_yaw = 0.0

        self.break_cooldown = False

        # Feliratkozás az odometriára
        self.odom_subscriber = self.create_subscription(
            Odometry,
            '/odom',
            self.odom_callback,
            10
        )

        # Feliratkozás a szakadás/anomália detektálás topicra
        self.break_subscriber = self.create_subscription(
            Bool,
            '/break_detected',
            self.break_callback,
            10
        )

        # Feliratkozás a kör vége topicra
        self.lap_finished_subscriber = self.create_subscription(
            Bool,
            '/lap_finished',
            self.lap_finished_callback,
            10
        )

        # RViz marker publisher
        self.marker_publisher = self.create_publisher(
            MarkerArray,
            '/anomaly_markers',
            10
        )

        self.get_logger().info(
            'Anomaly mapper node started. Listening to /odom, /break_detected and /lap_finished...'
        )

    def odom_callback(self, msg):

        # A robot aktuális pozíciójának mentése
        self.current_x = msg.pose.pose.position.x
        self.current_y = msg.pose.pose.position.y

        q = msg.pose.pose.orientation

        sin_yaw = 2.0 * (q.w * q.z + q.x * q.y)
        cos_yaw = 1.0 - 2.0 * (q.y * q.y + q.z * q.z)

        self.current_yaw = math.atan2(sin_yaw, cos_yaw)

    def break_callback(self, msg):

        # False üzenetek ignorálása
        if not msg.data:
            return
        # Cooldown alatt ignoráljuk az új True-kat
        if self.break_cooldown:
            return

        # Cooldown aktiválása
        self.break_cooldown = True

        # Megnézzük van-e már ismert anomália a közelben
        break_x = self.current_x + self.forward_offset * math.cos(self.current_yaw)
        break_y = self.current_y + self.forward_offset * math.sin(self.current_yaw)
        
        existing_anomaly = self.find_nearby_anomaly(
        break_x,
        break_y
        )       

        if existing_anomaly is not None:

            # Korábbi anomália újra detektálva ebben a körben
            existing_anomaly["active"] = True
            existing_anomaly["seen_this_lap"] = True

            self.get_logger().info(
                f'KNOWN BREAK SEEN AGAIN AT x={self.current_x:.2f}, y={self.current_y:.2f}'
            )

        else:

            # Új anomália létrehozása
            new_anomaly = {
                "x": break_x,
                "y": break_y,
                "active": True,
                "seen_this_lap": True
            }

            self.anomalies.append(new_anomaly)

            self.get_logger().info(
                f'NEW BREAK DETECTED AT x={break_x:.2f}, y={break_y:.2f}'
            )

        self.publish_markers()


        time.sleep(10.0)

        self.break_cooldown = False 

    def lap_finished_callback(self, msg):

        # False üzenetek ignorálása
        if not msg.data:
            return

        self.get_logger().info(
            'LAP FINISHED. Updating anomaly states...'
        )

        for anomaly in self.anomalies:

            # Ha korábban aktív volt,
            # de ebben a körben már nem láttuk újra,
            # akkor eltűntnek tekintjük
            if anomaly["active"] and not anomaly["seen_this_lap"]:

                anomaly["active"] = False

                self.get_logger().info(
                    f'BREAK DISAPPEARED AT x={anomaly["x"]:.2f}, y={anomaly["y"]:.2f}'
                )

            # Következő körre reseteljük
            anomaly["seen_this_lap"] = False

        self.publish_markers()

    def find_nearby_anomaly(self, x, y):

        # Megkeressük van-e már ismert anomália a közelben
        for anomaly in self.anomalies:

            dx = anomaly["x"] - x
            dy = anomaly["y"] - y

            distance = math.sqrt(dx * dx + dy * dy)

            if distance < self.match_distance:
                return anomaly

        return None

    def publish_markers(self):

        marker_array = MarkerArray()

        for i, anomaly in enumerate(self.anomalies):

            marker = Marker()

            marker.header.frame_id = 'odom'
            marker.header.stamp = self.get_clock().now().to_msg()

            marker.ns = 'anomalies'
            marker.id = i
            marker.type = Marker.SPHERE
            marker.action = Marker.ADD

            marker.pose.position.x = anomaly["x"]
            marker.pose.position.y = anomaly["y"]
            marker.pose.position.z = 0.1

            marker.pose.orientation.w = 1.0

            marker.scale.x = 0.2
            marker.scale.y = 0.2
            marker.scale.z = 0.2

            # Marker színek:
            # active=True  -> piros = aktív / jelenlegi szakadás
            # active=False -> kék = eltűnt / korábbi szakadás

            if anomaly["active"]:

                marker.color.r = 1.0
                marker.color.g = 0.0
                marker.color.b = 0.0

            else:

                marker.color.r = 0.0
                marker.color.g = 0.0
                marker.color.b = 1.0

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