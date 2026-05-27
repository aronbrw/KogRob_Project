# KogRob_Project
## Project Mapping Modul — `anomaly_mapper_node`

A `project_mapping` modul feladata a vonalkövetés során detektált szakadások/anomáliák térképes megjelenítése és állapotkövetése RViz környezetben.

### Működés

Amikor a `/break_detected` topic `True` értéket küld:

1. A node lekéri a robot aktuális pozícióját és orientációját.
2. A robot orientációja alapján kiszámolja a kamera előtti becsült szakadás pozícióját.
3. Megvizsgálja, hogy található-e már korábban eltárolt anomália a közelben.
4. Ha nem:
   - új anomáliát hoz létre.
5. Ha igen:
   - a meglévő anomáliát újra aktívnak jelöli.

### RViz marker színek

| Szín | Jelentés |
|---|---|
| 🔴 Piros | Aktív / jelenlegi szakadás |
| 🔵 Kék | Korábban detektált, de már eltűnt szakadás |

### Tesztelés

```bash
ros2 topic pub /break_detected std_msgs/msg/Bool "{data: true}" --once
```

```bash
ros2 topic pub /lap_finished std_msgs/msg/Bool "{data: true}" --once
```

### Fejlesztés közbeni RViz teszt

![RViz anomaly test](images/anomaly_test.png)
