import "./ReactionWheelPanel.css";

const AXES = [
  { key: "pitch", label: "Pitch" },
  { key: "roll", label: "Roll" },
  { key: "yaw", label: "Yaw" },
];

function ReactionWheelPanel({ speeds, onChange, direction, onDirectionChange }) {
  function handleChange(axis, value) {
    onChange((prev) => ({ ...prev, [axis]: Number(value) }));
  }

  const isRev = direction === "REV";

  return (
    <div className="reaction-wheel-panel">
      <div className="rw-direction-row">
        <span className={`rw-dir-label${isRev ? "" : " rw-dir-active"}`}>FWD</span>
        <label className="rw-switch">
          <input
            type="checkbox"
            checked={isRev}
            onChange={(e) => onDirectionChange(e.target.checked ? "REV" : "FWD")}
            aria-label="Reaction wheel direction"
          />
          <span className="rw-switch-track">
            <span className="rw-switch-thumb" />
          </span>
        </label>
        <span className={`rw-dir-label${isRev ? " rw-dir-active" : ""}`}>REV</span>
      </div>
      <div className="rw-sliders">
        {AXES.map(({ key, label }) => (
          <div className="rw-slider-group" key={key}>
            <span className="rw-value">{speeds[key]}%</span>
            <div className="rw-slider-track">
              <input
                className="rw-slider"
                type="range"
                orient="vertical"
                min={0}
                max={100}
                step={1}
                value={speeds[key]}
                onChange={(e) => handleChange(key, e.target.value)}
              />
            </div>
            <span className="rw-label">{label}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

export default ReactionWheelPanel;
