from electrophstat.hardware.voltcraft_pps import VoltcraftPPS

psu = VoltcraftPPS('/dev/ttyUSB0', reset=True, debug=True)
psu.connect()

try:
    psu.set_output(True)
    psu.set_voltage(5.0)
    psu.set_current(1.0)
    #psu.output(True)

    v, a, mode = psu.read_output()
    print(f"Voltage={v} V, Current={a} A, Mode={mode}")

except Exception as e:
    print("Error:", e)

#finally:
#    psu.output(False)
    #psu.disconnect()
