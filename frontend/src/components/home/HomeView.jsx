export default function HomeView() {
    return (
        <div className="flex flex-col items-center justify-center min-h-full px-4 pb-20">
            {/* Greeting */}
            <div className="text-center mb-12 max-w-2xl">
                <h1 className="text-5xl font-bold mb-4 text-[var(--color-text-primary)]">
                    Good morning, <span className="bg-gradient-to-r from-purple-500 to-blue-500 bg-clip-text text-transparent">Alex</span>
                </h1>
                <p className="text-lg text-[var(--color-text-secondary)]">
                    Where shall we start today?
                </p>
            </div>

            {/* Quick Actions */}
            <div className="mb-12 max-w-3xl w-full">
                <div className="flex items-center justify-center gap-2 mb-4 px-2">
                    <button className="flex items-center gap-2 px-3 py-2 text-sm text-[var(--color-text-secondary)] hover:text-[var(--color-text-primary)] transition-colors">
                        <svg viewBox="0 0 24 24" className="h-4 w-4" fill="none" stroke="currentColor" strokeWidth="1.8">
                            <path d="M12 5v14M5 12h14"/>
                        </svg>
                        Create image
                    </button>
                    <button className="flex items-center gap-2 px-3 py-2 text-sm text-[var(--color-text-secondary)] hover:text-[var(--color-text-primary)] transition-colors">
                        <svg viewBox="0 0 24 24" className="h-4 w-4" fill="none" stroke="currentColor" strokeWidth="1.8">
                            <path d="M3 12a9 9 0 1 0 18 0A9 9 0 0 0 3 12z"/>
                            <path d="M9 9h6v6H9z"/>
                        </svg>
                        Analyze data
                    </button>
                    <button className="flex items-center gap-2 px-3 py-2 text-sm text-[var(--color-text-secondary)] hover:text-[var(--color-text-primary)] transition-colors">
                        <svg viewBox="0 0 24 24" className="h-4 w-4" fill="none" stroke="currentColor" strokeWidth="1.8">
                            <path d="M4 6h16M4 12h16M4 18h16"/>
                        </svg>
                        Summarize text
                    </button>
                    <button className="flex items-center gap-2 px-3 py-2 text-sm text-[var(--color-text-secondary)] hover:text-[var(--color-text-primary)] transition-colors">
                        <svg viewBox="0 0 24 24" className="h-4 w-4" fill="none" stroke="currentColor" strokeWidth="1.8">
                            <path d="M12 3v18M3 12h18"/>
                        </svg>
                        Brainstorm
                    </button>
                    <button className="flex items-center gap-2 px-3 py-2 text-sm text-[var(--color-text-secondary)] hover:text-[var(--color-text-primary)] transition-colors">
                        <svg viewBox="0 0 24 24" className="h-4 w-4" fill="currentColor">
                            <circle cx="12" cy="12" r="1"/>
                            <circle cx="19" cy="12" r="1"/>
                            <circle cx="5" cy="12" r="1"/>
                        </svg>
                    </button>
                </div>

                {/* Input Field */}
                <div className="relative rounded-2xl border border-[var(--color-border)] bg-[var(--color-bg-secondary)] p-4 shadow-sm hover:border-[var(--color-text-secondary)] transition-colors">
                    <input
                        type="text"
                        placeholder="Ask anything..."
                        className="w-full bg-transparent text-base text-[var(--color-text-primary)] placeholder-[var(--color-text-muted)] outline-none"
                    />
                    <button className="absolute right-4 top-1/2 transform -translate-y-1/2 flex h-10 w-10 items-center justify-center rounded-full bg-gradient-to-r from-purple-500 to-blue-500 text-white hover:from-purple-600 hover:to-blue-600 transition-all">
                        <svg viewBox="0 0 24 24" className="h-5 w-5" fill="currentColor">
                            <path d="M16.6915026,12.4744748 L3.50612381,13.2599618 C3.19218622,13.2599618 3.03521743,13.4170592 3.03521743,13.5741566 L1.15159189,20.0151496 C0.8376543,20.8006365 0.99,21.89 1.77946707,22.52 C2.41,22.99 3.50612381,23.1 4.13399899,22.8429026 L21.714504,14.0454487 C22.6563168,13.5741566 23.1272231,12.6315722 22.6563168,11.6889879 L4.13399899,1.16346272 C3.34915502,0.9 2.40734225,1.00636533 1.77946707,1.4776575 C0.994623095,2.10604706 0.837654326,3.0486314 1.15159189,3.99701575 L3.03521743,10.4380088 C3.03521743,10.5950805 3.34915502,10.7521779 3.50612381,10.7521779 L16.6915026,11.5376648 C16.6915026,11.5376648 17.1624089,11.5376648 17.1624089,12.0089569 C17.1624089,12.4744748 16.6915026,12.4744748 16.6915026,12.4744748 Z"/>
                        </svg>
                    </button>
                </div>
            </div>

            {/* Cards Grid */}
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 w-full max-w-3xl">
                <ActionCard
                    icon="🎨"
                    title="Write a marketing campaign"
                    subtitle="Tailored for my audience"
                    bgClass="bg-purple-50 dark:bg-purple-900/20"
                />
                <ActionCard
                    icon="📊"
                    title="Analyze this data"
                    subtitle="Upload a file and get insights"
                    bgClass="bg-green-50 dark:bg-green-900/20"
                />
                <ActionCard
                    icon="💡"
                    title="Brainstorm ideas"
                    subtitle="For a product or project"
                    bgClass="bg-orange-50 dark:bg-orange-900/20"
                />
                <ActionCard
                    icon="✍️"
                    title="Help me write"
                    subtitle="Anything from emails to docs"
                    bgClass="bg-blue-50 dark:bg-blue-900/20"
                />
            </div>
        </div>
    );
}

function ActionCard({ icon, title, subtitle, bgClass }) {
    return (
        <button className={`group flex flex-col items-start gap-3 rounded-2xl ${bgClass} border border-[var(--color-border)] p-4 hover:border-[var(--color-text-secondary)] transition-all cursor-pointer h-full text-left`}>
            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-white dark:bg-[var(--color-bg-secondary)] text-xl">
                {icon}
            </div>
            <div className="flex-1">
                <p className="font-semibold text-sm text-[var(--color-text-primary)] mb-1">
                    {title}
                </p>
                <p className="text-xs text-[var(--color-text-muted)]">
                    {subtitle}
                </p>
            </div>
            <svg viewBox="0 0 24 24" className="h-4 w-4 text-[var(--color-text-muted)] opacity-0 group-hover:opacity-100 transition-opacity self-end mt-auto">
                <path d="M5 12h14M12 5l7 7-7 7" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
            </svg>
        </button>
    );
}
