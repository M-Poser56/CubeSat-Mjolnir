import { useState } from "react";
import "./CommandPanel.css";

// Backend link: POST /command on the same host as the serial WebSocket.
// Body: { command: string }. The backend queues it for the serial
// reader thread to write out to the Arduino.
const COMMAND_URL = "http://localhost:8765/command";

// Preset buttons insert a placeholder command string into the input
// without sending it, so the operator can review/edit before hitting Send.
const PRESET_COMMANDS = [
  { label: "Reporting Interval Change", value: "CMD:INTERVAL <seconds>" },
  { label: "Take Photo", value: "CMD:STARTRACKER" },
  { label: "Reboot Satellite", value: "CMD:REBOOT" },
];

function CommandPanel({ wheelSpeeds, wheelDirection }) {
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
    <div className="command-panel">
      <form className="command-form" onSubmit={sendCommand}>
        <div className="command-input-row">
          <input
            className="command-input"
            type="text"
            value={command}
            onChange={(e) => setCommand(e.target.value)}
            placeholder="COMMAND STRING"
            spellCheck={false}
            autoComplete="off"
          />
          <button className="command-send" type="submit" disabled={sending || !command.trim()}>
            Send
          </button>
          {status === "sent" && <span className="command-status command-status-ok">Sent</span>}
          {status === "error" && <span className="command-status command-status-err">Send failed</span>}
        </div>
        <div className="command-presets">
          {PRESET_COMMANDS.map((preset) => (
            <button
              key={preset.label}
              type="button"
              className="command-preset"
              onClick={() => setCommand(preset.value)}
            >
              {preset.label}
            </button>
          ))}
          <button
            type="button"
            className="command-preset"
            onClick={() => {
              const sign = wheelDirection === "REV" ? "-" : "";
              setCommand(
                `CMD:REACTIONWHEELS{${sign}${wheelSpeeds.pitch},${sign}${wheelSpeeds.roll},${sign}${wheelSpeeds.yaw}}`
              );
            }}
          >
            Reaction Wheel Speeds
          </button>
        </div>
      </form>
      {/* Guide text — edit these paragraphs to document available commands. */}
      <div className="command-guide">
        <p>
          The mjolnir CubeSat command panel can be operated to send string commands
          to the mjolnir cubesat's command handler, and parsed to perform specific functions
          on board. Any strings not following the specific CMD:"keyword" format with a valid
          keyword will be thrown out by the handler. Using the buttons will fill the command
          form with the valid command syntax
        </p>
        <p>
          Below, are the lists of valid commands and their usages
        </p>
        <p>
          <b>(1) CMD:INTERVAL {'<'}seconds{'>'}</b> used to change the onboard data reporting interval.
           It is recommended that this value is between 1-29 seconds, or you could risk the cubesat not 
           recieving updated interval commands
        </p>
        <p>
          <b>(2) CMD:STARTRACKER</b> used to operate the mjolnir onboard camera
           This command will take a photo with the onboard camera, stored locally
            to provide later to the startracker program
        </p>
        <p>
          <b>(3) CMD:REBOOT</b> reboots the mjolnir flight computer. Upon restart,
          packet reporting interval is set by default to 5 seconds
        </p>
        <p>
          <b>(4) CMD:REACTIONWHEELS{'{v1,v2,v3}'}</b> changes the onboard pitch, roll, yaw reaction wheel speeds. This
           command is meant to be used in conjunction with the live pitch/roll/yaw angular orientation
           plots, and it is not recommended to have huge jumps in speed, and set the speed to zero before
           swapping from FWD-{'>'}REV, and vice versa
        </p>
      </div>
    </div>
  );
}

export default CommandPanel;
