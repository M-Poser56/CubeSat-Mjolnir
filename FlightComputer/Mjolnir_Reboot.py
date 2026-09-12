#downstream script for reboot functionality

#this follows the exact same structure as Star_Tracker.py (at the moment), but with different
#local mqtt topics, and different subprocess commands

import queue
import paho.mqtt.client as mqtt
import re

command_queue = queue.Queue() #initialize script local queue to store upstream command messages


#mqtt functions (for reboot script)
def on_connect(client, userdata, flags, reason_code, properties):
    print(f"mqtt localhost connected with result code {reason_code}")
    client.subscribe("CMD/REBOOT") #upstream being published to by LoRA_ULDL in the CommandHandler() function

def on_message(client, userdata, msg):
    command_queue.put(msg.payload.decode()) #adds command string to queue, FIFO

Reboot_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
Reboot_client.on_connect = on_connect
Reboot_client.on_message = on_message
Reboot_client.connect("localhost", 1883)
Reboot_client.loop_start()




