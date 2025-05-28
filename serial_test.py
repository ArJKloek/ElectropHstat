# test_psu_comm.py
import time
import serial
from electrophstat.vendor.pps import PPS

PORT = "/dev/ttyUSB0"  # Change if needed

def main():
    print("=== PSU Command Test ===")
    try:
        psu = PPS(port=PORT, debug=True)
        commands = ["GMAX", "GOVP", "GOCP", "GETS", "GOUT", "GOUTV", "GOUTC", "GSTAT", "GIDN"]
        for cmd in commands:
            try:
                resp = psu._query(cmd)
                print(f"[{cmd}] -> {resp!r}")
            except Exception as e:
                print(f"[{cmd}] ERROR: {e}")
    except Exception as e:
        print(f"[ERROR] {e}")

if __name__ == "__main__":
    main()