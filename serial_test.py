# test_psu_comm.py
import time
import serial

PORT = "/dev/ttyUSB0"  # Change if needed
BAUD = 9600

def send_cmd(ser, cmd):
    ser.write((cmd + "\r").encode())
    time.sleep(0.1)
    resp = b""
    while ser.in_waiting:
        resp += ser.read(ser.in_waiting)
        time.sleep(0.05)
    return resp

def main():
    print("=== RAW PSU Command Test ===")
    try:
        with serial.Serial(PORT, BAUD, timeout=1) as ser:
            commands = ["GMAX", "GOVP", "GOCP", "GETS", "GOUT", "GOUTV", "GOUTC", "GSTAT", "GIDN"]
            for cmd in commands:
                print(f"Sending: {cmd}")
                resp = send_cmd(ser, cmd)
                print(f"Response: {resp!r}")
    except Exception as e:
        print(f"[ERROR] {e}")

if __name__ == "__main__":
    main()