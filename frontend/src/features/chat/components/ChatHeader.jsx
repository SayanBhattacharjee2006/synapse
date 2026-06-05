import { Button } from "@/components/ui";

import { Moon, PanelLeft, Sun } from "lucide-react";

import { useThemeStore } from "@/stores/themeStore";

export default function ChatHeader({
  title = "New Conversation",
  onOpenSidebar,
}) {
  const { theme, toggleTheme } = useThemeStore();

  return (
    <header className="z-10 flex shrink-0 items-center justify-between border-b-2 border-[var(--color-border)] bg-[var(--color-background)] py-4 pl-[calc(1.25rem_+_var(--safe-area-left))] pr-[calc(1.5rem_+_var(--safe-area-right))]">
      <div className="flex min-w-0 items-center gap-3">
        <Button
          variant="secondary"
          size="icon"
          className="shrink-0 md:hidden"
          onClick={onOpenSidebar}
          aria-label="Open sidebar"
        >
          <PanelLeft size={18} />
        </Button>

        <div className="min-w-0">
          <h1 className="truncate font-[var(--font-display)] text-3xl font-black uppercase tracking-[-0.08em]">
            {title}
          </h1>

          <p className="font-[var(--font-body)] text-xs uppercase tracking-widest text-[var(--color-muted)]">
            Synapse AI Assistant
          </p>
        </div>
      </div>

      <div className="flex items-center gap-2">
        <Button
          variant="secondary"
          size="icon"
          className="shrink-0"
          onClick={toggleTheme}
          aria-label={
            theme === "dark"
              ? "Switch to light mode"
              : "Switch to dark mode"
          }
          aria-pressed={theme === "dark"}
        >
          {theme === "dark" ? (
            <Sun size={18} />
          ) : (
            <Moon size={18} />
          )}
        </Button>
      </div>
    </header>
  );
}
