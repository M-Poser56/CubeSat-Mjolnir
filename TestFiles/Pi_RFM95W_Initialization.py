# detect.py (written by Claude)
import board
import busio
import digitalio
import adafruit_rfm9x

print("RFM95W Detection Test")
print("---------------------")

# Pin setup
CS    = digitalio.DigitalInOut(board.CE1)   # GPIO 7
RESET = digitalio.DigitalInOut(board.D17)   # GPIO 17

# SPI bus
spi = busio.SPI(board.SCK, MOSI=board.MOSI, MISO=board.MISO)

try:
    rfm9x = adafruit_rfm9x.RFM9x(spi, CS, RESET, 915.0)
    print("PASS — RFM95W detected!")
    print(f"  Frequency : 915.0 MHz")
    print(f"  TX Power  : {rfm9x.tx_power} dBm")
    print("Detection test complete. Ready.")

except RuntimeError as e:
    print(f"FAIL — Could not initialize RFM95W: {e}")
    print("  - Is VIN on 3.3V?")
    print("  - Check SCK/MOSI/MISO/CS/RST/G0 wiring")
    print("  - Is SPI enabled? Run: ls /dev/spidev*")
