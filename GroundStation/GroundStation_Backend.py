"""
M Poser, August 19th 2026
This is the script which uses the web API to broadcast packets coming from the Arduino
up to the local JS frontend. It is a simple thru/script, with it's main role to be
reading the packets coming from the Arduino, and occasionally sending a formatted command
along the serial bus to the Arduino to then send to the cubesat

"""

#library imports
import serial.tools.list_ports
import serial


#as an initial startup, find the Arduino device. Latch onto the associate COM port
#I'll be running this from Windows
PORT = ""
BAUD = 115200
for p in serial.tools.list_ports.comports():
    if "Arduino" in p.description:
        PORT = p.device.strip()


#we now have the port that the Uno is running on. This is our serial bus for the duration of
#our Groundstation backend
#initialize serial
ser = serial.Serial(PORT, BAUD, timeout=99)

while True:
    line = ser.readline().decode("utf-8", errors="replace").strip()
    if line:
        print(line)

#working! Will coordinate with frontend later



