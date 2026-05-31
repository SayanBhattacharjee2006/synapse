import Button from "../ui/Button";

export default function ConversationItem({
    conversation,
    isActive,
    onSelect,
    onDelete,
    onRename,
}) {
    return (
        <div
            onClick={() => onSelect(conversation.id)}
            className={`group flex min-h-12 cursor-pointer items-center justify-between gap-3 rounded-xl px-4 py-3 transition-colors duration-200 ${
                isActive
                    ? "bg-[var(--color-bg-elevated)]"
                    : "hover:bg-[var(--color-bg-elevated)]"
            }`}
        >
            <span className="min-w-0 flex-1 truncate text-base text-[var(--color-text-primary)]">
                {conversation.title || "New Chat"}
            </span>
            <div className="hidden shrink-0 items-center gap-1 group-hover:flex group-focus-within:flex">
                <Button
                    variant="ghost"
                    size="icon"
                    onClick={(e) => {
                        e.stopPropagation();
                        onRename(conversation);
                    }}
                    className="text-[var(--color-text-secondary)]"
                    aria-label="Rename conversation"
                >
                    <svg aria-hidden="true" viewBox="0 0 20 20" className="h-4 w-4" fill="none">
                        <path d="M4 13.5V16h2.5L14 8.5 11.5 6 4 13.5Z" stroke="currentColor" strokeWidth="1.7" strokeLinejoin="round" />
                        <path d="m10.5 7 2.5 2.5" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" />
                    </svg>
                </Button>
                <Button
                    variant="danger"
                    size="icon"
                    onClick={(e) => {
                        e.stopPropagation();
                        onDelete(conversation.id);
                    }}
                    aria-label="Delete conversation"
                >
                    <svg aria-hidden="true" viewBox="0 0 20 20" className="h-4 w-4" fill="none">
                        <path d="M5 6h10" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" />
                        <path d="M8 6V4.5h4V6" stroke="currentColor" strokeWidth="1.7" strokeLinejoin="round" />
                        <path d="m7 8 .5 7.5h5L13 8" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round" />
                    </svg>
                </Button>
            </div>
        </div>
    );
}
