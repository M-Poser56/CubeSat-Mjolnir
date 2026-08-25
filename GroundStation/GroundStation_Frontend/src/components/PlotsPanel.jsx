import useOrientationStream from "../hooks/useOrientationStream";
import SensorPlot from "./SensorPlot";
import "./PlotsPanel.css";

function PlotsPanel() {
  const data = useOrientationStream();

  return (
    <div className="plots-panel">
      <SensorPlot label="Pitch" dataKey="pitch" color="#c0392b" data={data} />
      <SensorPlot label="Roll" dataKey="roll" color="#2471a3" data={data} />
      <SensorPlot label="Yaw" dataKey="yaw" color="#1a8a3d" data={data} />
    </div>
  );
}

export default PlotsPanel;
