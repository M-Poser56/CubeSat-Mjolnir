#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Apr 30 21:14:31 2026

@author: m_epo
"""

# lora_pong.py
import time
import board
import busio
import digitalio
import adafruit_rfm9x

print("Pi LoRa Ping-Pong Ready")
print("Waiting for PING from Arduino...")
print("-" * 40)

# Pin setup
CS    = digitalio.DigitalInOut(board.CE1)   # GPIO 7
RESET = digitalio.DigitalInOut(board.D17)   # GPIO 17

# SPI
spi = busio.SPI(board.SCK, MOSI=board.MOSI, MISO=board.MISO)

# Init radio — frequency and modem config must match Arduino
rfm9x = adafruit_rfm9x.RFM9x(spi, CS, RESET, 915.0)
rfm9x.tx_power = 14
# Default modem config is Bw125Cr45Sf128 — matches Arduino side

pong_count = 0

while True:
    pong_count += 1
    
    
    # Send PONG back
    response = f"Earth to Rocky! Count {pong_count}".encode("utf-8")
    rfm9x.send(response)
    print(f"Sent!     : PONG {pong_count}")
    print("-" * 40)
    
    
    
    time.sleep(3)
    
