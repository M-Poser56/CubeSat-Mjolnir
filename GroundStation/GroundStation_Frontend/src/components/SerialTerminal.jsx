import { useEffect, useRef } from "react";
import useSerialStream from "../hooks/useSerialStream";
import "./SerialTerminal.css";

const PROMPT = "[Mjolnir]>>";

function SerialTerminal() {
  const { lines } = useSerialStream();
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ block: "end" });
  }, [lines]);

  return (
    <div className="serial-terminal">
      {lines.map((line, i) => (
        <div className="serial-line" key={i}>
          {PROMPT} {line}
        </div>
      ))}
      <div className="serial-line">
        {PROMPT}
        <span className="serial-cursor" />
      </div>
      <div ref={bottomRef} />
    </div>
  );
}

export default SerialTerminal;
