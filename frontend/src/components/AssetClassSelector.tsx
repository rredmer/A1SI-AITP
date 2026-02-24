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
    <div className="flex flex-col gap-0.5 rounded-lg border border-[var(--color-border)] bg-[var(--color-bg)] p-1">
      {SEGMENTS.map(({ value, label, Icon }) => (
        <button
          key={value}
          onClick={() => setAssetClass(value)}
          className={`flex items-center gap-2 rounded-md px-3 py-1.5 text-xs font-medium transition-colors ${
            assetClass === value
              ? "bg-[var(--color-primary)] text-white"
              : "text-[var(--color-text-muted)] hover:bg-[var(--color-surface)] hover:text-[var(--color-text)]"
          }`}
        >
          <Icon size={14} />
          {label}
        </button>
      ))}
    </div>
  );
}
