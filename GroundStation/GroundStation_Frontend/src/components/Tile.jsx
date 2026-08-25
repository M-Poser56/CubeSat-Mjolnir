import "./Tile.css";

function Tile({ title, className = "", children }) {
  return (
    <div className={`tile ${className}`.trim()}>
      {title && <h2 className="tile-title">{title}</h2>}
      <div className="tile-content">{children}</div>
    </div>
  );
}

export default Tile;
