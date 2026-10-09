"""
usv_sim.py - Pure Python Virtual USV (Autonomous Boat Simulator).
Emits real MAVLink telemetry and cruises at 1.8 m/s automatically.
"""

import time
import math
import socket
from pymavlink import mavutil

SENTINEL_IP = "127.0.0.1"
SENTINEL_PORT = 14550

print("==================================================")
print("          VIRTUAL USV VEHICLE EMULATOR            ")
print("==================================================")
print(f"[*] Starting boat IoT node...")
print(f"[*] Streaming MAVLink telemetry to Sentinel on UDP: {SENTINEL_PORT}\n")

# Standard UDP socket 
sock_out = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# MAVLink packet generator
mav = mavutil.mavlink.MAVLink(None, srcSystem=1, srcComponent=1)

# Initial Physical State
is_armed = True
groundspeed = 1.8  # m/s
base_lat = 43.1930 # Varna/coastal coordinates
base_lon = 27.9100
heading  = 45.0
tick = 0

print("[+] USV Armed and Navigating! Autonomous Propulsion: ACTIVE\n")

while True:
    try:
        tick += 1
        
        # GPS movement along heading if armed
        if is_armed and groundspeed > 0:
            base_lat += (groundspeed * 0.000001) * math.cos(math.radians(heading))
            base_lon += (groundspeed * 0.000001) * math.sin(math.radians(heading))

        # HEARTBEAT (1 Hz)
        if tick % 10 == 0:
            mode_flag = mavutil.mavlink.MAV_MODE_FLAG_CUSTOM_MODE_ENABLED
            if is_armed:
                mode_flag |= mavutil.mavlink.MAV_MODE_FLAG_SAFETY_ARMED

            hb = mav.heartbeat_encode(
                mavutil.mavlink.MAV_TYPE_SURFACE_BOAT,
                mavutil.mavlink.MAV_AUTOPILOT_ARDUPILOTMEGA,
                mode_flag,
                0,
                mavutil.mavlink.MAV_STATE_ACTIVE
            )
            sock_out.sendto(hb.pack(mav), (SENTINEL_IP, SENTINEL_PORT))

        # VFR_HUD (Groundspeed)
        vfr = mav.vfr_hud_encode(
            airspeed=0.0,
            groundspeed=groundspeed if is_armed else 0.0,
            heading=int(heading),
            throttle=65 if is_armed else 0,
            alt=0.0,
            climb=0.0
        )
        sock_out.sendto(vfr.pack(mav), (SENTINEL_IP, SENTINEL_PORT))

        # GLOBAL_POSITION_INT (GPS)
        pos = mav.global_position_int_encode(
            time_boot_ms=int(time.time() * 1000) & 0xFFFFFFFF,
            lat=int(base_lat * 1e7),
            lon=int(base_lon * 1e7),
            alt=0,
            relative_alt=0,
            vx=int(groundspeed * 100),
            vy=0,
            vz=0,
            hdg=int(heading * 100)
        )
        sock_out.sendto(pos.pack(mav), (SENTINEL_IP, SENTINEL_PORT))

        # live status every second
        if tick % 10 == 0:
            status_str = "ARMED (Cruising)" if is_armed else "DISARMED (Stopped)"
            print(f"\r[*] USV Status: {status_str:20} | Speed: {groundspeed:.2f} m/s | Pos: ({base_lat:.6f}, {base_lon:.6f})", end="")

        time.sleep(0.1)  # 10 Hz telemetry loop

    except KeyboardInterrupt:
        print("\n[!] Boat shutdown.")
        break