"""
Headless orientation readout for an Adafruit BNO055 IMU on a Raspberry Pi.

Same sensor setup as duck_test.py, but with no matplotlib / display needed.
Pitch, roll and yaw (from the BNO055's onboard sensor fusion) are printed to
the shell each time the sensor is sampled. Press Ctrl+C to stop.

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

import time
import board
import busio
import adafruit_bno055

SAMPLE_INTERVAL = 0.1  # seconds between samples

# ---------- IMU setup ----------
i2c = busio.I2C(board.SCL, board.SDA)
sensor = adafruit_bno055.BNO055_I2C(i2c)
# NDOF mode (9-DOF fused orientation) is the default on power-up.

print("Sampling BNO055 (Ctrl+C to stop)")
try:
    while True:
        euler = sensor.euler  # (heading/yaw, roll, pitch), degrees; can be None values briefly
        calib = sensor.calibration_status  # (sys, gyro, accel, mag), 0-3 each

        if euler is not None and euler[0] is not None:
            yaw, roll, pitch = euler
            print(
                f"Pitch:{pitch:7.1f}  Roll:{roll:7.1f}  Yaw:{yaw:7.1f}  "
                f"Calibration (sys,gyro,acc,mag): {calib}"
            )

        time.sleep(SAMPLE_INTERVAL)
except KeyboardInterrupt:
    print("\nStopped.")
