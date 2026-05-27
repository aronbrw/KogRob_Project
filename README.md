# Line following and break/anomaly detection using a neural network.
Team members:
Szabados Tibor Balázs
Veisz Andor
Istvándi Soma
Barna Áron
Prokob András Benedek

## Table of Contents

- [Project Demonstration Video](#project-demonstration-video)
- [Installation](#installation)
- [Running the Project](#running-the-project)
- [Simulation](#simulation---simulation_bringup_line_followlaunchpy)
- [Line Following and Break Detecting](#line-following-and-break-detecting---break_detector_nn)
- [Gazebo World](#gazebo-world---palya_finalsdf)
- [Lap Detector Module](#lap-detector-module---lap_detector_node)
- [Project Mapping Module](#project-mapping-module--anomaly_mapper_node)
- [Used ROS Packages](#used-ros-packages)
- [External Repositories](#external-repositories)

## Project Demonstration Video

You can watch the demo video of the project here:
[Project Demonstration Video](https://youtu.be/txEczfp6hIs)

## Installation

### Requirements

The project was developed and tested using:

- Ubuntu 24.04
- ROS2 Jazzy
- Gazebo Harmonic
- Rviz

---

### Install TurtleBot3 Packages

Install the required TurtleBot3 packages:

```bash
sudo apt update

sudo apt install ros-jazzy-turtlebot3 \
ros-jazzy-turtlebot3-msgs \
ros-jazzy-turtlebot3-simulations
```

---

### Clone the MOGI ROS Educational Repository

The project depends on the MOGI ROS educational packages:

```bash
git clone https://github.com/MOGI-ROS/Week-1-8-Cognitive-robotics.git
```

---

### Clone This Repository

Clone the project repository into your ROS2 workspace:

```bash
cd ~/ros2_ws/src

git clone https://github.com/aronbrw/KogRob_Project.git
```

---

### Build the Workspace

```bash
cd ~/ros2_ws

colcon build
```

---

### Source the Workspace

```bash
source install/setup.bash
```

To make sourcing permanent:

```bash
echo "source ~/ros2_ws/install/setup.bash" >> ~/.bashrc
source ~/.bashrc
```
## Running the Project

Start the simulation:

```bash
ros2 launch turtlebot3_mogi simulation_bringup_line_follow.launch.py world:=palya_final.sdf
```
After the simulation has started, open separate terminals and run the required nodes:

### Break Detector Node

```bash
ros2 run turtlebot3_mogi_py break_detector_NN
```

### Lap Detector Node

```bash
ros2 run project_mapping lap_detector_node
```
### Mapping node

```bash
ros2 run project_mapping lap_detector_node
```

## Simulation - simulation_bringup_line_follow.launch.py

The complete simulation environment is initialized using a ROS2 launch file. The purpose of the launch file is to automatically start all required system components with a single command, including:

- Gazebo simulation environment
- TurtleBot3 robot model
- world file (track)
- robot initial position
- robot state publisher nodes
- trajectory server

The simulation can be started with:

```bash
ros2 launch turtlebot3_mogi simulation_bringup_line_follow.launch.py world:=palya_final.sdf
```

Using the `world:=palya_final.sdf` parameter, the custom-made track used in the project can be loaded into the simulation.

## Line following and break detecting - break_detector_NN

The camera image first goes through an image processing pipeline. The program extracts the lightness channel from the RGB image, inverts it, and applies a trapezoidal mask so that only the region where the track/line is expected remains visible.
After this, thresholding is applied to create a binary image:
- the line becomes white,
- the background becomes black.
The middle region of the binary image is then analyzed, since under normal conditions the line should appear there. This middle area is divided into three horizontal rectangular regions:

- `UP` → upper / farther line segment
- `MID` → middle section
- `LOW` → lower / closer line segment

The number of white pixels is counted in each rectangle. These values become the three input features of the neural network:

- `upper_pixels`
- `middle_pixels`
- `lower_pixels`

The neural network therefore does not process the full image directly, but instead works with these extracted numerical features.

During training, the training script generates random sample values and labels them according to a predefined rule. A break is considered present when the upper and lower regions contain many white pixels, while the middle region contains significantly fewer.

The exact rule used for generating the labels is:

```python
upper > 1300
middle > 5000
lower > 3000
```

A break is detected if:

- `upper` is true,
- `lower` is true,
- but `middle` is false.

The classifier itself is a small MLP (Multi-Layer Perceptron) neural network with two hidden layers containing 8 neurons each.

Before classification, a `StandardScaler` normalizes the input features so that the network can learn more reliably from pixel counts with different magnitudes.

During runtime, the processing pipeline works as follows:

```text
camera image
    ↓
binary image
    ↓
UP/MID/LOW white pixel counts
    ↓
neural network
    ↓
break / no break decision
```

The network output is binary:

- `0` → no break detected
- `1` → break detected

For example:

```text
UP   = 2000
MID  = 800
LOW  = 4500
```

In this case, the line is visible in the upper and lower regions but disappears in the middle region, therefore the network classifies the situation as a break.

## Gazebo World - palya_final.sdf

The Gazebo world consists of a white ground surface and multiple movable flat black boxes. These boxes have no collision, therefore the robot does not
collide with the boxes, only detects them visually as black lines

By manually moving the shorter boxes, breaks in the track can be dynamically created or removed while the robot is moving.
<img width="530" height="461" alt="image" src="https://github.com/user-attachments/assets/7bdb4dc9-3366-436c-b79d-e87f28ed6972" />

## Lap Detector Module - 'lap_detector_node'

The purpose of the lap detector node is to detect when the robot has completed a full lap.
The node publishes this information to a topic and also keeps track of the completed lap count in the terminal output.

In the node's code, we can define a rectangular area that acts as the start/finish zone.
Whenever the robot enters this area, the node registers a completed lap.
The robot's current position is obtained from the `/odom` topic and continuously monitored.

When the robot completes a lap, the node publishes a `True` boolean value to the `/lap_finished` topic,
which is then read by the anomaly mapper node.

## Project Mapping Module — `anomaly_mapper_node`

The purpose of the `project_mapping` module is to visualize and track detected line breaks/anomalies during line following in RViz.

The `anomaly_mapper_node` monitors:

- the robot’s current position (`/odom`),
- the break detector output (`/break_detected`),
- and lap completion events (`/lap_finished`).

The node stores the positions of detected anomalies and publishes them as RViz markers.

### Operation

When the `/break_detected` topic publishes `True`:

1. The node reads the robot’s current position and orientation.
2. It calculates the estimated break position in front of the robot camera.
3. It checks whether a previously known anomaly already exists nearby.
4. If no nearby anomaly exists:
   - a new anomaly is created.
5. If a nearby anomaly already exists:
   - the existing anomaly is reactivated.

The anomaly states are updated after each completed lap.

The `/lap_finished` topic signals the end of a full lap. At this point:

- anomalies that were not detected again during the current lap
  become inactive.

This allows the system to distinguish between:

- currently active line breaks,
- and previously detected but disappeared anomalies.

### RViz Marker Colors

| Color | Meaning |
|---|---|
| 🔴 Red | Active / currently visible anomaly |
| 🔵 Blue | Previously detected but disappeared anomaly |

### Used Topics

#### Subscribed Topics

| Topic | Type | Purpose |
|---|---|---|
| `/odom` | `nav_msgs/Odometry` | Robot position and orientation |
| `/break_detected` | `std_msgs/Bool` | Break detection signal |
| `/lap_finished` | `std_msgs/Bool` | End-of-lap signal |

#### Published Topic

| Topic | Type | Purpose |
|---|---|---|
| `/anomaly_markers` | `visualization_msgs/MarkerArray` | RViz marker visualization |

### Testing

The module was tested manually using ROS2 topic publishing.

Example break simulation:

```bash
ros2 topic pub /break_detected std_msgs/msg/Bool "{data: true}" --once
```

Lap completion simulation:

```bash
ros2 topic pub /lap_finished std_msgs/msg/Bool "{data: true}" --once
```

The robot was controlled using `teleop_twist_keyboard`.

### RViz Test During Development

The following screenshot shows the anomaly tracking system during manual RViz testing.

The red marker represents an active anomaly,
while the blue marker represents a previously detected but currently disappeared anomaly.

![RViz anomaly test](images/anomaly_test.png)

### Used ROS Packages

| ROS2 Package | Links |
|---|---|
| `rclpy` | https://docs.ros.org/en/iron/p/rclpy/ |
| `nav_msgs` | https://wiki.ros.org/nav_msgs |
| `std_msgs` | https://wiki.ros.org/std_msgs |
| `visualization_msgs` | https://wiki.ros.org/visualization_msgs |
| `sensor_msgs` | https://wiki.ros.org/sensor_msgs |
| `geometry_msgs` | https://wiki.ros.org/geometry_msgs |
| `cv_bridge` | https://wiki.ros.org/cv_bridge |
| `turtlebot3` | https://wiki.ros.org/turtlebot3 |
| `turtlebot3_msgs` | https://wiki.ros.org/turtlebot3_msgs |
| `turtlebot3_simulations` | https://wiki.ros.org/turtlebot3_simulations |
| `ros_gz_sim` | https://index.ros.org/p/ros_gz_sim/ |
| `rosgraph_msgs` | https://wiki.ros.org/rosgraph_msgs |
  
### External Repositories

MOGI ROS educational repository:

https://github.com/MOGI-ROS/Week-1-8-Cognitive-robotics

The repository contains the `turtlebot3_mogi` simulation package and additional TurtleBot3 Gazebo resources used in this project.
