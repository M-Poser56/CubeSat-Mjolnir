#FlightLoop.py - main flight loop for the StratoStar Flight 1 configuration

#standard library
import os
import csv
import time
import re
import queue
import threading
import subprocess
from datetime import datetime

#local mqtt (inter-script communication)
import paho.mqtt.client as mqtt

#hardware - Blinka (I2C/SPI/digital pins)
import board
import busio
import digitalio

#hardware - sensor & radio drivers
import adafruit_bno055 #IMU
import adafruit_rfm9x  #LoRa radio

#hardware - GPIO/PWM (reaction wheels)
import RPi.GPIO as GPIO

print("successfully ran")



#IMU board setup (same as IMU.py)
i2c = busio.I2C(board.SCL, board.SDA) #board pins 5, and 3, respectively
sensor = adafruit_bno055.BNO055_I2C(i2c)
#use_external_crystal left off (default/internal oscillator) - this board doesn't have one
#populated, and forcing it caused persistent None/-128C garbage readings
#(IMU is set up before the csv is created, so if the IMU fails to init and the service
#restarts, it doesn't leave a pile of empty csv files behind)


def ReadSensor(quantity, num_values):
    #reads one quantity off the BNO055 (ex. "euler", "magnetic"), always returned as a tuple
    #each quantity is its own small I2C read, so if one read glitches, only that
    #quantity is blanked in the row instead of losing the entire sample
    try:
        value = getattr(sensor, quantity)
    except (OSError, RuntimeError) as e:
        print(f"IMU {quantity} read failed: {e}")
        return (None,) * num_values
    if not isinstance(value, tuple): #temperature comes back as a single int
        value = (value,)
    #driver multiplies raw ints by a scale factor (ex. 9.81 -> 9.810000000000001),
    #rounding to 6 places just strips that float noise, it's still finer than the sensor resolution
    return tuple(round(v, 6) if isinstance(v, float) else v for v in value)


#telemetry csv setup
#one new csv per service start, named with the start datetime, saved in ~/FlightTelemetry/
#NOTE: ~ is the home directory of whichever user the service runs as (User= in the .service file)
telemetry_dir = os.path.expanduser("~/FlightTelemetry")
os.makedirs(telemetry_dir, exist_ok=True)
telemetry_path = os.path.join(telemetry_dir, datetime.now().strftime("%Y-%m-%d_%H-%M-%S") + ".csv")

#append mode, so an existing file can never be overwritten (the pi has no RTC, so after
#a reboot the clock can roll back and land on an old filename)
telemetry_file = open(telemetry_path, "a", newline="")
telemetry_writer = csv.writer(telemetry_file)
#column header, written once at the top of the file
#units: angles in degrees, acceleration in m/s^2, gyro in rad/s, magnetometer in microtesla,
#quaternion unitless, calibration 0 (uncalibrated) to 3 (fully calibrated)
telemetry_header = [
    "timestamp", "pitch", "roll", "yaw", "temp_C",
    "accel_x_ms2", "accel_y_ms2", "accel_z_ms2",       #raw accelerometer (includes gravity)
    "linaccel_x_ms2", "linaccel_y_ms2", "linaccel_z_ms2", #acceleration with gravity removed
    "gravity_x_ms2", "gravity_y_ms2", "gravity_z_ms2",  #gravity vector only (which way is down)
    "gyro_x_rads", "gyro_y_rads", "gyro_z_rads",        #angular velocity (rotation speed)
    "mag_x_uT", "mag_y_uT", "mag_z_uT",                 #magnetic field
    "quat_w", "quat_x", "quat_y", "quat_z",             #orientation as a quaternion
    "cal_sys", "cal_gyro", "cal_accel", "cal_mag",      #calibration status
]
if os.path.getsize(telemetry_path) == 0: #only a brand new file gets the header
    telemetry_writer.writerow(telemetry_header)
    telemetry_file.flush()
print(f"Logging IMU telemetry to {telemetry_path}")


sample_interval = 3.0 #seconds between IMU readings
next_sample = time.monotonic()


try:
    while True:
        #step 1, take a single reading of everything on the IMU
        #(a failed read comes back as blanks, so the gap still shows up in the data)
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        CubeSat_angular = ReadSensor("euler", 3) #returns a tuple type, as: yaw, roll, pitch
        CubeSat_temp = ReadSensor("temperature", 1)
        CubeSat_accel = ReadSensor("acceleration", 3)
        CubeSat_linaccel = ReadSensor("linear_acceleration", 3)
        CubeSat_gravity = ReadSensor("gravity", 3)
        CubeSat_gyro = ReadSensor("gyro", 3)
        CubeSat_mag = ReadSensor("magnetic", 3)
        CubeSat_quat = ReadSensor("quaternion", 4) #w, x, y, z
        CubeSat_cal = ReadSensor("calibration_status", 4) #sys, gyro, accel, mag

        #step 2, write it to the csv, same order as the header
        #(pitch, roll, yaw, temp first, same as IMU.py packet format)
        telemetry_row = [timestamp, CubeSat_angular[2], CubeSat_angular[1], CubeSat_angular[0], *CubeSat_temp,
                         *CubeSat_accel, *CubeSat_linaccel, *CubeSat_gravity, *CubeSat_gyro,
                         *CubeSat_mag, *CubeSat_quat, *CubeSat_cal]
        telemetry_writer.writerow(telemetry_row)
        telemetry_file.flush()
        os.fsync(telemetry_file.fileno()) #force the row onto the SD card now, so a sudden power cut can't lose it

        #step 3, wait for the next 3.0 second mark
        #scheduling off a fixed clock (instead of a plain sleep(3.0)) stops the read/write
        #time from slowly drifting the interval
        next_sample += sample_interval
        delay = next_sample - time.monotonic()
        if delay > 0:
            time.sleep(delay)
        else:
            next_sample = time.monotonic() #fell behind (slow read), resync instead of bursting


finally:
    print("Flight Computer Flight Loop Deactivated")
    telemetry_file.close()
