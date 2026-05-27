# KogRob_Project
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

- `rclpy`
- `nav_msgs`
- `std_msgs`
- `visualization_msgs`

### External Repositories

MOGI ROS educational repository:

https://github.com/MOGI-ROS/Week-1-8-Cognitive-robotics
