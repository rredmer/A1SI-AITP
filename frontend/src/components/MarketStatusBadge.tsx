import type { AssetClass } from "../types";

interface MarketStatusBadgeProps {
  assetClass: AssetClass;
}

function isNYSEOpen(): boolean {
  const now = new Date();
  const et = new Date(now.toLocaleString("en-US", { timeZone: "America/New_York" }));
  const day = et.getDay();
  if (day === 0 || day === 6) return false;
  const minutes = et.getHours() * 60 + et.getMinutes();
  return minutes >= 570 && minutes < 960; // 9:30 AM - 4:00 PM ET
}

function isForexOpen(): boolean {
  const now = new Date();
  const day = now.getUTCDay();
  // Forex is closed from Friday 22:00 UTC to Sunday 22:00 UTC
  if (day === 6) return false;
  if (day === 0) {
    return now.getUTCHours() >= 22;
  }
  if (day === 5) {
    return now.getUTCHours() < 22;
  }
  return true;
}

export function MarketStatusBadge({ assetClass }: MarketStatusBadgeProps) {
  if (assetClass === "crypto") return null;

  if (assetClass === "equity") {
    const open = isNYSEOpen();
    return (
      <span
        className={`inline-block rounded-full px-2 py-0.5 text-xs font-medium ${
          open ? "bg-green-500/15 text-green-400" : "bg-red-500/15 text-red-400"
        }`}
      >
        {open ? "Market Open" : "Market Closed"}
      </span>
    );
  }

  // forex
  const active = isForexOpen();
  return (
    <span
      className={`inline-block rounded-full px-2 py-0.5 text-xs font-medium ${
        active ? "bg-green-500/15 text-green-400" : "bg-red-500/15 text-red-400"
      }`}
    >
      {active ? "Session Active" : "Weekend"}
    </span>
  );
}
