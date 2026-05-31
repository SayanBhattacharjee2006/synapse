import { useEffect, useState } from "react";
import { useChatStore } from "../../stores/chatStore";
import ConversationItem from "../conversation/ConversationItem";
import Button from "../ui/Button";
import Spinner from "../ui/Spinner";

const THEME_STORAGE_KEY = "synapse-theme";

function SunIcon() {
    return (
        <svg
            aria-hidden="true"
            viewBox="0 0 24 24"
            className="h-4 w-4"
            fill="none"
        >
            <circle
                cx="12"
                cy="12"
                r="4"
                stroke="currentColor"
                strokeWidth="1.8"
            />
            <path
                d="M12 2.75v2.5M12 18.75v2.5M21.25 12h-2.5M5.25 12h-2.5M18.54 5.46l-1.77 1.77M7.23 16.77l-1.77 1.77M18.54 18.54l-1.77-1.77M7.23 7.23 5.46 5.46"
                stroke="currentColor"
                strokeWidth="1.8"
                strokeLinecap="round"
            />
        </svg>
    );
}

function MoonIcon() {
    return (
        <svg
            aria-hidden="true"
            viewBox="0 0 24 24"
            className="h-4 w-4"
            fill="none"
        >
            <path
                d="M20.25 14.38A7.78 7.78 0 0 1 9.62 3.75 8.25 8.25 0 1 0 20.25 14.38Z"
                stroke="currentColor"
                strokeWidth="1.8"
                strokeLinecap="round"
                strokeLinejoin="round"
            />
        </svg>
    );
}

export default function Sidebar() {
    const {
        conversations,
        activeConversationId,
        isLoading,
        loadConversations,
        createConversation,
        deleteConversation,
        loadMessages,
    } = useChatStore();
    const [isDarkMode, setIsDarkMode] = useState(() => {
        return document.documentElement.classList.contains("dark");
    });

    useEffect(() => {
        loadConversations();
    }, [loadConversations]);

    const toggleDarkMode = () => {
        setIsDarkMode((currentMode) => {
            const nextMode = !currentMode;
            document.documentElement.classList.toggle("dark", nextMode);

            try {
                localStorage.setItem(
                    THEME_STORAGE_KEY,
                    nextMode ? "dark" : "light",
                );
            } catch {
                // Keep the visual toggle working even if storage is unavailable.
            }

            return nextMode;
        });
    };

    return (
        <aside className="flex h-screen w-[260px] min-w-[260px] shrink-0 flex-col border-r border-[var(--color-border)] bg-[var(--color-bg-secondary)]">
            <div className="flex flex-col gap-4 border-b border-[var(--color-border)] p-4 pt-7">
                <div className="flex items-center text-3xl font-semibold text-[var(--color-accent)]">
                    Synapse
                </div>
                <Button
                    onClick={createConversation}
                    className="w-full"
                    disabled={isLoading}
                >
                    + New Chat
                </Button>
            </div>

            <div className="flex-1 space-y-1 overflow-y-auto p-2 pt-4">
                {isLoading && conversations.length === 0 ? (
                    <div className="mt-6 flex justify-center">
                        <Spinner size="md" />
                    </div>
                ) : conversations.length === 0 ? (
                    <p className="mt-6 text-center text-base text-[var(--color-text-muted)]">
                        No conversations yet
                    </p>
                ) : (
                    conversations.map((convo) => (
                        <ConversationItem
                            key={convo.id}
                            conversation={convo}
                            isActive={activeConversationId === convo.id}
                            onSelect={(id) => loadMessages(id)}
                            onDelete={deleteConversation}
                            onRename={() => {}}
                        />
                    ))
                )}
            </div>

            <div className="border-t border-[var(--color-border)] p-4">
                <button
                    type="button"
                    onClick={toggleDarkMode}
                    className="flex w-full items-center justify-between gap-3 rounded-xl border border-[var(--color-border)] bg-[var(--color-bg-elevated)] px-3 py-2.5 text-left transition-colors duration-200 hover:border-[var(--color-accent)] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-accent)] focus-visible:ring-offset-2 focus-visible:ring-offset-[var(--color-bg-secondary)]"
                    aria-label={
                        isDarkMode
                            ? "Switch to light mode"
                            : "Switch to dark mode"
                    }
                    title={
                        isDarkMode
                            ? "Switch to light mode"
                            : "Switch to dark mode"
                    }
                >
                    <span className="text-sm font-medium text-[var(--color-text-secondary)]">
                        {isDarkMode ? "Dark mode" : "Light mode"}
                    </span>
                    <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-[var(--color-bg-secondary)] text-[var(--color-text-primary)]">
                        {isDarkMode ? <SunIcon /> : <MoonIcon />}
                    </span>
                </button>
            </div>
        </aside>
    );
}
