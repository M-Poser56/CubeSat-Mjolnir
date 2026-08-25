import { useState } from "react";

// Expected packet shape once wired to the backend: { t, pitch, roll, yaw }
// where `t` is an epoch-ms timestamp and pitch/roll/yaw are degrees.
function useOrientationStream() {
  const [data] = useState([]);

  return data;
}

export default useOrientationStream;
