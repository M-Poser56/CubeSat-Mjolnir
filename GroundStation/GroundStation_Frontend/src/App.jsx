import "./App.css";
import Tile from "./components/Tile";
import Clock from "./components/Clock";
import PlotsPanel from "./components/PlotsPanel";
import SerialTerminal from "./components/SerialTerminal";
import CommandPanel from "./components/CommandPanel";

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
  return (
    <div className="dashboard">
      <div className="left-column">
        <Tile title="Plots" className="tile-large">
          <PlotsPanel />
        </Tile>
        <div className="bottom-row">
          <Tile title="Temperature" className="tile-small" />
          <Tile title="Reaction Wheel Control" className="tile-small" />
        </div>
      </div>
      <div className="right-column">
        <div className="bottom-row">
          <Tile title="Serial term" className="tile-small">
            <SerialTerminal />
          </Tile>
          <Tile className="tile-small">
            <p className="tile5-caption">
              Mjolnir CubeSat GroundStation
              <br />
              Matt Poser, 2026
            </p>
            <div className="clock-row">
              <Clock />
              <span className="clock-label">(EST)</span>
            </div>
            <p className="status-lines">
              Radio Status: <span className="status-good">Good</span>
              <br />
              Satellite Status: <span className="status-good">Good</span>
            </p>
          </Tile>
        </div>
        <Tile title="Command Panel" className="tile-large">
          <CommandPanel />
        </Tile>
      </div>
    </div>
  );
}
 
export default App;
 