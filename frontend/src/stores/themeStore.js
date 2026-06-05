import { create } from "zustand";
import { THEME_STORAGE_KEY } from "@/lib/constants/theme";

const getInitialTheme = () => {
  const storedTheme = localStorage.getItem(THEME_STORAGE_KEY);

  if (storedTheme) {
    return storedTheme;
  }

  return window.matchMedia("(prefers-color-scheme: dark)").matches
    ? "dark"
    : "light";
};

export const useThemeStore = create((set, get) => ({
  theme: getInitialTheme(),

  setTheme: (theme) => {
    localStorage.setItem(THEME_STORAGE_KEY, theme);

    document.documentElement.classList.toggle(
      "dark",
      theme === "dark"
    );
    document.documentElement.classList.toggle(
      "light",
      theme === "light"
    );

    set({ theme });
  },

  toggleTheme: () => {
    const currentTheme = get().theme;

    const nextTheme =
      currentTheme === "dark" ? "light" : "dark";

    get().setTheme(nextTheme);
  },
}));
