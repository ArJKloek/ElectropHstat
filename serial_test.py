# test_psu_comm.py
import time
from electrophstat.vendor.pps import PPS
import serial

PORT = "/dev/ttyUSB0"  # Change if needed

def main():
    print("=== PSU Communication Test ===")
    try:
        psu = PPS(port=PORT, debug=True)
        print("[TEST] PPS object created successfully.")
        print(f"[TEST] Model: {psu.MODEL}, VMAX: {psu.VMAX}, IMAX: {psu.IMAX}")
        print("[TEST] Querying voltage and current reading...")
        v, i, mode = psu.reading()
        print(f"[TEST] Voltage: {v} V, Current: {i} A, Mode: {mode}")
    except serial.SerialException as e:
        print(f"[ERROR] Serial port error: {e}")
    except RuntimeError as e:
        print(f"[ERROR] Runtime error: {e}")
    except Exception as e:
        print(f"[ERROR] Unexpected error: {e}")

if __name__ == "__main__":
    main()