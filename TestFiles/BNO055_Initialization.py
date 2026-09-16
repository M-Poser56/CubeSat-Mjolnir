"""
Initialization / connection test for an Adafruit BNO055 9-axis IMU on a Raspberry Pi.

Connects over I2C, confirms the sensor responds, and prints one packet of
data (temperature, calibration status, and a quaternion reading) to prove
the link is alive.

Wiring (I2C, 4 wires):
    BNO055 VIN -> Pi 3.3V   (physical pin 1)
    BNO055 GND -> Pi GND    (physical pin 6, or any GND pin)
    BNO055 SDA -> Pi SDA    (GPIO2 / physical pin 3)
    BNO055 SCL -> Pi SCL    (GPIO3 / physical pin 5)

Before running:
    sudo raspi-config           # Interface Options -> I2C -> Enable, then reboot
    sudo i2cdetect -y 1         # confirm the sensor shows up at address 0x28 (or 0x29)
    pip3 install adafruit-circuitpython-bno055 adafruit-blinka
"""
#this was written by claude in its entirety
import time
import board
import busio
import adafruit_bno055

print("BNO055 Initialization Test")
print("---------------------------")

try:
    i2c = busio.I2C(board.SCL, board.SDA)
    sensor = adafruit_bno055.BNO055_I2C(i2c)

    # The Adafruit breakout has an external crystal; using it improves accuracy.
    sensor.use_external_crystal = True

    # The fusion firmware needs a moment after init, and the very first
    # register read can be junk (e.g. temperature reading -128/-102 C).
    # Take a couple of throwaway readings before printing.
    time.sleep(1)
    for _ in range(3):
        sensor.temperature
        sensor.quaternion
        time.sleep(0.1)

    print("PASS — BNO055 detected!")
    print(f"  Temperature : {sensor.temperature} C")
    print(f"  Calibration (sys,gyro,acc,mag) : {sensor.calibration_status}")
    print(f"  Quaternion (w,x,y,z) : {sensor.quaternion}")
    print("Initialization test complete. Ready.")
    print()
    print("Note: gyro/accel/mag calibration climb to 3 only once you move the")
    print("board — rotate it through several orientations, hold it still for")
    print("a couple seconds, and wave it in a figure-8 for the magnetometer.")

except (RuntimeError, ValueError, OSError) as e:
    print(f"FAIL — Could not initialize BNO055: {e}")
    print("  - Is VIN on 3.3V?")
    print("  - Check SDA/SCL wiring")
    print("  - Is I2C enabled? Run: sudo i2cdetect -y 1")
