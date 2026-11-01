import { useCallback, useEffect, useState } from "react";

/** Two per-viewer conveniences, remembered in this browser only. Storage can be blocked, so every access is guarded. */
const read = (key) => { try { return localStorage.getItem(key); } catch { return null; } };
const write = (key, value) => { try { localStorage.setItem(key, value); } catch { /* storage unavailable: the choice just lasts for this visit */ } };

export function useTheme() {
  const [theme, setTheme] = useState(() => document.documentElement.dataset.theme || "dark");
  useEffect(() => {
    document.documentElement.dataset.theme = theme;
    document.querySelector('meta[name="theme-color"]')?.setAttribute("content", theme === "light" ? "#F5F4EF" : "#090B0F");
  }, [theme]);
  const toggle = useCallback(() => setTheme((t) => { const next = t === "light" ? "dark" : "light"; write("ss-theme", next); return next; }), []);
  return [theme, toggle];
}

export function useLargeText() {
  const [large, setLarge] = useState(() => document.documentElement.dataset.text === "large");
  useEffect(() => {
    if (large) document.documentElement.dataset.text = "large";
    else delete document.documentElement.dataset.text;
  }, [large]);
  const toggle = useCallback(() => setLarge((v) => { write("ss-large", v ? "0" : "1"); return !v; }), []);
  return [large, toggle];
}

/** Used by index.html before React starts, to avoid a flash of the wrong theme. */
export const initialPrefs = () => ({ theme: read("ss-theme") === "light" ? "light" : "dark", large: read("ss-large") === "1" });
