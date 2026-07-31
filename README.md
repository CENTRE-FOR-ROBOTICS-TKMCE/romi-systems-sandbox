# Romi

A ROS 2 Jazzy workspace for the [Pololu Romi](https://www.pololu.com/category/203/romi-chassis-and-accessories) differential-drive robot, with a Gazebo Harmonic simulation and simple GUI/keyboard teleop controllers.

## Packages

| Package | Description |
|---|---|
| [`romi_description`](romi_description) | URDF/xacro model, meshes, and RViz2 config for the differential-drive robot |
| [`romi_gazebo`](romi_gazebo) | Gazebo Harmonic (`gz-sim`) simulation launch, world, and ROS–GZ bridge config |
| [`romi_teleop`](romi_teleop) | GUI D-pad and terminal keyboard teleop controllers (publish `geometry_msgs/Twist` on `/cmd_vel`) |
| [`romi_bringup`](romi_bringup) | One-command bringup: simulation + RViz2 + GUI controller |

## Prerequisites

- Ubuntu 24.04
- [ROS 2 Jazzy](https://docs.ros.org/en/jazzy/Installation.html)
- Gazebo Harmonic (`gz-sim`) and the `ros_gz` bridge packages
- `python3-tk` (for the GUI teleop controller)

```bash
sudo apt install ros-jazzy-ros-gz ros-jazzy-xacro ros-jazzy-robot-state-publisher \
                  ros-jazzy-joint-state-publisher-gui ros-jazzy-rviz2 python3-tk
```

## Build

Clone this repo into the `src` directory of a colcon workspace, then build:

```bash
cd ~/ros2_ws
colcon build --symlink-install
source install/setup.bash
```

## Quick start

Launch the Gazebo simulation, RViz2, and the GUI D-pad controller in one command:

```bash
ros2 launch romi_bringup sim_with_controller.launch.py
```

## Usage

### Simulation only

```bash
ros2 launch romi_gazebo gazebo.launch.py
```

Arguments:

| Argument | Default | Description |
|---|---|---|
| `world` | `romi_gazebo/worlds/romi_world.sdf` | Full path to a `gz-sim` world SDF |
| `use_rviz` | `true` | Launch RViz2 alongside the simulation |
| `use_sim_time` | `true` | Use `/clock` from Gazebo |
| `x`, `y`, `z`, `yaw` | `0.0, 0.0, 0.05, 0.0` | Initial spawn pose |

### View the model only (no simulator)

```bash
ros2 launch romi_description display.launch.py
```

Opens the URDF in RViz2 with `joint_state_publisher_gui` sliders for the wheels — useful for sanity-checking the model.

### Teleop

GUI D-pad controller:

```bash
ros2 launch romi_teleop gui_controller.launch.py
# or
ros2 run romi_teleop gui_controller
```

Terminal keyboard controller:

```bash
ros2 run romi_teleop keyboard_controller
```

| Key | Action |
|---|---|
| `w` / `↑` | forward |
| `s` / `↓` | backward |
| `a` / `←` | turn left |
| `d` / `→` | turn right |
| space | stop |
| `q` | quit |

Both controllers expose `linear_speed` (default `0.20` m/s, max ~`0.22`) and `angular_speed` (default `1.50` rad/s, max ~`2.84`) as ROS 2 parameters.

## Topics bridged in simulation

| Topic | Type | Direction |
|---|---|---|
| `/cmd_vel` | `geometry_msgs/msg/Twist` | ROS → Gazebo |
| `/odom` | `nav_msgs/msg/Odometry` | Gazebo → ROS |
| `/tf` | `tf2_msgs/msg/TFMessage` | Gazebo → ROS |
| `/joint_states` | `sensor_msgs/msg/JointState` | Gazebo → ROS |
| `/scan` | `sensor_msgs/msg/LaserScan` | Gazebo → ROS |
| `/clock` | `rosgraph_msgs/msg/Clock` | Gazebo → ROS |

## Repository layout

```
romi/
├── romi_bringup/
│   └── launch/sim_with_controller.launch.py
├── romi_description/
│   ├── urdf/           # romi.urdf.xacro, romi.gazebo.xacro, lidar.xacro, common_properties.xacro
│   ├── meshes/          # base, wheels, caster, LiDAR
│   ├── rviz/romi.rviz
│   └── launch/display.launch.py
├── romi_gazebo/
│   ├── worlds/romi_world.sdf
│   ├── config/gz_bridge.yaml
│   └── launch/gazebo.launch.py
└── romi_teleop/
    ├── romi_teleop/gui_controller.py
    ├── romi_teleop/keyboard_controller.py
    └── launch/gui_controller.launch.py
```

## License

Apache-2.0
