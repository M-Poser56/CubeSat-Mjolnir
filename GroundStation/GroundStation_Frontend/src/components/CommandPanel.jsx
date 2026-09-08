import { useState } from "react";
import "./CommandPanel.css";

// Backend link: POST /command on the same host as the serial WebSocket.
// Body: { command: string }. The backend queues it for the serial
// reader thread to write out to the Arduino.
const COMMAND_URL = "http://localhost:8765/command";

function CommandPanel() {
  const [command, setCommand] = useState("");
  const [status, setStatus] = useState(null); // "sent" | "error" | null
  const [sending, setSending] = useState(false);

  async function sendCommand(e) {
    e.preventDefault();
    const trimmed = command.trim();
    if (!trimmed || sending) return;

    setSending(true);
    setStatus(null);
    try {
      const res = await fetch(COMMAND_URL, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ command: trimmed }),
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      setStatus("sent");
      setCommand("");
    } catch {
      setStatus("error");
    } finally {
      setSending(false);
    }
  }

  return (
    <form className="command-panel" onSubmit={sendCommand}>
      <input
        className="command-input"
        type="text"
        value={command}
        onChange={(e) => setCommand(e.target.value)}
        placeholder="Enter command..."
        spellCheck={false}
        autoComplete="off"
      />
      <button className="command-send" type="submit" disabled={sending || !command.trim()}>
        Send
      </button>
      {status === "sent" && <span className="command-status command-status-ok">Sent</span>}
      {status === "error" && <span className="command-status command-status-err">Send failed</span>}
    </form>
  );
}

export default CommandPanel;
