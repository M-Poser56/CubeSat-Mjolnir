import { useEffect, useState } from "react";
import { formatEstTime } from "../utils/time";
import "./Clock.css";

function Clock() {
  const [time, setTime] = useState(formatEstTime(Date.now()));

  useEffect(() => {
    const id = setInterval(() => {
      setTime(formatEstTime(Date.now()));
    }, 1000);
    return () => clearInterval(id);
  }, []);

  return <div className="clock">{time}</div>;
}

export default Clock;
