#!/usr/bin/env python3
"""Terminal keyboard front/back/left/right controller for Romi.

Tap a key to drive one step; the robot stops on its own shortly after
you stop pressing keys (or hit space to stop immediately).

    w / up-arrow    : forward
    s / down-arrow  : backward
    a / left-arrow  : turn left
    d / right-arrow : turn right
    space           : stop
    q               : quit

    ros2 run romi_teleop keyboard_controller
"""

import sys
import select
import termios
import tty

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist

MSG = """
Romi keyboard controller
---------------------------
   w / \u2191  : forward
a  s / \u2193  d : left / backward / right
   space   : stop
   q       : quit
---------------------------
"""

WATCHDOG_SEC = 0.5  # stop automatically if no key is pressed for this long


class RomiKeyboardController(Node):

    def __init__(self):
        super().__init__('romi_keyboard_controller')
        self.declare_parameter('linear_speed', 0.20)
        self.declare_parameter('angular_speed', 1.50)
        self.linear_speed = float(self.get_parameter('linear_speed').value)
        self.angular_speed = float(self.get_parameter('angular_speed').value)
        self.publisher = self.create_publisher(Twist, 'cmd_vel', 10)

    def publish(self, linear, angular):
        twist = Twist()
        twist.linear.x = linear
        twist.angular.z = angular
        self.publisher.publish(twist)

    def stop(self):
        self.publish(0.0, 0.0)


def get_key(settings, timeout):
    tty.setraw(sys.stdin.fileno())
    ready, _, _ = select.select([sys.stdin], [], [], timeout)
    key = sys.stdin.read(1) if ready else ''
    if key == '\x1b':  # escape sequence -> arrow key
        key += sys.stdin.read(2)
    termios.tcsetattr(sys.stdin, termios.TCSADRAIN, settings)
    return key


KEY_TO_DIRECTION = {
    'w': 'forward', '\x1b[A': 'forward',
    's': 'backward', '\x1b[B': 'backward',
    'a': 'left', '\x1b[D': 'left',
    'd': 'right', '\x1b[C': 'right',
}


def main(args=None):
    settings = termios.tcgetattr(sys.stdin)
    rclpy.init(args=args)
    node = RomiKeyboardController()
    print(MSG)

    try:
        while rclpy.ok():
            key = get_key(settings, WATCHDOG_SEC)

            if key == 'q' or key == '\x03':  # q or Ctrl-C
                break
            elif key == ' ':
                node.stop()
            elif key in KEY_TO_DIRECTION:
                direction = KEY_TO_DIRECTION[key]
                if direction == 'forward':
                    node.publish(node.linear_speed, 0.0)
                elif direction == 'backward':
                    node.publish(-node.linear_speed, 0.0)
                elif direction == 'left':
                    node.publish(0.0, node.angular_speed)
                elif direction == 'right':
                    node.publish(0.0, -node.angular_speed)
            elif key == '':
                # nothing pressed within WATCHDOG_SEC -> safety stop
                node.stop()
    except Exception as exc:
        print(exc)
    finally:
        node.stop()
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, settings)
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
