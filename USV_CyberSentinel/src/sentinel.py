"""
sentinel.py - Stateful MAVLink Security Gateway & DPI Firewall.
"""

import sys
import time
import os
import datetime
import socket
from pymavlink import mavutil

LOG_FILE = "../logs/security_alerts.log"
os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)

class VehicleState:
    def __init__(self):
        self.is_armed = False
        self.groundspeed = 0.0
        self.lat = 0.0
        self.lon = 0.0

state = VehicleState()

def log_alert(alert_type: str, details: str):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry = f"[{timestamp}] [CRITICAL] [{alert_type}] {details}"
    print(f"\n\n{'='*60}\n>>> {entry}\n{'='*60}\n")
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(entry + "\n")

def inspect_command(msg) -> tuple[bool, str]:
    """Stateful Deep Packet Inspection."""
    mtype = msg.get_type()

    # Rule 1: In-Transit Disarm Check
    if mtype == 'COMMAND_LONG':
        if msg.command == mavutil.mavlink.MAV_CMD_COMPONENT_ARM_DISARM:
            if msg.param1 == 0:  # Disarm request
                if state.groundspeed > 0.3:
                    return False, f"MALICIOUS DISARM BLOCKED: USV cruising at {state.groundspeed:.2f} m/s!"

    # Rule 2: Autonomous Mission Wipe Check
    elif mtype == 'MISSION_CLEAR_ALL':
        return False, "UNAUTHORIZED MISSION_CLEAR_ALL BLOCKED: Wipe rejected."

    # Rule 3: Geofence Validation (supports both float and int waypoints)
    elif mtype in ['MISSION_ITEM', 'MISSION_ITEM_INT']:
        lat = msg.x if mtype == 'MISSION_ITEM' else (msg.x / 1e7)
        lon = msg.y if mtype == 'MISSION_ITEM' else (msg.y / 1e7)
        if not (43.10 <= lat <= 43.30 and 27.80 <= lon <= 28.10):
            return False, f"ROGUE WAYPOINT BLOCKED: ({lat:.4f}, {lon:.4f}) outside Geofence!"

    return True, "SAFE"

def run_sentinel():
    print("==================================================")
    print("      USV-SENTINEL: CYBERSECURITY DPI GATEWAY     ")
    print("==================================================")
    print("[*] Listening for USV Telemetry on UDP: 14550")
    print("[*] Listening for External Commands on UDP: 14551")
    print("[*] Streaming Telemetry to Mission Planner on UDP: 14552")
    print("[*] Gateway Active. Monitoring link integrity...\n")

    # Inbound telemetry listener from USV
    usv_in = mavutil.mavlink_connection("udpin:127.0.0.1:14550")
    # Inbound command listener from Hacker
    cmd_in = mavutil.mavlink_connection("udpin:127.0.0.1:14551")
    
    # socket (port 14552)
    mp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    packet_count = 0

    while True:
        try:
            # USV -> Sentinel -> Mission Planner
            telemetry_msg = usv_in.recv_match(blocking=False)
            if telemetry_msg:
                mtype = telemetry_msg.get_type()
                
                # Update state
                if mtype == 'HEARTBEAT':
                    state.is_armed = bool(telemetry_msg.base_mode & mavutil.mavlink.MAV_MODE_FLAG_SAFETY_ARMED)
                elif mtype == 'VFR_HUD':
                    state.groundspeed = telemetry_msg.groundspeed
                elif mtype == 'GLOBAL_POSITION_INT':
                    state.lat = telemetry_msg.lat / 1e7
                    state.lon = telemetry_msg.lon / 1e7

                #  telemetry
                raw_bytes = telemetry_msg.get_msgbuf()
                if raw_bytes:
                    try:
                        mp_sock.sendto(raw_bytes, ("127.0.0.1", 14552))
                    except Exception:
                        pass

                packet_count += 1
                if packet_count % 20 == 0:
                    status = "ARMED" if state.is_armed else "DISARMED"
                    sys.stdout.write(f"\r[*] Sentinel Monitoring | Status: {status:8} | Speed: {state.groundspeed:.2f} m/s | Packets: {packet_count}")
                    sys.stdout.flush()

            # External Senders -> Sentinel
            incoming_cmd = cmd_in.recv_match(blocking=False)
            if incoming_cmd:
                is_safe, reason = inspect_command(incoming_cmd)
                if not is_safe:
                    log_alert("COMMAND_INJECTION_PREVENTED", reason)

            time.sleep(0.001)

        except KeyboardInterrupt:
            print("\n[!] Sentinel stopped.")
            break

if __name__ == "__main__":
    run_sentinel()