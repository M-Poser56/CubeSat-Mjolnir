#LoRA Uplink/downlink (work in progress)
import time
import board
import busio
import digitalio
import adafruit_rfm9x

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
    return "90, 90, 75, 25*C" #dummy, for now



def Downlink(packet):
    #method which sends sensor packet down
    #acknowledgement means it tries a few times, 2.5 seconds of attempts
    rfm9x.send_with_ack(packet.encode("utf-8"))

    

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
    return None #catch all, if the command is nothing

def timeout_change(gndstation_command):
    global current_timeout
    new_timeout=gndstation_command #need to properly parse this line
    current_timeout = new_timeout


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
        if gndstation_command is not None:
            #parse string here to change timeout value
            timeout_change(gndstation_command)

        #at the moment, the command simply is to change the
        #timeout/loop delay value for getting sensor packets
        #Once this is fully implemented, what I want to do 
        #is to have reaction wheel control, as well as
        #timeout changes



finally:
    print("Flight Computer Uplink/Downlink Deactivated")
        

    



