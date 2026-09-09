import { useEffect, useState } from "react";
import "./App.css";
import Tile from "./components/Tile";
import Clock from "./components/Clock";
import PlotsPanel from "./components/PlotsPanel";
import SerialTerminal from "./components/SerialTerminal";
import CommandPanel from "./components/CommandPanel";
import ReactionWheelPanel from "./components/ReactionWheelPanel";
import TemperaturePanel from "./components/TemperaturePanel";
import useOrientationStream from "./hooks/useOrientationStream";
import { formatEstTime } from "./utils/time";
import mjolnirLogo from "./assets/mjolnir-logo.png";

const SATELLITE_UNKNOWN_MS = 60 * 1000;
const SATELLITE_DOWN_MS = 5 * 60 * 1000;

//frontend UI for the groundstation app & stack
//I will have a few features in the window, basic stylistic details are noted below
/*
Font: NASA

Features:
Live serial terminal
Plots of orientation and temp against time
write command palate & send command button


*/


function App() {
  const [wheelSpeeds, setWheelSpeeds] = useState({ pitch: 0, roll: 0, yaw: 0 });
  const [wheelDirection, setWheelDirection] = useState("FWD");
  const { data: orientationData, connected: radioConnected } = useOrientationStream();
  const lastPacket = orientationData[orientationData.length - 1];
  const lastPacketTime = lastPacket ? formatEstTime(lastPacket.t) : "--:--:--";

  // Ticks once a second so the radio status can degrade over time even
  // when no new packets are arriving to trigger a re-render.
  const [now, setNow] = useState(Date.now());
  useEffect(() => {
    const id = setInterval(() => setNow(Date.now()), 1000);
    return () => clearInterval(id);
  }, []);

  // Groundstation Radio Status reflects only whether the backend's
  // WebSocket link is up — a simple connected/not-connected reading.
  const radioStatusText = radioConnected ? "Good" : "Down";
  const radioStatusClass = radioConnected ? "status-good" : "status-down";

  // Satellite Status depends only on how long it's been since the last
  // packet arrived — independent of whether the backend link is up.
  let satelliteStatusText = "Unknown";
  let satelliteStatusClass = "status-warn";
  if (lastPacket) {
    const sinceLastPacket = now - lastPacket.t;
    if (sinceLastPacket > SATELLITE_DOWN_MS) {
      satelliteStatusText = "Down";
      satelliteStatusClass = "status-down";
    } else if (sinceLastPacket > SATELLITE_UNKNOWN_MS) {
      satelliteStatusText = "Unknown";
      satelliteStatusClass = "status-warn";
    } else {
      satelliteStatusText = "Good";
      satelliteStatusClass = "status-good";
    }
  }

  return (
    <div className="dashboard">
      <div className="left-column">
        <Tile title="Plots" className="tile-large">
          <PlotsPanel />
        </Tile>
        <div className="bottom-row">
          <Tile title="Temperature" className="tile-small">
            <TemperaturePanel />
          </Tile>
          <Tile title="Reaction Wheel Control" className="tile-small">
            <ReactionWheelPanel
              speeds={wheelSpeeds}
              onChange={setWheelSpeeds}
              direction={wheelDirection}
              onDirectionChange={setWheelDirection}
            />
          </Tile>
        </div>
      </div>
      <div className="right-column">
        <div className="bottom-row">
          <Tile title="Serial term" className="tile-small">
            <SerialTerminal />
          </Tile>
          <Tile className="tile-small">
            <div className="title-panel">
              <div className="title-header">
                <p className="tile5-caption">
                  Mjolnir CubeSat GroundStation
                  <br />
                  Matt Poser, 2026
                </p>
                <img
                  className="title-logo"
                  src={mjolnirLogo}
                  alt="Mjolnir emblem"
                />
              </div>
              <div className="clock-row">
                <Clock />
                <span className="clock-label">(EST)</span>
              </div>
              <p className="status-lines">
                Groundstation Radio Status:{" "}
                <span className={radioStatusClass}>{radioStatusText}</span>
                <br />
                Satellite Status:{" "}
                <span className={satelliteStatusClass}>{satelliteStatusText}</span>
                <br />
                Last Packet: <span className="status-time">{lastPacketTime}</span>
              </p>
            </div>
          </Tile>
        </div>
        <Tile title="Command Panel" className="tile-large">
          <CommandPanel wheelSpeeds={wheelSpeeds} wheelDirection={wheelDirection} />
        </Tile>
      </div>
    </div>
  );
}
 
export default App;
 