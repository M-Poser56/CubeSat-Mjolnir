const estTimeFormatter = new Intl.DateTimeFormat("en-US", {
  timeZone: "America/New_York",
  hourCycle: "h23",
  hour: "2-digit",
  minute: "2-digit",
  second: "2-digit",
});

export function formatEstTime(timestampMs) {
  return estTimeFormatter.format(new Date(timestampMs));
}
