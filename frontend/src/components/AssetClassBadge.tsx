import { ASSET_CLASS_LABELS } from "../constants/assetDefaults";
import type { AssetClass } from "../types";

const BADGE_STYLES: Record<AssetClass, string> = {
  crypto: "bg-orange-500/15 text-orange-400",
  equity: "bg-blue-500/15 text-blue-400",
  forex: "bg-green-500/15 text-green-400",
};

interface AssetClassBadgeProps {
  assetClass: AssetClass;
}

export function AssetClassBadge({ assetClass }: AssetClassBadgeProps) {
  return (
    <span
      className={`inline-block rounded-full px-2 py-0.5 text-xs font-medium ${BADGE_STYLES[assetClass]}`}
    >
      {ASSET_CLASS_LABELS[assetClass]}
    </span>
  );
}
