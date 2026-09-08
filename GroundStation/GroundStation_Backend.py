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

Also serves POST /command — the frontend's command button hits this
to queue a string that gets written out to the Arduino on the next
reader-thread cycle (commands are expected to be infrequent).
"""
import asyncio
import queue
import threading
import time
import serial
import serial.tools.list_ports
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

BAUD = 115200
PORT_SCAN_INTERVAL = 2.0  # seconds between retries while no Arduino is found

app = FastAPI()
# The frontend (Vite dev server) runs on a different origin than this
# backend, so the browser blocks the /command POST without this — the
# WebSocket connection isn't affected since browsers don't apply CORS
# to it the same way.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
clients: set[WebSocket] = set()
line_queue: asyncio.Queue[str] = asyncio.Queue()

# Thread-safe hand-off for outgoing commands: the FastAPI endpoint (event
# loop thread) puts here, the serial reader (background thread) drains it.
# A plain queue.Queue is used rather than asyncio.Queue because the
# consumer lives outside the event loop.
command_queue: queue.Queue[str] = queue.Queue()


class CommandRequest(BaseModel):
    command: str


def find_arduino_port() -> str | None:
    for p in serial.tools.list_ports.comports():
        if "Arduino" in p.description:
            return p.device
    return None


def serial_reader(loop: asyncio.AbstractEventLoop) -> None:
    """Runs in a background thread (pyserial is blocking). Reconnects
    automatically if the Arduino isn't plugged in yet or drops out.

    Before each blocking read, drains at most one pending outgoing
    command (if any) and writes it out. Commands are rare, so riding
    along on the existing ~1s readline() timeout cadence is plenty
    responsive without needing a second thread or a lock on `ser`."""
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

        # --- outgoing: send a queued command, if any, before reading ---
        try:
            command = command_queue.get_nowait()
        except queue.Empty:
            command = None

        if command is not None:
            try:
                ser.write(command.encode("utf-8"))  # no trailing \n —
                # the Arduino reads via a short-timeout readString(),
                # not a newline-delimited read
                asyncio.run_coroutine_threadsafe(
                    line_queue.put(f"> {command}"), loop
                )
            except serial.SerialException:
                ser.close()
                ser = None
                continue

        # --- incoming: unchanged from before ---
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


@app.post("/command")
async def send_command(req: CommandRequest) -> dict:
    """Called by the frontend's command button. Queues the command for
    the serial reader thread to write out — does not block on the
    write itself, and does not wait for any response from the Arduino."""
    command_queue.put(req.command)
    return {"status": "queued", "command": req.command}


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