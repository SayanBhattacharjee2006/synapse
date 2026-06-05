import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.jsx'
import { THEME_STORAGE_KEY } from "@/lib/constants/theme"


function applyInitialTheme() {
  const root = document.documentElement

  try {
    const savedTheme = localStorage.getItem(THEME_STORAGE_KEY)
    const prefersDark = window.matchMedia("(prefers-color-scheme: dark)").matches
    const theme =
      savedTheme === "light" || savedTheme === "dark"
        ? savedTheme
        : prefersDark
          ? "dark"
          : "light"

    root.classList.toggle("light", theme === "light")
    root.classList.toggle("dark", theme === "dark")
    localStorage.setItem(THEME_STORAGE_KEY, theme)
  } catch {
    root.classList.remove("dark")
    root.classList.add("light")
  }
}

applyInitialTheme()

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
