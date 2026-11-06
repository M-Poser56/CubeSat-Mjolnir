#FlightLoop.py - main flight loop for the StratoStar Flight 1 configuration

"""
A Note from the Engineer! (Matt Poser)

This is some code which is running on the November 16th StratoStar flight, in lieu of the
standard code which runs on the flight computer in conjunction with a groundstation
(there is no groundstation for this flight, CubeSat is alone as a payload!)

I want on the flight to do 2 main things:
1 - capture as much telemetry data as I can via the BNO055
2 - capture as many photos as I can using the onboard camera

Unfortunately due to extreme conditions, I do expect these to fail at some point during the
ascent. We will see how long I can collect data & telemetry for!

The purpose of this script, is to run on a loop with the same architecture as all the other
scripts I wrote myself (this is 100% claude), to log as much BNO055 data on a loop as I can.
While this happens, I want to send 'dummy' mqtt commands to the command handler script, which
alongside the star tracker script will be the only other two service scripts running. When these
dummy commands are sent from this script to the command handler, the downstream of the command
handler script will run how it did on the other Mk.I CubeSat. The only command which will come
from this script to the command handler is "CMD:STARTRACKER" , so only the star tracker service
needs to run. Camera is controlled by StarTracker.py, and the downstream camera_test.py

"""

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



#mqtt setup (this script only publishes, the dummy star tracker commands)
#same as the other scripts, except connect_async: if mosquitto isn't up yet (ex. right at boot)
#paho keeps retrying in the background instead of crashing this script, so the IMU logging
#never depends on mqtt being alive
#(no on_publish callback here, PhotoCommander() prints its own send confirmation, and the two
#printing from different threads at the same moment garbled the log lines together)
def on_connect(client, userdata, flags, reason_code, properties):
    print(f"mqtt localhost connected with result code {reason_code}")

FlightLoop_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
FlightLoop_client.on_connect = on_connect
FlightLoop_client.reconnect_delay_set(min_delay=1, max_delay=10) #seconds between reconnect attempts
FlightLoop_client.connect_async("localhost", 1883)
FlightLoop_client.loop_start()


#dummy star tracker (photo) commands
photo_interval_min = 0.5 #MINUTES between photos, change this! (0.5 minimum)
photo_interval = max(photo_interval_min, 0.5) * 60 #seconds, clamped so a typo can't queue photos faster than the camera takes them

def PhotoCommander():
    #runs in its own background thread, on its own timer
    #publishes the exact command string the groundstation would send, to the same topic LoRA_ULDL's
    #CommandHandler() publishes to, so the downstream runs exactly like Mk.I:
    #FlightLoop.py -> CMD/HANDLER -> Command_Handler.py -> CMD/STARTRACKER -> Star_Tracker.py -> camera_test.py
    #being its own thread means photos keep being commanded even if the IMU dies, and vice versa
    next_photo = time.monotonic() + photo_interval
    while True:
        time.sleep(max(0, next_photo - time.monotonic()))
        try:
            result = FlightLoop_client.publish("CMD/HANDLER", "CMD:STARTRACKER")
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                print("Photo command sent: CMD:STARTRACKER")
            else:
                print(f"Photo command NOT sent, mqtt not connected (rc {result.rc}), trying again next interval")
        except Exception as e: #never let this thread die quietly, or the photos stop for the rest of the flight
            print(f"Photo command error: {e}")
        next_photo += photo_interval
        if next_photo < time.monotonic(): #fell behind, resync instead of firing a burst of commands
            next_photo = time.monotonic() + photo_interval

photo_thread = threading.Thread(target=PhotoCommander, daemon=True) #daemon, so it dies with the main script
photo_thread.start()
print(f"Photo commands every {photo_interval / 60} minutes")



#IMU board setup (same as IMU.py)
i2c = busio.I2C(board.SCL, board.SDA) #board pins 5, and 3, respectively
sensor = None #set by InitIMU()

def InitIMU():
    #brings up the BNO055. If it isn't responding, this does NOT crash the script (that would take
    #the photo commands down with it), sensor just stays None and the main loop retries next sample
    global sensor
    try:
        sensor = adafruit_bno055.BNO055_I2C(i2c)
        #use_external_crystal left off (default/internal oscillator) - this board doesn't have one
        #populated, and forcing it caused persistent None/-128C garbage readings
        print("BNO055 IMU initialized")
    except (OSError, RuntimeError, ValueError) as e: #ValueError = nothing answering at address 0x28
        sensor = None
        print(f"BNO055 IMU init failed, retrying next sample: {e}")

InitIMU()


def ReadSensor(quantity, num_values):
    #reads one quantity off the BNO055 (ex. "euler", "magnetic"), always returned as a tuple
    #each quantity is its own small I2C read, so if one read glitches, only that
    #quantity is blanked in the row instead of losing the entire sample
    if sensor is None: #IMU not up, blanks for this sample
        return (None,) * num_values
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
imu_fail_streak = 0 #consecutive samples with no orientation data


try:
    while True:
        #step 0, if the IMU isn't up (failed at boot, or dropped out mid flight), try to bring it back
        if sensor is None:
            InitIMU()
            imu_fail_streak = 0

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

        #step 3, IMU health check
        #if orientation comes back blank 5 samples (15 s) in a row, the BNO055 has most likely reset
        #itself or dropped off the bus (cold, brownout). Throw it out, step 0 re-initializes it next sample
        if CubeSat_angular == (None, None, None):
            imu_fail_streak += 1
            if imu_fail_streak >= 5 and sensor is not None:
                print("IMU unresponsive for 5 samples, re-initializing")
                sensor = None
        else:
            imu_fail_streak = 0

        #step 4, wait for the next 3.0 second mark
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
    FlightLoop_client.loop_stop()
    FlightLoop_client.disconnect()
