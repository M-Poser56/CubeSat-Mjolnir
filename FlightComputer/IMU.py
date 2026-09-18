#placeholder script for IMU board & data

#the goal of this script is to broadcast (on regular intervals) sensor packet data
#to the IMU/PACKET topic, which the LoRA ULDL will read



#imports
import time
import board
import busio
import adafruit_bno055
import paho.mqtt.client as mqtt



#mqtt connection stuff here (this script only publishes)
def on_connect(client, userdata, flags, reason_code, properties):
    print(f"mqtt localhost connected with result code {reason_code}")

def on_publish(client, userdata, mid, reason_codes, properties):
    print(f"Published message id {mid}")

IMU_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
IMU_client.on_connect = on_connect
IMU_client.on_publish = on_publish
IMU_client.connect("localhost", 1883)
IMU_client.loop_start()

#the structure of this loop publishing script will be:
#on a set timer of 1 second, sleep, then record sensor information,
#parse it to correct format, and publish it. Repeat.

#IMU board setup
i2c = busio.I2C(board.SCL, board.SDA) #board pins 5, and 3, respectively
sensor = adafruit_bno055.BNO055_I2C(i2c)
#use_external_crystal left off (default/internal oscillator) - this board doesn't have one
#populated, and forcing it caused persistent None/-128C garbage readings


try:
    while True:
        time.sleep(1) #maintain the 1Hz floor time limit for ambient temperature readings.
        #packet timeout speed for the main script will be between 2-5 seconds, so this loop natively
        #runs faster

        #obtain sensor info
        CubeSat_angular = sensor.euler #returns a tuple type, as: yaw, roll, pitch
        CubeSat_temp = sensor.temperature

        #parsing
        payload_string = f"{CubeSat_angular[2]}, {CubeSat_angular[1]}, {CubeSat_angular[0]}, {CubeSat_temp}C"
        #this is to put it in the expected pitch, roll, yaw, *C format


        #publishing
        IMU_client.publish("IMU/PACKET", payload_string, retain=True) 
        #this retain=True will allow new subscribers to be fed immediately the newest packet


finally:
    print("Flight Computer Uplink/Downlink Deactivated")
    IMU_client.loop_stop()
    IMU_client.disconnect()


