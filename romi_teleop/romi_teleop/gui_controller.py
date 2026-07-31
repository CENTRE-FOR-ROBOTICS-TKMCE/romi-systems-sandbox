#!/usr/bin/env python3
"""Front / Back / Left / Right D-pad controller for Romi.

A small Tkinter window with four directional buttons. Press and hold a
button to drive; release it and the robot stops. Publishes
geometry_msgs/Twist on /cmd_vel.

    ros2 run romi_teleop gui_controller
"""

import threading
import tkinter as tk

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist

TICK_MS = 100  # how often we re-publish while a button is held


class RomiGuiController(Node):

    def __init__(self):
        super().__init__('romi_gui_controller')
        self.declare_parameter('linear_speed', 0.20)   # m/s   (Romi max ~0.22)
        self.declare_parameter('angular_speed', 1.50)  # rad/s (Romi max ~2.84)

        self.linear_speed = float(self.get_parameter('linear_speed').value)
        self.angular_speed = float(self.get_parameter('angular_speed').value)

        self.publisher = self.create_publisher(Twist, 'cmd_vel', 10)
        self.active_direction = None

    def twist_for(self, direction):
        twist = Twist()
        if direction == 'forward':
            twist.linear.x = self.linear_speed
        elif direction == 'backward':
            twist.linear.x = -self.linear_speed
        elif direction == 'left':
            twist.angular.z = self.angular_speed
        elif direction == 'right':
            twist.angular.z = -self.angular_speed
        return twist

    def press(self, direction):
        self.active_direction = direction
        self.publisher.publish(self.twist_for(direction))

    def release(self):
        self.active_direction = None
        self.publisher.publish(Twist())

    def tick(self):
        """Called on a timer so the command keeps flowing while held."""
        if self.active_direction is not None:
            self.publisher.publish(self.twist_for(self.active_direction))


class ControllerWindow:

    def __init__(self, node: RomiGuiController):
        self.node = node

        self.root = tk.Tk()
        self.root.title('Romi Controller')
        self.root.protocol('WM_DELETE_WINDOW', self.on_close)

        pad = {'width': 8, 'height': 3, 'font': ('Sans', 14, 'bold')}

        grid = tk.Frame(self.root, padx=10, pady=10)
        grid.pack()

        self._make_hold_button(grid, '\u2191\nForward', 'forward', pad).grid(row=0, column=1)
        self._make_hold_button(grid, '\u2190\nLeft', 'left', pad).grid(row=1, column=0)
        self._make_stop_button(grid, pad).grid(row=1, column=1)
        self._make_hold_button(grid, '\u2192\nRight', 'right', pad).grid(row=1, column=2)
        self._make_hold_button(grid, '\u2193\nBack', 'backward', pad).grid(row=2, column=1)

        speed_frame = tk.Frame(self.root, padx=10, pady=5)
        speed_frame.pack(fill='x', pady=(0, 10))

        tk.Label(speed_frame, text='Linear speed (m/s)').grid(row=0, column=0, sticky='w')
        self.linear_scale = tk.Scale(
            speed_frame, from_=0.0, to=0.22, resolution=0.01, orient='horizontal',
            command=self._on_linear_change, length=220,
        )
        self.linear_scale.set(node.linear_speed)
        self.linear_scale.grid(row=0, column=1)

        tk.Label(speed_frame, text='Angular speed (rad/s)').grid(row=1, column=0, sticky='w')
        self.angular_scale = tk.Scale(
            speed_frame, from_=0.0, to=2.84, resolution=0.1, orient='horizontal',
            command=self._on_angular_change, length=220,
        )
        self.angular_scale.set(node.angular_speed)
        self.angular_scale.grid(row=1, column=1)

        self.status_label = tk.Label(self.root, text='stopped', fg='gray')
        self.status_label.pack(pady=(0, 10))

        self._tick()

    def _make_hold_button(self, parent, text, direction, pad):
        button = tk.Button(parent, text=text, **pad)
        button.bind('<ButtonPress-1>', lambda _evt: self._start(direction))
        button.bind('<ButtonRelease-1>', lambda _evt: self._stop())
        return button

    def _make_stop_button(self, parent, pad):
        button = tk.Button(parent, text='STOP', bg='#c0392b', fg='white', **pad)
        button.bind('<ButtonPress-1>', lambda _evt: self._stop())
        return button

    def _start(self, direction):
        self.node.press(direction)
        self.status_label.config(text=f'driving: {direction}', fg='#27ae60')

    def _stop(self):
        self.node.release()
        self.status_label.config(text='stopped', fg='gray')

    def _on_linear_change(self, value):
        self.node.linear_speed = float(value)

    def _on_angular_change(self, value):
        self.node.angular_speed = float(value)

    def _tick(self):
        self.node.tick()
        self.root.after(TICK_MS, self._tick)

    def on_close(self):
        self.node.release()
        self.root.destroy()

    def run(self):
        self.root.mainloop()


def main(args=None):
    rclpy.init(args=args)
    node = RomiGuiController()

    # spin rclpy on a background thread; Tkinter owns the main thread
    spin_thread = threading.Thread(target=rclpy.spin, args=(node,), daemon=True)
    spin_thread.start()

    window = ControllerWindow(node)
    try:
        window.run()
    finally:
        node.release()
        rclpy.shutdown()
        spin_thread.join(timeout=1.0)


if __name__ == '__main__':
    main()
