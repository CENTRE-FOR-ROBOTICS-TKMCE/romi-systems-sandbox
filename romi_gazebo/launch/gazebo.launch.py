"""Bring up Romi in Gazebo Harmonic (gz-sim) and bridge it to ROS 2.

    ros2 launch romi_gazebo gazebo.launch.py

Starts:
  - gz-sim with the romi_world.sdf world
  - robot_state_publisher (publishes /robot_description and TF)
  - ros_gz_sim 'create', spawning the robot from /robot_description
  - ros_gz_bridge, bridging /cmd_vel, /odom, /tf, /joint_states, /scan, /clock
  - RViz2 (unless use_rviz:=false)
"""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, SetEnvironmentVariable
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import Command, LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():
    pkg_description = get_package_share_directory('romi_description')
    pkg_gazebo = get_package_share_directory('romi_gazebo')
    pkg_ros_gz_sim = get_package_share_directory('ros_gz_sim')

    xacro_file = os.path.join(pkg_description, 'urdf', 'romi.urdf.xacro')
    rviz_config = os.path.join(pkg_description, 'rviz', 'romi.rviz')
    default_world = os.path.join(pkg_gazebo, 'worlds', 'romi_world.sdf')
    bridge_config = os.path.join(pkg_gazebo, 'config', 'gz_bridge.yaml')

    world = LaunchConfiguration('world')
    use_rviz = LaunchConfiguration('use_rviz')
    use_sim_time = LaunchConfiguration('use_sim_time')
    x, y, z, yaw = LaunchConfiguration('x'), LaunchConfiguration('y'), LaunchConfiguration('z'), LaunchConfiguration('yaw')

    # so gz-sim can resolve the URDF's package://romi_description/... mesh URIs
    set_resource_path = SetEnvironmentVariable(
        'GZ_SIM_RESOURCE_PATH',
        os.path.dirname(pkg_description) + os.pathsep + os.environ.get('GZ_SIM_RESOURCE_PATH', '')
    )

    robot_description = ParameterValue(
        Command(['xacro ', xacro_file]), value_type=str
    )

    gz_sim = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_ros_gz_sim, 'launch', 'gz_sim.launch.py')
        ),
        launch_arguments={'gz_args': ['-r ', world]}.items(),
    )

    robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        name='robot_state_publisher',
        output='screen',
        parameters=[{
            'robot_description': robot_description,
            'use_sim_time': use_sim_time,
        }],
    )

    spawn_robot = Node(
        package='ros_gz_sim',
        executable='create',
        name='spawn_romi',
        output='screen',
        arguments=[
            '-topic', 'robot_description',
            '-name', 'romi',
            '-x', x, '-y', y, '-z', z, '-Y', yaw,
        ],
    )

    bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        name='ros_gz_bridge',
        output='screen',
        parameters=[{
            'config_file': bridge_config,
            'use_sim_time': use_sim_time,
        }],
    )

    rviz = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        output='screen',
        arguments=['-d', rviz_config],
        parameters=[{'use_sim_time': use_sim_time}],
        condition=IfCondition(use_rviz),
    )

    return LaunchDescription([
        DeclareLaunchArgument('world', default_value=default_world, description='Full path to a gz-sim world SDF'),
        DeclareLaunchArgument('use_rviz', default_value='true', description='Launch RViz2'),
        DeclareLaunchArgument('use_sim_time', default_value='true', description='Use /clock from Gazebo'),
        DeclareLaunchArgument('x', default_value='0.0'),
        DeclareLaunchArgument('y', default_value='0.0'),
        DeclareLaunchArgument('z', default_value='0.05'),
        DeclareLaunchArgument('yaw', default_value='0.0'),

        set_resource_path,
        gz_sim,
        robot_state_publisher,
        spawn_robot,
        bridge,
        rviz,
    ])
