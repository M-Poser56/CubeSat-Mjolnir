import { useEffect, useState } from "react";

// Same backend socket as useSerialStream — every connected client gets
// every broadcast line, so this can listen independently without
// affecting the raw terminal feed.
const SERIAL_WS_URL = "ws://localhost:8765/serial";

// Cap how many points we keep so a long-running session doesn't grow
// the plot data (and the DOM) without bound.
const MAX_POINTS = 500;

// Sensor packet format: "{pitch, roll, yaw, tempC, HH:MM:SS}", e.g.
// "{-90, 90, 100, 25C, 14:03:22}". Lines that don't start with "{" are
// something else (command echoes, logs, etc.) and are left for the
// serial terminal to display as-is — they don't touch the plots.
function parsePacket(raw) {
  const trimmed = raw.trim();
  if (!trimmed.startsWith("{")) return null;

  const body = trimmed.replace(/^\{/, "").replace(/\}$/, "");
  const parts = body.split(",").map((p) => p.trim());
  if (parts.length < 5) return null;

  const [pitchStr, rollStr, yawStr, temp, timeStr] = parts;
  const pitch = Number(pitchStr);
  const roll = Number(rollStr);
  const yaw = Number(yawStr);
  if ([pitch, roll, yaw].some(Number.isNaN)) return null;

  const t = timeStringToEpochMs(timeStr);
  if (t === null) return null;

  return { t, pitch, roll, yaw, temp };
}

// Combines the packet's "HH:MM:SS" wall-clock time with today's date so
// it can sit on a time axis. Assumes the flight computer's clock and the
// browser are in the same timezone (EST, per the ground station clock).
function timeStringToEpochMs(timeStr) {
  const match = /^(\d{1,2}):(\d{1,2}):(\d{1,2})$/.exec(timeStr);
  if (!match) return null;
  const [, h, m, s] = match;
  const date = new Date();
  date.setHours(Number(h), Number(m), Number(s), 0);
  return date.getTime();
}

function useOrientationStream() {
  const [data, setData] = useState([]);

  useEffect(() => {
    const socket = new WebSocket(SERIAL_WS_URL);

    socket.onmessage = (event) => {
      const point = parsePacket(event.data);
      if (point === null) return;
      setData((prev) => [...prev.slice(-(MAX_POINTS - 1)), point]);
    };

    return () => socket.close();
  }, []);

  return data;
}

export default useOrientationStream;
