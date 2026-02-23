import { Bitcoin, TrendingUp, Banknote } from "lucide-react";
import { useAssetClass } from "../hooks/useAssetClass";
import type { AssetClass } from "../types";

const SEGMENTS: { value: AssetClass; label: string; Icon: typeof Bitcoin }[] = [
  { value: "crypto", label: "Crypto", Icon: Bitcoin },
  { value: "equity", label: "Equities", Icon: TrendingUp },
  { value: "forex", label: "Forex", Icon: Banknote },
];

export function AssetClassSelector() {
  const { assetClass, setAssetClass } = useAssetClass();

  return (
    <div className="flex rounded-lg border border-[var(--color-border)] bg-[var(--color-bg)]">
      {SEGMENTS.map(({ value, label, Icon }) => (
        <button
          key={value}
          onClick={() => setAssetClass(value)}
          className={`flex flex-1 items-center justify-center gap-1.5 px-2 py-1.5 text-xs font-medium transition-colors ${
            assetClass === value
              ? "bg-[var(--color-primary)] text-white"
              : "text-[var(--color-text-muted)] hover:text-[var(--color-text)]"
          } ${value === "crypto" ? "rounded-l-lg" : ""} ${value === "forex" ? "rounded-r-lg" : ""}`}
        >
          <Icon size={14} />
          {label}
        </button>
      ))}
    </div>
  );
}
