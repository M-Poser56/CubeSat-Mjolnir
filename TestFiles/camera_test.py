from picamera2 import Picamera2
from datetime import datetime
import os

def take_photo(output_dir=os.path.expanduser("~"), fmt="jpg"):
    cam = Picamera2()

    # Configure for still capture
    config = cam.create_still_configuration(
        main={"size": (3280, 2464)}  # Full resolution for V2 camera
    )
    cam.configure(config)

    cam.start()

    # Build filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"photo_{timestamp}.{fmt}"
    filepath = os.path.join(output_dir, filename)

    cam.capture_file(filepath)
    cam.stop()
    cam.close()

    print(f"Photo saved to: {filepath}")
    return filepath

if __name__ == "__main__":
    take_photo()
