#FlightLoop.py - main flight loop for the StratoStar Flight 1 configuration

#standard library
import time
import re
import queue
import threading
import subprocess
from datetime import datetime

#local mqtt (inter-script communication)
import paho.mqtt.client as mqtt

#hardware - Blinka (I2C/SPI/digital pins)
import board
import busio
import digitalio

#hardware - sensor & radio drivers
import adafruit_bno055 #IMU
import adafruit_rfm9x  #LoRa radio

#hardware - GPIO/PWM (reaction wheels)
import RPi.GPIO as GPIO

print("successfully ran")
