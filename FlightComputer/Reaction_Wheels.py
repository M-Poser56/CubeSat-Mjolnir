#downstream script for reaction wheels functionality

#this will follow the same (rough) architecture as the Mjolnir_Reboot.py and
#Star_tracker.py scripts, but will be a little bit more depth

#this script, will take in command information, and after some initialization of
#GPIO output & PWM pins, update the state of the onboard reaction wheel controls
#the flow of the script will recieve messages in the same way as the other two,
#but will update GPIO settings instead of running a subprocess command function

import queue
import paho.mqtt.client as mqtt
import RPi.GPIO as GPIO
import re

reactionwheels_queue = queue.Queue() #initialize script local queue to store upstream command messages


#mqtt functions (for reboot script)
def on_connect(client, userdata, flags, reason_code, properties):
    print(f"mqtt localhost connected with result code {reason_code}")
    client.subscribe("CMD/REACTIONWHEELS") #upstream being published to by LoRA_ULDL in the CommandHandler() function

def on_message(client, userdata, msg):
    reactionwheels_queue.put(msg.payload.decode()) #adds command string to queue, FIFO

ReactionWheels_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
ReactionWheels_client.on_connect = on_connect
ReactionWheels_client.on_message = on_message
ReactionWheels_client.connect("localhost", 1883)
ReactionWheels_client.loop_start()

#GPIO initialization
motor_logic_switch = [GPIO.LOW,GPIO.LOW] #digital directionality pins, 1/0 and 0/1 for CW/CCW. These are pins 16, 18 in order
motor_logic_pins = [16, 18]
M1_pwm_pin = 29 #all physical board pins
M2_pwm_pin = 31
M3_pwm_pin = 37
pwm_Hz = 490 #matches arduino Uno test frequency
GPIO.setmode(GPIO.BOARD)
GPIO.setwarnings(False)

#motor logic setup
GPIO.setup(motor_logic_pins[0], GPIO.OUT, initial=GPIO.LOW)
GPIO.setup(motor_logic_pins[1], GPIO.OUT, initial=GPIO.LOW)
#motor pwm setup, start all at 0% pwm
GPIO.setup(M1_pwm_pin, GPIO.OUT)
GPIO.setup(M2_pwm_pin, GPIO.OUT)
GPIO.setup(M3_pwm_pin, GPIO.OUT)
M1_pwm = GPIO.PWM(M1_pwm_pin, pwm_Hz)
M2_pwm = GPIO.PWM(M2_pwm_pin, pwm_Hz)
M3_pwm = GPIO.PWM(M3_pwm_pin, pwm_Hz)
M1_pwm.start(0)
M2_pwm.start(0)
M3_pwm.start(0)
#initialize p1, p2, p3 values ahead of time for thoroughness (also for first command)
p1 = 0
p2 = 0
p3 = 0



try:
    while True:
        recieved_command = reactionwheels_queue.get()

        #first step is to parse the string, to determine both the direction of the wheels
        #and the values of each PWM to update string is of the below form:
        #"CMD:REACTIONWHEELS{INT,INT,INT}" where any of the ints can be signed either way
        match = re.fullmatch(r"CMD:REACTIONWHEELS\{(-?\d+),(-?\d+),(-?\d+)\}", recieved_command)
        if match:
            p1, p2, p3 = (int(g) for g in match.groups()) #pulls the ints out of the string, as ints

        #2 - determine if first int is negative (and change logic accordingly)
        if p1 < 0:
            motor_logic_switch = [GPIO.LOW, GPIO.HIGH]
        else:
            motor_logic_switch = [GPIO.HIGH, GPIO.LOW]
        #set logic/direction states
        GPIO.output(motor_logic_pins[0], motor_logic_switch[0])
        GPIO.output(motor_logic_pins[1], motor_logic_switch[1])

        #3 - update PWM values for each individual object, based on p1/p2/p3
        #safety check, if inputted pwm% (pn variable) is over 100, set to 0
        if abs(p1) > 100:
            p1 = 0
        if abs(p2) > 100:
            p2 = 0
        if abs(p3) > 100:
            p3 = 0
        #set pwm values
        M1_pwm.ChangeDutyCycle(abs(p1))
        M2_pwm.ChangeDutyCycle(abs(p2))
        M3_pwm.ChangeDutyCycle(abs(p3))
        

finally:
        print("Reaction Wheel motor control Script Deactivated")
        ReactionWheels_client.loop_stop()
        ReactionWheels_client.disconnect()
        M1_pwm.stop()
        M2_pwm.stop()
        M3_pwm.stop()
        GPIO.cleanup()

