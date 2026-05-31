import { useChatStore } from "../../stores/ChatStore";

export default function RightSidebar() {
    const { conversations } = useChatStore();
    const recentChats = conversations.slice(0, 5);

    return (
        <aside className="flex h-screen w-[280px] min-w-[280px] shrink-0 flex-col border-l border-[var(--color-border)] bg-[var(--color-bg-primary)]">
            {/* Top Actions */}
            <div className="border-b border-[var(--color-border)] p-4">
                <div className="flex items-center justify-between gap-2">
                    <button className="flex-1 flex items-center justify-center gap-2 rounded-lg px-3 py-2 text-sm font-medium text-[var(--color-text-secondary)] hover:bg-[var(--color-bg-elevated)] transition-colors">
                        <svg viewBox="0 0 24 24" className="h-4 w-4" fill="none" stroke="currentColor" strokeWidth="1.8">
                            <circle cx="11" cy="11" r="8"/>
                            <path d="m21 21-4.35-4.35"/>
                        </svg>
                    </button>
                    <button className="flex-1 flex items-center justify-center gap-2 rounded-lg px-3 py-2 text-sm font-medium text-[var(--color-text-secondary)] hover:bg-[var(--color-bg-elevated)] transition-colors">
                        <svg viewBox="0 0 24 24" className="h-4 w-4" fill="none" stroke="currentColor" strokeWidth="1.8">
                            <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/>
                            <path d="M13.73 21a2 2 0 0 1-3.46 0"/>
                        </svg>
                    </button>
                    <button className="flex-1 flex items-center justify-center gap-2 rounded-lg px-3 py-2 text-sm font-medium text-[var(--color-text-secondary)] hover:bg-[var(--color-bg-elevated)] transition-colors">
                        <svg viewBox="0 0 24 24" className="h-4 w-4" fill="none" stroke="currentColor" strokeWidth="1.8">
                            <circle cx="12" cy="12" r="1"/>
                            <circle cx="19" cy="12" r="1"/>
                            <circle cx="5" cy="12" r="1"/>
                        </svg>
                    </button>
                </div>
            </div>

            {/* Recent Chats */}
            <div className="flex-1 overflow-y-auto px-3 py-4 border-b border-[var(--color-border)]">
                <div className="flex items-center justify-between mb-3">
                    <h3 className="text-sm font-semibold text-[var(--color-text-primary)]">Recent chats</h3>
                    <a href="#" className="text-xs text-[var(--color-accent)] hover:underline">View all</a>
                </div>
                <div className="space-y-2">
                    {recentChats.length === 0 ? (
                        <p className="text-xs text-[var(--color-text-muted)]">No recent chats</p>
                    ) : (
                        recentChats.map((chat, idx) => (
                            <div
                                key={chat.id}
                                className="flex items-start gap-2 rounded-lg p-2 hover:bg-[var(--color-bg-elevated)] cursor-pointer transition-colors group"
                            >
                                <div className="flex h-8 w-8 items-center justify-center rounded-full bg-[var(--color-bg-secondary)] text-sm flex-shrink-0">
                                    {idx === 0 ? "🎯" : idx === 1 ? "🌐" : idx === 2 ? "👥" : idx === 3 ? "📊" : "📄"}
                                </div>
                                <div className="min-w-0 flex-1">
                                    <p className="text-xs font-medium text-[var(--color-text-primary)] truncate">
                                        {chat.title || `Chat ${chat.id.slice(0, 8)}`}
                                    </p>
                                    <p className="text-xs text-[var(--color-text-muted)]">Today</p>
                                </div>
                                <svg viewBox="0 0 24 24" className="h-4 w-4 text-[var(--color-text-muted)] opacity-0 group-hover:opacity-100 transition-opacity flex-shrink-0">
                                    <path d="M8 12l4-4 4 4" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
                                </svg>
                            </div>
                        ))
                    )}
                </div>
            </div>

            {/* Upgrade Section */}
            <div className="shrink-0 p-3">
                <div className="rounded-2xl bg-gradient-to-br from-purple-100 to-blue-100 dark:from-purple-900/30 dark:to-blue-900/30 border border-purple-200 dark:border-purple-700/50 p-4">
                    <div className="flex items-start gap-2 mb-3">
                        <div className="flex h-6 w-6 items-center justify-center rounded bg-gradient-to-r from-purple-500 to-blue-500 text-white text-xs flex-shrink-0">
                            ✨
                        </div>
                        <h3 className="text-sm font-semibold text-[var(--color-text-primary)]">Upgrade your plan</h3>
                    </div>
                    <p className="text-xs text-[var(--color-text-secondary)] mb-3">
                        More GPTs, higher limits, and priority access.
                    </p>
                    <button className="w-full rounded-full bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700 px-4 py-2 text-sm font-medium text-white transition-all flex items-center justify-center gap-2">
                        Upgrade to Plus
                        <svg viewBox="0 0 24 24" className="h-3 w-3" fill="none" stroke="currentColor" strokeWidth="2">
                            <path d="M5 12h14M12 5l7 7-7 7"/>
                        </svg>
                    </button>
                </div>

                {/* Your GPTs */}
                <div className="mt-4">
                    <div className="flex items-center justify-between mb-3">
                        <h3 className="text-sm font-semibold text-[var(--color-text-primary)]">Your GPTs</h3>
                        <a href="#" className="text-xs text-[var(--color-accent)] hover:underline">View all</a>
                    </div>
                    <div className="space-y-2">
                        {[
                            { name: "DesignerGPT", desc: "Create and edit visuals", icon: "🎨" },
                            { name: "Data Analyst", desc: "Analyze data and charts", icon: "📊" },
                            { name: "WriteMate", desc: "Improve writing", icon: "✍️" },
                        ].map((gpt, idx) => (
                            <div
                                key={idx}
                                className="flex items-start gap-2 rounded-lg p-2 hover:bg-[var(--color-bg-elevated)] cursor-pointer transition-colors"
                            >
                                <div className="flex h-8 w-8 items-center justify-center rounded-full bg-[var(--color-bg-secondary)] text-lg flex-shrink-0">
                                    {gpt.icon}
                                </div>
                                <div className="min-w-0 flex-1">
                                    <p className="text-xs font-medium text-[var(--color-text-primary)]">
                                        {gpt.name}
                                    </p>
                                    <p className="text-xs text-[var(--color-text-muted)] truncate">
                                        {gpt.desc}
                                    </p>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            </div>
        </aside>
    );
}
