#LoRA Uplink/downlink (work in progress)
import time
import board
import busio
import digitalio
import adafruit_rfm9x
from datetime import datetime
import re


#SPI setup, pins
CS    = digitalio.DigitalInOut(board.CE1)   #GPIO 7
RESET = digitalio.DigitalInOut(board.D17)   #GPIO 17
spi = busio.SPI(board.SCK, MOSI=board.MOSI, MISO=board.MISO)
#radio configs
rfm9x = adafruit_rfm9x.RFM9x(spi, CS, RESET, 915.0)
rfm9x.tx_power = 14

rfm9x.node = 1           #CubeSat's Address
rfm9x.destination = 2    #Groundstation's Address
rfm9x.ack_wait = 0.5     #delay before retry
rfm9x.ack_retries = 5    #number of retries
rfm9x.ack_delay = 0.15   #delay before the receiver sends its ACK
current_timeout = 5.0 #seconds, of delay, as our starting value
#****when arduino sends a command, it needs to be
#at least the length of time of the send with ack function
#from the flight computer, preferrably double

def SensorPacket():
    #method which will query mqtt internal
    #server to retrieve angular orientation, and temp

    #call function here which pulls from local mqtt queue
    sensor_packet_temp = Fetch()

    """
    The sensor packet must be in the following serialized string format:
    {int, int, int, intC, HH:MM:SS}
    pitch, roll, yaw, temp+C, timestamp
    """
    timestamp = datetime.now().strftime("%H:%M:%S")
    #add sensor_packet_temp here, same fashion as timestamp into dummy
    dummy = f"{{90, 90, 25, 27C, {timestamp}}}"
    #need to properly make and serialize this


    

    return dummy #dummy, for now

def Fetch():
    #function for fetching the most recent IMU & temp data from internal
    #mqtt topic/queue
    #this function fetches from the top of the queue, 'instantaneous'
    return

def CommandHandler(temp2command):
    #debug
    print(40*"*")
    print(f"CMD: VALID HANDLER COMMAND RECIEVED: {temp2command}")
    print(40*"*")

    #instantaneous mqtt local publish here

    return

def Downlink(packet):
    #method which sends sensor packet down
    #acknowledgement means it tries a few times, 2.5 seconds of attempts
    rfm9x.send_with_ack(packet.encode("utf-8"))
    return

    

def Listen(current_timeout):
    #method for listening for packets (acknowledge)
    #for a set timeout, this is the timeout which will be changed by the command
    #coming from groundstation
    command_bytes = rfm9x.receive(with_ack=True, timeout=current_timeout)
    if command_bytes is not None:
        command = command_bytes.decode()
        print(40*"*")
        print(f"COMMAND RECIEVED: {command}")
        print(40*"*")
        return command
    return "NO COMMAND" #catch all, if the command is nothing

def TimeoutChange(temp1_command):
    global current_timeout
    try:
        new_timeout = float(temp1_command)
    except ValueError: #this is an old check, should never run but I'm keeping it in
        print(f"Ignoring non-numeric command: {temp1_command!r}")
        return
    current_timeout = new_timeout
    print(f"PACKET INTERVAL CHANGED TO: {current_timeout}")
    return


try:
    while True:
        #main flow of program, on flight computer

        #step 1, obtain sensor data
        #How long does this take to run?
        #hoping 'instantaneous
        sensor_data = SensorPacket()

        #step 2, broadcast packet down. This should
        #be "instantaneous"
        Downlink(sensor_data)

        #step 3, listen for incoming commands.
        #this will be our timeout, how long do I listen for
        #before the loop repeats. Need to change on the fly
        gndstation_command = Listen(current_timeout)
        if bool(re.fullmatch(r"CMD:INTERVAL \d+", gndstation_command)): #if command is a timeout change valid command
            #parse string here to change timeout value
            gndstation_command = gndstation_command.strip().split()[-1] #fetching <seconds>
            TimeoutChange(gndstation_command) #casts string to float for assignment
        elif gndstation_command.startswith("CMD:"):
            #string is a valid command format, pass it to the handler for further checking
            CommandHandler(gndstation_command)

        #end of main LoRA ULDL loop





finally:
    print("Flight Computer Uplink/Downlink Deactivated")