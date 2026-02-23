import { useContext } from "react";
import { AssetClassContext } from "../contexts/assetClass";

export function useAssetClass() {
  return useContext(AssetClassContext);
}
