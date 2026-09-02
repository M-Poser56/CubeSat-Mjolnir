"""
M Poser, August 19th 2026
This is the script which uses the web API to broadcast packets coming from the Arduino
up to the local JS frontend. It is a simple thru/script, with it's main role to be
reading the packets coming from the Arduino, and occasionally sending a formatted command
along the serial bus to the Arduino to then send to the cubesat

Run with:  python GroundStation_Backend.py
Serves a WebSocket at ws://localhost:8765/serial that the frontend's
SerialTerminal widget connects to. Each completed line read off the
Arduino's serial port is broadcast to every connected browser tab as
its own text message.
"""

import asyncio
import threading
import time

import serial
import serial.tools.list_ports
from fastapi import FastAPI, WebSocket, WebSocketDisconnect

BAUD = 115200
PORT_SCAN_INTERVAL = 2.0  # seconds between retries while no Arduino is found

app = FastAPI()

clients: set[WebSocket] = set()
line_queue: asyncio.Queue[str] = asyncio.Queue()


def find_arduino_port() -> str | None:
    for p in serial.tools.list_ports.comports():
        if "Arduino" in p.description:
            return p.device
    return None


def serial_reader(loop: asyncio.AbstractEventLoop) -> None:
    """Runs in a background thread (pyserial is blocking). Reconnects
    automatically if the Arduino isn't plugged in yet or drops out."""
    ser: serial.Serial | None = None
    while True:
        if ser is None:
            port = find_arduino_port()
            if port is None:
                time.sleep(PORT_SCAN_INTERVAL)
                continue
            try:
                ser = serial.Serial(port, BAUD, timeout=1)
            except serial.SerialException:
                ser = None
                time.sleep(PORT_SCAN_INTERVAL)
                continue

        try:
            raw = ser.readline()
        except serial.SerialException:
            ser.close()
            ser = None
            continue

        line = raw.decode("utf-8", errors="replace").strip()
        if line:
            asyncio.run_coroutine_threadsafe(line_queue.put(line), loop)


async def broadcaster() -> None:
    while True:
        line = await line_queue.get()
        dead = []
        for ws in clients:
            try:
                await ws.send_text(line)
            except Exception:
                dead.append(ws)
        for ws in dead:
            clients.discard(ws)


@app.on_event("startup")
async def startup() -> None:
    loop = asyncio.get_running_loop()
    threading.Thread(target=serial_reader, args=(loop,), daemon=True).start()
    asyncio.create_task(broadcaster())


@app.websocket("/serial")
async def serial_ws(websocket: WebSocket) -> None:
    await websocket.accept()
    clients.add(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        clients.discard(websocket)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8765)
