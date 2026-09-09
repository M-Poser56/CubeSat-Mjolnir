import useOrientationStream from "../hooks/useOrientationStream";
import "./TemperaturePanel.css";

const HEAT_MIN_C = -600;
const HEAT_MAX_C = 600;

// Sensor packet's 4th field arrives as a raw string like "25C" —
// pull the numeric part out as a real number so it can drive both
// the Fahrenheit conversion and the heatmap slider.
function parseTempC(temp) {
  if (!temp) return null;
  const match = /-?\d+(\.\d+)?/.exec(temp);
  return match ? Number(match[0]) : null;
}

function TemperaturePanel() {
  const { data } = useOrientationStream();
  const latest = data[data.length - 1];
  const celsius = latest ? parseTempC(latest.temp) : null;
  const fahrenheit = celsius !== null ? celsius * 1.8 + 32 : null;
  const sliderValue = celsius !== null
    ? Math.min(HEAT_MAX_C, Math.max(HEAT_MIN_C, celsius))
    : 0;

  return (
    <div className="temperature-panel">
      <span className="temp-title">Mjolnir Onboard Temp</span>
      <div className="temp-body">
        <div className="temp-readouts">
          <div className="temp-readout">
            <span className="temp-value">
              {celsius !== null ? celsius.toFixed(1) : "--"}
            </span>
            <span className="temp-unit">&deg;C</span>
          </div>
          <div className="temp-fahrenheit">
            {fahrenheit !== null ? fahrenheit.toFixed(1) : "--"}&deg;F
          </div>
        </div>
        <div className="temp-gauge">
          <span className="temp-scale-label temp-scale-hot">{HEAT_MAX_C}&deg;C</span>
          <div className="temp-gauge-track">
            <input
              className="temp-heat-slider"
              type="range"
              min={HEAT_MIN_C}
              max={HEAT_MAX_C}
              value={sliderValue}
              disabled
              readOnly
              aria-label="Temperature heatmap"
            />
          </div>
          <span className="temp-scale-label temp-scale-cold">{HEAT_MIN_C}&deg;C</span>
        </div>
      </div>
    </div>
  );
}

export default TemperaturePanel;
