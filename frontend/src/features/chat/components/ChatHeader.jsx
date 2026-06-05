import { Card, Button } from "@/components/ui";

import { Moon, PanelLeft, Sun } from "lucide-react";

import { useThemeStore } from "@/stores/themeStore";

export default function ChatHeader({
  title = "New Conversation",
  onOpenSidebar,
}) {
  const { theme, toggleTheme } = useThemeStore();

  return (
    <Card className="flex items-center justify-between border-0 p-4 z-10">
      
      <div className="flex items-center gap-3">
        
        {/* Mobile Sidebar Toggle */}
        <Button
          variant="secondary"
          size="icon"
          className="md:hidden"
          onClick={onOpenSidebar}
          aria-label="Open sidebar"
        >
          <PanelLeft size={18} />
        </Button>

        <div className="pl-6">
          <h1 className="text-3xl font-black uppercase ">
            {title}
          </h1>

          <p className="text-sm uppercase text-[var(--color-muted)]">
            Synapse AI Assistant
          </p>
        </div>
      </div>

      {/* Actions */}
      <div className="flex items-center gap-2">
        <Button
          variant="secondary"
          size="icon"
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
    </Card>
  );
}
