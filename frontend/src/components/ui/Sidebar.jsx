import { useEffect, useState } from "react";
import { useChatStore } from "../../stores/chatStore";
import ConversationItem from "../conversation/ConversationItem";
import Button from "../ui/Button";
import Spinner from "../ui/Spinner";

const THEME_STORAGE_KEY = "synapse-theme";

export default function Sidebar({ isOpen, onClose }) {
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

    const handleSelect = (id) => {
        loadMessages(id);
        onClose?.();
    };

    return (
        <aside
            className={`flex h-screen w-[300px] min-w-[300px] shrink-0 flex-col border-r border-[var(--color-border)] bg-[var(--color-bg-secondary)] max-md:fixed max-md:inset-y-0 max-md:left-0 max-md:z-50 max-md:shadow-2xl max-md:transition-transform max-md:duration-300 max-md:ease-in-out ${
                isOpen ? "max-md:translate-x-0" : "max-md:-translate-x-full"
            }`}
        >
            <div className="flex flex-col gap-5 border-b border-[var(--color-border)] p-5">
                <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2.5 text-2xl font-bold text-[var(--color-text-primary)]">
                        <span aria-hidden="true" className="text-[var(--color-accent)]">⚡</span>
                        <span>Synapse</span>
                    </div>
                    <button
                        type="button"
                        onClick={onClose}
                        className="flex h-9 w-9 items-center justify-center rounded-xl text-[var(--color-text-secondary)] transition-colors hover:bg-[var(--color-bg-elevated)] hover:text-[var(--color-text-primary)] md:hidden"
                        aria-label="Close sidebar"
                    >
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
                            <path d="M18 6L6 18M6 6l12 12" />
                        </svg>
                    </button>
                </div>
                <Button
                    onClick={createConversation}
                    className="w-full rounded-xl"
                    disabled={isLoading}
                >
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round">
                        <path d="M12 5v14M5 12h14" />
                    </svg>
                    <span>New Chat</span>
                </Button>
            </div>

            <div className="flex-1 overflow-y-auto p-4">
                <p className="mb-3 px-4 text-[13px] font-semibold uppercase tracking-wider text-[var(--color-text-muted)]">
                    Recent
                </p>
                <div className="space-y-1">
                    {isLoading && conversations.length === 0 ? (
                        <div className="mt-8 flex justify-center">
                            <Spinner size="md" />
                        </div>
                    ) : conversations.length === 0 ? (
                        <p className="mt-8 text-center text-base text-[var(--color-text-muted)]">
                            No conversations yet
                        </p>
                    ) : (
                        conversations.map((convo) => (
                            <ConversationItem
                                key={convo.id}
                                conversation={convo}
                                isActive={activeConversationId === convo.id}
                                onSelect={handleSelect}
                                onDelete={deleteConversation}
                                onRename={() => {}}
                            />
                        ))
                    )}
                </div>
            </div>

            <div className="border-t border-[var(--color-border)] p-5">
                <button
                    type="button"
                    onClick={toggleDarkMode}
                    className="flex h-11 w-11 items-center justify-center rounded-xl border border-[var(--color-border)] bg-[var(--color-bg-elevated)] text-[var(--color-text-secondary)] transition-colors duration-200 hover:border-[var(--color-accent)] hover:text-[var(--color-accent)] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-accent)] focus-visible:ring-offset-2 focus-visible:ring-offset-[var(--color-bg-secondary)]"
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
                    {isDarkMode ? (
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                            <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z" />
                        </svg>
                    ) : (
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                            <circle cx="12" cy="12" r="5" />
                            <path d="M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42" />
                        </svg>
                    )}
                </button>
            </div>
        </aside>
    );
}
