# USV-Sentinel: Stateful Telemetry Security Gateway & DPI Firewall for Autonomous Marine Vessels

![Python Version](https://img.shields.io/badge/python-3.9%2B-blue.svg)
![Protocol](https://img.shields.io/badge/protocol-MAVLink%20v1%2Fv2-orange.svg)
![Transport](https://img.shields.io/badge/transport-UDP%20Socket-brightgreen.svg)
![Domain](https://img.shields.io/badge/domain-Robotics%20%2F%20IoT%20Security-red.svg)

An inline **Application-Layer Gateway (ALG)** and **Intrusion Prevention System (IPS)** engineered to protect Unmanned Surface Vehicles (USVs) and autonomous drones from unauthenticated MAVLink command injection over UDP telemetry links.

---

## 1. Problem Statement & Threat Model

Unmanned Surface Vehicles (USVs) operating in coastal and maritime environments rely on connectionless UDP transport for telemetry links (LTE, maritime mesh radio, or satellite). Unlike TCP, UDP avoids **Head-of-Line (HoL) blocking** and retransmission delays, ensuring real-time vehicle awareness.

However, standard MAVLink networks lack native link-layer authentication. An attacker on the local network or cellular subnet can inject raw UDP datagrams directly into the vehicle's telemetry stream.

### Exploited Vulnerabilities:
1. **Kinetic Disarm (Remote Engine Cutoff):** Forcing `MAV_CMD_COMPONENT_ARM_DISARM` with parameter `1=0` while the vessel is underway, causing propulsion loss and drift.
2. **Autonomous Memory Erasure:** Injecting `MISSION_CLEAR_ALL` (Message ID 45) to erase autonomous waypoint plans.
3. **Spatial Hijacking (Geofence Breach):** Injecting spoofed `MISSION_ITEM` coordinates to divert the vessel outside authorized operational sectors.

---

## 2. System Architecture

`USV-Sentinel` operates as an inline proxy between external communication links and the vessel's internal flight controller.

```mermaid
flowchart LR
    subgraph Vehicle [Autonomous USV - IoT Node]
        USV["usv_sim.py<br/>Kinematics @ 10 Hz<br/>Speed: 1.80 m/s"]
    end

    subgraph SecurityGateway [Onboard Companion Computer]
        Sentinel["sentinel.py<br/>Stateful DPI Engine<br/>& Threat Filter"]
        Logs[("security_alerts.log<br/>Incident Forensics")]
    end

    subgraph External [External Network / Telemetry Link]
        Attacker["attacker.py<br/>UDP Exploit Injector"]
        GCS["Mission Planner / QGC<br/>Optional Map Display"]
    end

    USV -->|"UDP 14550<br/>Telemetry: HEARTBEAT, VFR_HUD, GPS"| Sentinel
    Attacker -->|"UDP 14551<br/>Command Injections"| Sentinel
    Sentinel -->|"UDP 14552<br/>Verified Telemetry Mirror"| GCS
    Sentinel -->|"Alert Audits"| Logs
    Sentinel -->|"Approved Commands Only"| USV
```
