#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from std_msgs.msg import Float32

class StableLineFollower(Node):
    def __init__(self):
        super().__init__('stable_line_follower')
        self.cmd_vel_pub = self.create_publisher(Twist, '/cmd_vel', 10)
        self.error_sub = self.create_subscription(Float32, '/line_error', self.error_callback, 10)
        self.Kp = 0.006  
        self.Kd = 0.002  
        self.base_speed = 0.15   
        self.max_angular = 1.0   
        self.last_error = 0.0
        self.get_logger().info('Project Control: Stabil PD Line Follower Node elindult!')

    def error_callback(self, msg):
        error = msg.data
        twist = Twist()
        if error == -999.0:
            twist.linear.x = 0.0
            twist.angular.z = 0.0
            self.get_logger().warn('Vonal elveszett! Megállás.')
        else:
            error_deriv = error - self.last_error
            angular_velocity = -1.0 * (self.Kp * error + self.Kd * error_deriv)
            angular_velocity = max(min(angular_velocity, self.max_angular), -self.max_angular)
            twist.linear.x = self.base_speed * (1.0 - min(abs(angular_velocity)/self.max_angular, 0.6))
            twist.angular.z = angular_velocity
            self.last_error = error
        self.cmd_vel_pub.publish(twist)

def main(args=None):
    rclpy.init(args=args)
    node = StableLineFollower()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        stop_twist = Twist()
        node.cmd_vel_pub.publish(stop_twist)
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
