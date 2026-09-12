#downstream script for reboot functionality

#this follows the exact same structure as Star_Tracker.py (at the moment), but with different
#local mqtt topics, and different subprocess commands

import queue
import paho.mqtt.client as mqtt
import re
import subprocess

reboot_queue = queue.Queue() #initialize script local queue to store upstream command messages


#mqtt functions (for reboot script)
def on_connect(client, userdata, flags, reason_code, properties):
    print(f"mqtt localhost connected with result code {reason_code}")
    client.subscribe("CMD/REBOOT") #upstream being published to by LoRA_ULDL in the CommandHandler() function

def on_message(client, userdata, msg):
    reboot_queue.put(msg.payload.decode()) #adds command string to queue, FIFO

Reboot_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
Reboot_client.on_connect = on_connect
Reboot_client.on_message = on_message
Reboot_client.connect("localhost", 1883)
Reboot_client.loop_start()

#this system service script is going to be oneshot, as we can only reboot
#once within an operating system cycle. queue.get() is a blocking function,
#so once we recieve this command we can just immediately run our
#system reboot, and have it be done with

recieved_command = reboot_queue.get()

if recieved_command == "CMD:REBOOT": #redundant check, only thing being published to this topic is this command from the handler
    try:
        subprocess.run(["sudo", "/usr/sbin/reboot"], check=True)
    except subprocess.CalledProcessError as e:
        print(f"command failed with exit code {e.returncode}")

#I had to make this a passwordless command by adding some configs to
# sudo visudo -f /etc/sudoers.d/myuser-systemctl, but change for mjolnir-reboot
#within this file, I added: mjolnir ALL=(root) NOPASSWD: /usr/sbin/reboot
#now, callable from subprocess or the CLI, sudo /usr/sbin/reboot does not require a password
