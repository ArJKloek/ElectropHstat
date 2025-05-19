from electrophstat.hardware.voltcraft_pps import VoltcraftPPS

psu = VoltcraftPPS('/dev/ttyUSB0', reset=True)
psu.connect()

try:
    psu.voltage(5.0)
    psu.current(1.0)
    psu.output(True)

    v, a, mode = psu.reading()
    print(f"Voltage={v} V, Current={a} A, Mode={mode}")

except Exception as e:
    print("Error:", e)

finally:
    psu.output(False)
    psu.disconnect()
