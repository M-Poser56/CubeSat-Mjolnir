"""
Live 3D orientation visualization for an Adafruit BNO055 IMU on a Raspberry Pi.

A crude "duck" mesh rotates in real time to match the sensor's reported
orientation (quaternion from the BNO055's onboard sensor fusion).

Wiring (I2C, 4 wires):
    BNO055 VIN -> Pi 3.3V   (physical pin 1)
    BNO055 GND -> Pi GND    (physical pin 6, or any GND pin)
    BNO055 SDA -> Pi SDA    (GPIO2 / physical pin 3)
    BNO055 SCL -> Pi SCL    (GPIO3 / physical pin 5)

Before running:
    sudo raspi-config           # Interface Options -> I2C -> Enable, then reboot
    sudo i2cdetect -y 1         # confirm the sensor shows up at address 0x28 (or 0x29)
    pip3 install adafruit-circuitpython-bno055 adafruit-blinka matplotlib numpy
"""

import numpy as np
import board
import busio
import adafruit_bno055

import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from matplotlib.animation import FuncAnimation

# ---------- IMU setup ----------
i2c = busio.I2C(board.SCL, board.SDA)
sensor = adafruit_bno055.BNO055_I2C(i2c)
# NDOF mode (9-DOF fused orientation) is the default on power-up.

# ---------- Build a crude duck out of triangles ----------
def make_duck():
    faces = []

    def ellipsoid(center, radii, n=10, color="gold"):
        u = np.linspace(0, 2 * np.pi, n)
        v = np.linspace(0, np.pi, n)
        x = radii[0] * np.outer(np.cos(u), np.sin(v)) + center[0]
        y = radii[1] * np.outer(np.sin(u), np.sin(v)) + center[1]
        z = radii[2] * np.outer(np.ones_like(u), np.cos(v)) + center[2]
        tris = []
        for i in range(n - 1):
            for j in range(n - 1):
                p1 = [x[i, j], y[i, j], z[i, j]]
                p2 = [x[i + 1, j], y[i + 1, j], z[i + 1, j]]
                p3 = [x[i + 1, j + 1], y[i + 1, j + 1], z[i + 1, j + 1]]
                p4 = [x[i, j + 1], y[i, j + 1], z[i, j + 1]]
                tris.append((np.array([p1, p2, p3]), color))
                tris.append((np.array([p1, p3, p4]), color))
        return tris

    faces += ellipsoid((0, 0, 0), (1.0, 0.7, 0.7), n=10, color="gold")      # body
    faces += ellipsoid((1.0, 0, 0.4), (0.4, 0.4, 0.4), n=8, color="gold")   # head

    # beak (small pyramid)
    p1 = np.array([1.35, 0, 0.35])
    p2 = np.array([1.7, 0.12, 0.3])
    p3 = np.array([1.7, -0.12, 0.3])
    p4 = np.array([1.5, 0, 0.5])
    beak_color = "orange"
    faces.append((np.array([p1, p2, p4]), beak_color))
    faces.append((np.array([p1, p4, p3]), beak_color))
    faces.append((np.array([p1, p2, p3]), beak_color))
    faces.append((np.array([p2, p3, p4]), beak_color))
    return faces

DUCK_FACES = make_duck()

# ---------- Quaternion -> rotation matrix ----------
def quat_to_rotmat(w, x, y, z):
    n = np.sqrt(w * w + x * x + y * y + z * z)
    if n == 0:
        return np.eye(3)
    w, x, y, z = w / n, x / n, y / n, z / n
    return np.array([
        [1 - 2 * (y * y + z * z), 2 * (x * y - z * w),     2 * (x * z + y * w)],
        [2 * (x * y + z * w),     1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
        [2 * (x * z - y * w),     2 * (y * z + x * w),     1 - 2 * (x * x + y * y)],
    ])

# ---------- Plot setup ----------
fig = plt.figure(figsize=(7, 7))
ax = fig.add_subplot(111, projection="3d")
ax.set_box_aspect([1, 1, 1])
LIM = 2
ax.set_xlim(-LIM, LIM)
ax.set_ylim(-LIM, LIM)
ax.set_zlim(-LIM, LIM)
ax.set_axis_off()

collection = Poly3DCollection(
    [f[0] for f in DUCK_FACES],
    facecolors=[f[1] for f in DUCK_FACES],
    edgecolors="k",
    linewidths=0.1,
)
ax.add_collection3d(collection)

status_text = ax.text2D(0.02, 0.95, "", transform=ax.transAxes)

def update(frame):
    quat = sensor.quaternion  # (w, x, y, z); can be (None, None, None, None) briefly
    if quat is None or quat[0] is None:
        return collection, status_text

    w, x, y, z = quat
    R = quat_to_rotmat(w, x, y, z)
    rotated_verts = [verts @ R.T for verts, _ in DUCK_FACES]
    collection.set_verts(rotated_verts)

    euler = sensor.euler  # (heading, roll, pitch), degrees
    calib = sensor.calibration_status  # (sys, gyro, accel, mag), 0-3 each
    if euler[0] is not None:
        status_text.set_text(
            f"Heading:{euler[0]:6.1f}  Roll:{euler[1]:6.1f}  Pitch:{euler[2]:6.1f}\n"
            f"Calibration (sys,gyro,acc,mag): {calib}"
        )
    return collection, status_text

ani = FuncAnimation(fig, update, interval=100, blit=False)
plt.show()
