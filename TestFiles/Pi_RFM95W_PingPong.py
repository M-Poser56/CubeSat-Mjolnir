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
    # Block until a packet arrives (check every 100ms)
    packet = rfm9x.receive(timeout=30.0)

    if packet is None:
        print("Still waiting...")
        continue

    # Decode and display the received ping
    try:
        message = packet.decode("utf-8").strip("\x00")
    except UnicodeDecodeError:
        message = str(packet)

    pong_count += 1
    print(f"Received : {message}")
    print(f"  RSSI   : {rfm9x.last_rssi} dBm")
    print(f"  SNR    : {rfm9x.last_snr} dB")

    # Send PONG back
    response = f"PONG {pong_count}".encode("utf-8")
    rfm9x.send(response)
    print(f"Sent     : PONG {pong_count}")
    print("-" * 40)
