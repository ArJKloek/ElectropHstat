from electrophstat.vendor.pps import PPS

psu = PPS('/dev/ttyUSB0', reset=True, debug=True)
psu.connect()

try:
    psu.output(1)
    psu.voltage(5.0)
    psu.current(1.0)
    #psu.output(True)

    v, a, mode = psu.reading()
    print(f"Voltage={v} V, Current={a} A, Mode={mode}")

except Exception as e:
    print("Error:", e)

finally:
    psu.output(False)
    psu.disconnect()
