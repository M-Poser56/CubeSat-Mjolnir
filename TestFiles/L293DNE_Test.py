#Python script for testing/running a 5V L293DNE H Bridge Chip, with 3V3 switching (PWM)
#

"""
for controlling the H-Bridge:

Direction pins 1,2 -> board pins 16,18
PWM Pin - board pin 22

For the direction pins, assuming constant EN PWM, 1/0 and 0/1 are opposite directions from one another, and 0/0 is our brake mode

lit!
"""

#flow of the code will be as follows:
#spin motor one way, brake & delay, spin motor the other way, brake & delay, repeat
# If this works, then I'll have my setup. 

import RPi.GPIO as GPIO
import time

PIN_1A = 16   # digital output
PIN_2A = 18   # digital output
PIN_EN = 22   # PWM output
PWM_FREQ_HZ = 490
delay_s=2

GPIO.setmode(GPIO.BOARD)
GPIO.setwarnings(False)
GPIO.setup(PIN_1A, GPIO.OUT)
GPIO.setup(PIN_2A, GPIO.OUT)
GPIO.setup(PIN_EN, GPIO.OUT)

pwm = GPIO.PWM(PIN_EN, PWM_FREQ_HZ)
pwm.start(0)
GPIO.output(PIN_1A, GPIO.LOW)
GPIO.output(PIN_2A, GPIO.LOW)
time.sleep(delay_s)
#turn motor clockwise, and anticlockwise on loop
print("starting test")
try:
	while(True):
		#on loop, move between both directions
		pwm.ChangeDutyCycle(30) #30%
		GPIO.output(PIN_1A, GPIO.LOW)
		GPIO.output(PIN_2A, GPIO.HIGH)
		time.sleep(delay_s)
		#braking
		GPIO.output(PIN_1A, GPIO.LOW)
		GPIO.output(PIN_2A, GPIO.LOW)
		time.sleep(delay_s)
		#anti-clockwise
		GPIO.output(PIN_1A, GPIO.LOW)
		GPIO.output(PIN_2A, GPIO.HIGH)
		time.sleep(delay_s)
		#braking
		GPIO.output(PIN_1A, GPIO.LOW)
		GPIO.output(PIN_2A, GPIO.LOW)
		time.sleep(delay_s)
		print("cycle complete")


finally:
	pwm.ChangeDutyCycle(0)
	GPIO.output(PIN_1A, GPIO.LOW)
	GPIO.output(PIN_2A, GPIO.LOW)
	pwm.stop()
	GPIO.cleanup()


"""
dev notes:
circuit works exactly as expected. I would recommend that 30% is the lowest applied PWM here,
as the motor is basically useless at that point. Further, with the motor's red terminal tied to 1A,
and black to 2A, the above configuration produces clockwise motion (GND HIGH, RED LOW). I checked
this to be true, all motors have the wirings the same way.

L293DNE Circuit should be good to go from here. It is worth noting that for the 2nd ICs unused side, I will leave it floating.
One sided test showed no issues with this, and further it seems like the output of the motor driver pins was high after gpio.cleanup.
Will still ground both sides. Can proceed to PCB
"""
