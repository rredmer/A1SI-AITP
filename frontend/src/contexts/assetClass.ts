import { createContext } from "react";
import type { AssetClass } from "../types";

export interface AssetClassContextType {
  assetClass: AssetClass;
  setAssetClass: (ac: AssetClass) => void;
}

export const AssetClassContext = createContext<AssetClassContextType>({
  assetClass: "crypto",
  setAssetClass: () => {},
});
