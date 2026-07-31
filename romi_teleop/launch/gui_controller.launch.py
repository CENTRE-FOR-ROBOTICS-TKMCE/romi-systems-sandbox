from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription([
        Node(
            package='romi_teleop',
            executable='gui_controller',
            name='romi_gui_controller',
            output='screen',
        ),
    ])
