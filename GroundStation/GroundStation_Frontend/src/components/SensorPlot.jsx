import { Line, LineChart, ResponsiveContainer, XAxis, YAxis } from "recharts";
import { formatEstTime } from "../utils/time";
import "./SensorPlot.css";

const axisTick = { fontSize: 10, fill: "#142a52" };

function SensorPlot({ label, dataKey, color, data }) {
  return (
    <div className="sensor-plot">
      <span className="sensor-plot-label">{label}</span>
      <div className="sensor-plot-chart">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data}>
            <XAxis
              dataKey="t"
              domain={["auto", "auto"]}
              tickFormatter={formatEstTime}
              tick={axisTick}
              stroke="#142a52"
              height={16}
            />
            <YAxis
              domain={["auto", "auto"]}
              width={32}
              tick={axisTick}
              stroke="#142a52"
            />
            <Line
              type="monotone"
              dataKey={dataKey}
              stroke={color}
              strokeWidth={2}
              dot={false}
              isAnimationActive={false}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

export default SensorPlot;
