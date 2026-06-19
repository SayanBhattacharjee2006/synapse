import { Button } from "@/components/ui";
import { UploadButton } from "@/features/documents";

import {
  MoreHorizontal,
  Moon,
  PanelLeft,
  Sun,
} from "lucide-react";

import { useThemeStore } from "@/stores/themeStore";

export default function ChatHeader({
  title = "New Conversation",
  onOpenSidebar,
  hasActiveConversation = false,
  fileCount = 0,
  isUploadOpen = false,
  onOpenUploadPanel,
  onOpenFilesDrawer,
}) {
  const { theme, toggleTheme } = useThemeStore();
  const hasFiles = fileCount > 0;

  return (
    <header className="z-10 flex shrink-0 flex-wrap items-center justify-between gap-3 border-b-2 border-[var(--color-border)] bg-[var(--color-background)] py-4 pl-[calc(1.25rem_+_var(--safe-area-left))] pr-[calc(1.5rem_+_var(--safe-area-right))]">
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
          <div className="flex min-w-0 flex-wrap items-center gap-3">
            <h1 className="truncate font-[var(--font-display)] text-2xl font-black uppercase tracking-[-0.06em] sm:text-3xl">
              {title}
            </h1>

            {hasFiles && (
              <span className="border-2 border-black bg-[var(--color-primary)] px-2 py-1 text-[10px] font-black uppercase text-black">
                {fileCount} {fileCount === 1 ? "file" : "files"}
              </span>
            )}
          </div>

          <p className="font-[var(--font-body)] text-xs uppercase tracking-widest text-[var(--color-muted)]">
            {hasFiles
              ? "Synapse AI Assistant - File Context Active"
              : "Synapse AI Assistant"}
          </p>
        </div>
      </div>

      <div className="flex items-center gap-2">
        {hasActiveConversation && (
          <>
            {hasFiles ? (
              <UploadButton
                mode="view"
                fileCount={fileCount}
                onClick={onOpenFilesDrawer}
              />
            ) : (
              <UploadButton
                active={isUploadOpen}
                label={
                  isUploadOpen ? "Close Upload" : "Upload Files"
                }
                onClick={onOpenUploadPanel}
              />
            )}

            {hasFiles && (
              <Button
                type="button"
                variant="secondary"
                size="icon"
                className="h-10 w-10 shrink-0"
                onClick={onOpenUploadPanel}
                aria-label={
                  isUploadOpen
                    ? "Close upload panel"
                    : "Open upload panel"
                }
                title={
                  isUploadOpen
                    ? "Close upload panel"
                    : "Add more files"
                }
              >
                <MoreHorizontal size={18} strokeWidth={3} />
              </Button>
            )}
          </>
        )}

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
