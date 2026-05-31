import { useEffect, useState } from "react";
import { useChatStore } from "../../stores/ChatStore";
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

function HomeIcon() {
    return (
        <svg viewBox="0 0 24 24" className="h-4 w-4" fill="none" stroke="currentColor" strokeWidth="1.8">
            <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/>
            <polyline points="9 22 9 12 15 12 15 22"/>
        </svg>
    );
}

function ExploreIcon() {
    return (
        <svg viewBox="0 0 24 24" className="h-4 w-4" fill="none" stroke="currentColor" strokeWidth="1.8">
            <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
        </svg>
    );
}

function LibraryIcon() {
    return (
        <svg viewBox="0 0 24 24" className="h-4 w-4" fill="none" stroke="currentColor" strokeWidth="1.8">
            <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20M4 4a2 2 0 0 1 2-2h12a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V4z"/>
            <path d="M8 8h8M8 12h8M8 16h4"/>
        </svg>
    );
}

function ProjectsIcon() {
    return (
        <svg viewBox="0 0 24 24" className="h-4 w-4" fill="none" stroke="currentColor" strokeWidth="1.8">
            <rect x="3" y="3" width="7" height="7"/>
            <rect x="14" y="3" width="7" height="7"/>
            <rect x="14" y="14" width="7" height="7"/>
            <rect x="3" y="14" width="7" height="7"/>
        </svg>
    );
}

function PlusIcon() {
    return (
        <svg viewBox="0 0 24 24" className="h-4 w-4" fill="none" stroke="currentColor" strokeWidth="2">
            <line x1="12" y1="5" x2="12" y2="19"/>
            <line x1="5" y1="12" x2="19" y2="12"/>
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
            {/* Header */}
            <div className="flex flex-col gap-4 border-b border-[var(--color-border)] p-4 pt-7">
                <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                        <div className="text-2xl font-bold text-[var(--color-accent)]">⚡</div>
                        <span className="text-xl font-semibold text-[var(--color-text-primary)]">Synapse</span>
                    </div>
                    <button className="rounded-lg p-1.5 hover:bg-[var(--color-bg-elevated)] transition-colors">
                        <svg viewBox="0 0 24 24" className="h-5 w-5 text-[var(--color-text-secondary)]" fill="none" stroke="currentColor" strokeWidth="1.8">
                            <line x1="12" y1="5" x2="12" y2="19"/>
                            <line x1="5" y1="12" x2="19" y2="12"/>
                        </svg>
                    </button>
                </div>
                <Button
                    onClick={createConversation}
                    className="w-full bg-gradient-to-r from-purple-500 to-cyan-500 hover:from-purple-600 hover:to-cyan-600"
                    disabled={isLoading}
                >
                    <svg viewBox="0 0 24 24" className="h-4 w-4" fill="none" stroke="currentColor" strokeWidth="2">
                        <line x1="12" y1="5" x2="12" y2="19"/>
                        <line x1="5" y1="12" x2="19" y2="12"/>
                    </svg>
                    New chat
                </Button>
            </div>

            {/* Navigation */}
            <nav className="space-y-1 border-b border-[var(--color-border)] px-2 py-4">
                <NavigationItem icon={<HomeIcon />} label="Home" />
                <NavigationItem icon={<ExploreIcon />} label="Explore GPTs" />
                <NavigationItem icon={<LibraryIcon />} label="Library" />
                <NavigationItem icon={<ProjectsIcon />} label="Projects" badge="Beta" />
            </nav>

            {/* Spaces Section */}
            <div className="flex-1 overflow-y-auto px-2 py-4">
                <div className="mb-4">
                    <div className="flex items-center justify-between px-2 py-2">
                        <span className="text-xs font-semibold text-[var(--color-text-muted)] uppercase tracking-wider">Spaces</span>
                        <button className="rounded-lg p-1 hover:bg-[var(--color-bg-elevated)] transition-colors">
                            <PlusIcon />
                        </button>
                    </div>
                    <div className="space-y-1 mt-2">
                        <SpaceItem icon="🎯" label="Marketing Team" />
                        <SpaceItem icon="🚀" label="Product Roadmap" />
                        <SpaceItem icon="🎨" label="Design System" />
                    </div>
                </div>

                {/* Chats Section */}
                <div>
                    <div className="px-2 py-2 mb-3">
                        <span className="text-xs font-semibold text-[var(--color-text-muted)] uppercase tracking-wider">Chats</span>
                    </div>
                    {isLoading && conversations.length === 0 ? (
                        <div className="mt-6 flex justify-center">
                            <Spinner size="md" />
                        </div>
                    ) : conversations.length === 0 ? (
                        <p className="mt-6 text-center text-xs text-[var(--color-text-muted)]">
                            No conversations yet
                        </p>
                    ) : (
                        <div className="space-y-1">
                            {conversations.map((convo) => (
                                <ConversationItem
                                    key={convo.id}
                                    conversation={convo}
                                    isActive={activeConversationId === convo.id}
                                    onSelect={(id) => loadMessages(id)}
                                    onDelete={deleteConversation}
                                    onRename={() => {}}
                                />
                            ))}
                        </div>
                    )}
                </div>
            </div>

            {/* Footer */}
            <div className="border-t border-[var(--color-border)] p-4 space-y-2">
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
                        {isDarkMode ? "Dark" : "Light"}
                    </span>
                    <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-[var(--color-bg-secondary)] text-[var(--color-text-primary)]">
                        {isDarkMode ? <SunIcon /> : <MoonIcon />}
                    </span>
                </button>
                <button className="flex w-full items-center justify-between gap-3 rounded-xl border border-[var(--color-border)] bg-[var(--color-bg-elevated)] px-3 py-2.5 text-left transition-colors duration-200 hover:border-[var(--color-accent)]">
                    <svg viewBox="0 0 24 24" className="h-4 w-4 text-[var(--color-text-secondary)]" fill="currentColor">
                        <circle cx="12" cy="12" r="1"/>
                        <circle cx="19" cy="12" r="1"/>
                        <circle cx="5" cy="12" r="1"/>
                    </svg>
                    <span className="text-sm font-medium text-[var(--color-text-secondary)] flex-1">More</span>
                </button>
            </div>
        </aside>
    );
}

function NavigationItem({ icon, label, badge }) {
    return (
        <button className="flex w-full items-center justify-between gap-3 rounded-lg px-3 py-2.5 text-sm font-medium text-[var(--color-text-secondary)] hover:bg-[var(--color-bg-elevated)] transition-colors">
            <div className="flex items-center gap-3">
                <span className="flex h-5 w-5 items-center justify-center">{icon}</span>
                <span>{label}</span>
            </div>
            {badge && (
                <span className="text-xs font-semibold text-blue-600 bg-blue-100 dark:bg-blue-900 dark:text-blue-300 px-2 py-0.5 rounded">
                    {badge}
                </span>
            )}
        </button>
    );
}

function SpaceItem({ icon, label }) {
    return (
        <button className="flex w-full items-center gap-3 rounded-lg px-3 py-2 text-sm text-[var(--color-text-secondary)] hover:bg-[var(--color-bg-elevated)] transition-colors">
            <span className="text-lg">{icon}</span>
            <span>{label}</span>
        </button>
    );
}
