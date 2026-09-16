#LoRA Uplink/downlink (work in progress)
import time
import board
import busio
import digitalio
import adafruit_rfm9x
from datetime import datetime
import re
import paho.mqtt.client as mqtt
import threading



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
IMU_PACKET = "No_Packets_Recieved"

def SensorPacket():
    sensor_packet_temp = Fetch() 
    #Fetch() is a function that just returns
    #the latest IMU packet value, using 
    #global variable & mqtt architecture
    #(threaded variable updating)
    """
    The sensor packet must be in the following serialized string format:
    {int, int, int, intC, HH:MM:SS}
    pitch, roll, yaw, temp+C, timestamp
    """
    timestamp = datetime.now().strftime("%H:%M:%S")
    
    downlink_packet = f"{{{sensor_packet_temp}, {timestamp}}}"
    
    return downlink_packet 

def Fetch():
    #function for fetching the most recent IMU & temp data from internal
    #mqtt topic/queue
    #this function fetches from the top of the queue, 'instantaneous'
    return IMU_PACKET #global variable updated by on_message()

def CommandHandler(temp2command):
    #debug
    print(40*"*")
    print(f"CMD: VALID HANDLER COMMAND RECIEVED: {temp2command}")
    print(40*"*")

    #instantaneous mqtt local publish here
    LoRA_ULDL_client.publish("CMD/HANDLER", temp2command.strip()) #gets rid of any trailing spaces

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


def ListenThreaded(timeout): #claude's wrapper function, to address the 2 packets back to back bug
    #runs Listen() and a matching sleep concurrently, and doesn't return until
    #BOTH finish -- guarantees this call always takes at least `timeout` seconds,
    #even if a packet (and its ack) comes back almost instantly
    result = {}

    def _worker():
        result["command"] = Listen(timeout)

    listen_thread = threading.Thread(target=_worker)
    sleep_thread = threading.Thread(target=time.sleep, args=(timeout,))

    listen_thread.start()
    sleep_thread.start()
    listen_thread.join()
    sleep_thread.join()

    return result["command"]

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


#mqtt specific
def on_connect(client, userdata, flags, reason_code, properties):
    print(f"mqtt localhost connected with result code {reason_code}")
    client.subscribe("IMU/PACKET")

def on_publish(client, userdata, mid, reason_codes, properties):
    print(f"Published message id {mid}")

def on_message(client, userdata, msg):
    global IMU_PACKET #for immediate updating in the Fetch() function
    IMU_PACKET = msg.payload.decode().strip()
    #the updating of this global variable
    #on a newly recieved message means that
    #the newest data from the IMU is always
    #returned by the fetch function, this
    #threaded function runs in the background



LoRA_ULDL_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
LoRA_ULDL_client.on_connect = on_connect
LoRA_ULDL_client.on_message = on_message 
LoRA_ULDL_client.on_publish = on_publish
LoRA_ULDL_client.connect("localhost", 1883)
LoRA_ULDL_client.loop_start()



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
        gndstation_command = ListenThreaded(current_timeout) #wrapper function, which calls Listen()
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
    LoRA_ULDL_client.loop_stop()
    LoRA_ULDL_client.disconnect()