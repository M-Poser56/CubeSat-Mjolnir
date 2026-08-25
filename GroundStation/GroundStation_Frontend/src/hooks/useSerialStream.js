import { useEffect, useState } from "react";

// Backend link: the Python backend should serve a WebSocket here and
// send one text message per received packet. Each message becomes one
// completed line in the terminal.
const SERIAL_WS_URL = "ws://localhost:8765/serial";

function useSerialStream() {
  const [lines, setLines] = useState([]);
  const [connected, setConnected] = useState(false);

  useEffect(() => {
    const socket = new WebSocket(SERIAL_WS_URL);

    socket.onopen = () => setConnected(true);
    socket.onclose = () => setConnected(false);
    socket.onerror = () => setConnected(false);
    socket.onmessage = (event) => {
      setLines((prev) => [...prev, event.data]);
    };

    return () => socket.close();
  }, []);

  return { lines, connected };
}

export default useSerialStream;
