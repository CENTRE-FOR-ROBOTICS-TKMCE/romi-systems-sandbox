import rclpy
from geometry_msgs.msg import Twist
from rclpy.node import Node
from sensor_msgs.msg import JointState
from std_msgs.msg import Float64


class PIDController:
    def __init__(self, kp, ki, kd, output_limit,integral_limit):
        self.kp = kp
        self.ki = ki
        self.kd = kd
        self.output_limit = abs(output_limit)
        self.integral_limit = integral_limit

        self.integral = 0.0
        self.previous_measurement = 0.0
        self.has_previous_measurement = False

    def update(self, setpoint, measurement, dt):
        error = setpoint - measurement
        self.integral += error * dt

        # Anti-wind up: Clamp the integral term to prevent excessive accumulation
        self.integral = max(
            -self.integral_limit,
            min(self.integral_limit, self.integral)
        )

        # Compute the derivative term based on the change in measurement
        derivative = 0.0
        if self.has_previous_measurement and dt > 0.0:
            derivative = -(measurement - self.previous_measurement) / dt

        output = (
            self.kp * error
            + self.ki * self.integral
            + self.kd * derivative
        )

        output = max(-self.output_limit, min(self.output_limit, output))
        self.previous_measurement = measurement
        self.has_previous_measurement = True
        p_term = self.kp * error
        i_term = self.ki * self.integral
        d_term = self.kd * derivative

        output = p_term + i_term + d_term

        print(
            f"error={error:.3f}, "
            f"P={p_term:.3f}, "
            f"I={i_term:.3f}, "
            f"D={d_term:.3f}, "
            f"output={output:.3f}"
        )
        return output

    def reset(self):
        self.integral = 0.0
        self.previous_measurement = 0.0
        self.has_previous_measurement = False


class PIDWheelController(Node):
    def __init__(self):
        super().__init__('pid_wheel_controller')
        self.declare_parameter('wheel_radius', 0.0345)
        self.declare_parameter('wheel_separation', 0.140)
        self.declare_parameter('left_joint_name', 'wheel_left_joint')
        self.declare_parameter('right_joint_name', 'wheel_right_joint')
        self.declare_parameter('control_rate', 20.0)
        self.declare_parameter('cmd_vel_timeout', 0.5)
        self.declare_parameter('joint_state_timeout', 0.5)
        self.declare_parameter('stopped_velocity_tolerance', 0.05)
        self.declare_parameter('kp', 0.2)
        self.declare_parameter('ki', 0.5)
        self.declare_parameter('kd', 0.0)
        self.declare_parameter('max_output', 1.0)
        self.declare_parameter('integral_limit', 2.0)

        self.wheel_radius = self.get_parameter('wheel_radius').value
        self.wheel_separation = self.get_parameter('wheel_separation').value
        self.left_joint_name = self.get_parameter('left_joint_name').value
        self.right_joint_name = self.get_parameter('right_joint_name').value

        kp = self.get_parameter('kp').value
        ki = self.get_parameter('ki').value
        kd = self.get_parameter('kd').value
        max_output = self.get_parameter('max_output').value
        integral_limit = self.get_parameter('integral_limit').value
        self.left_pid = PIDController(kp, ki, kd, max_output, integral_limit)
        self.right_pid = PIDController(kp, ki, kd, max_output, integral_limit)

        self.target_left_wheel_speed = 0.0
        self.target_right_wheel_speed = 0.0
        self.actual_left_wheel_speed = 0.0
        self.actual_right_wheel_speed = 0.0
        self.last_control_time = self.get_clock().now()
        self.last_cmd_vel_time = self.get_clock().now()
        self.last_joint_state_time = self.get_clock().now()
        self.cmd_vel_timeout = self.get_parameter('cmd_vel_timeout').value
        self.joint_state_timeout = self.get_parameter('joint_state_timeout').value
        self.stopped_velocity_tolerance = (
            self.get_parameter('stopped_velocity_tolerance').value
        )

        self.subscription = self.create_subscription(
            Twist,
            'cmd_vel',
            self.cmd_vel_callback,
            10
        )
        self.joint_state_subscription = self.create_subscription(
            JointState,
            'joint_states',
            self.joint_state_callback,
            10
        )
        self.left_motor_publisher = self.create_publisher(
            Float64,
            'left_motor_command',
            10
        )
        self.right_motor_publisher = self.create_publisher(
            Float64,
            'right_motor_command',
            10
        )
        self.left_correction_publisher = self.create_publisher(
            Float64,
            'left_motor_correction',
            10
        )
        self.right_correction_publisher = self.create_publisher(
            Float64,
            'right_motor_correction',
            10
        )

        control_rate = max(1.0, self.get_parameter('control_rate').value)
        self.control_timer = self.create_timer(
            1.0 / control_rate,
            self.control_loop
        )

    def cmd_vel_callback(self, msg):
        linear_velocity = msg.linear.x
        angular_velocity = msg.angular.z

        left_wheel_linear_velocity = (
            linear_velocity
            - angular_velocity * self.wheel_separation / 2.0
        )
        right_wheel_linear_velocity = (
            linear_velocity
            + angular_velocity * self.wheel_separation / 2.0
        )

        self.target_left_wheel_speed = (
            left_wheel_linear_velocity / self.wheel_radius
        )
        self.target_right_wheel_speed = (
            right_wheel_linear_velocity / self.wheel_radius
        )
        self.last_cmd_vel_time = self.get_clock().now()

        if self._is_zero(linear_velocity) and self._is_zero(angular_velocity):
            self.target_left_wheel_speed = 0.0
            self.target_right_wheel_speed = 0.0
            self.left_pid.reset()
            self.right_pid.reset()

    def joint_state_callback(self, msg):
        updated_wheel_speed = False
        for index, name in enumerate(msg.name):
            if index >= len(msg.velocity):
                continue

            if name == self.left_joint_name:
                self.actual_left_wheel_speed = msg.velocity[index]
                updated_wheel_speed = True
            elif name == self.right_joint_name:
                self.actual_right_wheel_speed = msg.velocity[index]
                updated_wheel_speed = True

        if updated_wheel_speed:
            self.last_joint_state_time = self.get_clock().now()

    def control_loop(self):
        now = self.get_clock().now()
        dt = (now - self.last_control_time).nanoseconds / 1e9
        self.last_control_time = now

        if dt <= 0.0:
            return

        time_since_cmd_vel = (now - self.last_cmd_vel_time).nanoseconds / 1e9
        if time_since_cmd_vel > self.cmd_vel_timeout:
            self.target_left_wheel_speed = 0.0
            self.target_right_wheel_speed = 0.0
            self.left_pid.reset()
            self.right_pid.reset()

        time_since_joint_state = (
            now - self.last_joint_state_time
        ).nanoseconds / 1e9
        target_is_stopped = (
            self._is_zero(self.target_left_wheel_speed)
            and self._is_zero(self.target_right_wheel_speed)
        )
        feedback_is_stale = time_since_joint_state > self.joint_state_timeout
        wheels_are_stopped = (
            abs(self.actual_left_wheel_speed) <= self.stopped_velocity_tolerance
            and abs(self.actual_right_wheel_speed) <= self.stopped_velocity_tolerance
        )

        if target_is_stopped and (feedback_is_stale or wheels_are_stopped):
            self.left_pid.reset()
            self.right_pid.reset()
            self.left_motor_publisher.publish(Float64(data=0.0))
            self.right_motor_publisher.publish(Float64(data=0.0))
            self.left_correction_publisher.publish(Float64(data=0.0))
            self.right_correction_publisher.publish(Float64(data=0.0))
            return

        left_correction = self.left_pid.update(
            self.target_left_wheel_speed,
            self.actual_left_wheel_speed,
            dt
        )
        right_correction = self.right_pid.update(
            self.target_right_wheel_speed,
            self.actual_right_wheel_speed,
            dt
        )
        left_command = self.target_left_wheel_speed + left_correction 
        right_command = self.target_right_wheel_speed + right_correction 

        self.left_motor_publisher.publish(Float64(data=left_command))
        self.right_motor_publisher.publish(Float64(data=right_command))
        self.left_correction_publisher.publish(Float64(data=left_correction))
        self.right_correction_publisher.publish(Float64(data=right_correction))

    def _is_zero(self, value):
        return abs(value) <= 1e-6


def main(args=None):
    rclpy.init(args=args)
    pid_wheel_controller = PIDWheelController()
    rclpy.spin(pid_wheel_controller)
    pid_wheel_controller.destroy_node()
    rclpy.shutdown()
