"""Everything in one command: Gazebo Harmonic sim, RViz2, and the D-pad GUI controller.

    ros2 launch romi_bringup sim_with_controller.launch.py
"""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node


def generate_launch_description():
    pkg_gazebo = get_package_share_directory('romi_gazebo')

    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_gazebo, 'launch', 'gazebo.launch.py')
        ),
    )

    gui_controller = Node(
        package='romi_teleop',
        executable='gui_controller',
        name='romi_gui_controller',
        output='screen',
    )

    wheel_pid_controller = Node(
        package='wheel_pid_controller',
        executable='wheel_pid_controller',
        name='wheel_pid_controller',
        output='screen',
    )

    return LaunchDescription([
        gazebo,
        gui_controller,
        wheel_pid_controller
    ])
