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


def SensorPacket():
    #method which will query mqtt internal
    #server to retrieve angular orientation, and temp
    return "90, 90, 75, 25*C"



def Downlink(packet):
    #method which sends sensor packet down
    #acknowledgement means it tries a few times, 2.5 seconds of attempts
    rfm9x.send_with_ack(packet.encode("utf-8"))

    

def Listen():
    #method for listening for packets (acknowledge)
    #for a set timeout, this is the timeout which will be changed by the command
    #coming from groundstation
    command_bytes = rfm9x.receive(with_ack=True)
    if command_bytes is not None:
        command = command_bytes.decode()


while True:
    try:


    



