#file for startracker downstream script

#this follows the exact same structure as Mjolnir_Reboot.py (at the moment), but with different
#local mqtt topics, and different subprocess commands



import queue
import paho.mqtt.client as mqtt
import re
import subprocess

startracker_queue = queue.Queue() #initialize script local queue to store upstream command messages


#mqtt functions (for reboot script)
def on_connect(client, userdata, flags, reason_code, properties):
    print(f"mqtt localhost connected with result code {reason_code}")
    client.subscribe("CMD/STARTRACKER") #upstream being published to by LoRA_ULDL in the CommandHandler() function

def on_message(client, userdata, msg):
    startracker_queue.put(msg.payload.decode()) #adds command string to queue, FIFO

Startracker_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
Startracker_client.on_connect = on_connect
Startracker_client.on_message = on_message
Startracker_client.connect("localhost", 1883)
Startracker_client.loop_start()

#this is a command/subsystem that we'll want to run on loop. Thus, the loop architecture will follow
#the currently written Command_Handler script, but the subprocess.run() executable line will follow
#that of the reboot script (without the silly passwordless business)

try:
    while True:
        recieved_command = startracker_queue.get()

        #call camera/star tracker script
        #NOTE TO DEV: This python script being called  by subprocess is simply
        #a script which takes a photo using the camera, and leaves it in the 
        #home directory as a timestamped file. Seeing as this cubesat has not (yet)
        #launched, any photo taken will not be of stars and a startracker program would spit out garbage
        #this can thus be just treated like a script which takes photos of the 'earth' from above!

        if recieved_command == "CMD:STARTRACKER":
            try:
                subprocess.run(["python3", "/home/mjolnir/CubeSat-Mjolnir/TestFiles/camera_test.py"], check=True)
            except subprocess.CalledProcessError as e:
                print(f"command failed with exit code {e.returncode}")
finally:
        print("Flight Computer Star Tracker Script Deactivated")
        Startracker_client.loop_stop()
        Startracker_client.disconnect()

