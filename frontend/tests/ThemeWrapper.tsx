import { useState } from "react";
import { ThemeContext } from "../src/contexts/theme";
import type { Theme } from "../src/contexts/theme";

export function ThemeWrapper({ children }: { children: React.ReactNode }) {
  const [theme, setTheme] = useState<Theme>("dark");
  return (
    <ThemeContext.Provider value={{ theme, setTheme }}>
      {children}
    </ThemeContext.Provider>
  );
}
