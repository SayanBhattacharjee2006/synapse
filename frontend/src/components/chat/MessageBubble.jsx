export default function MessageBubble({ message }) {
  const isUser = message.sender === "user"

  return (
    <div className={`flex w-full px-4 ${isUser ? "justify-end" : "justify-start"}`}>
      <div className={`flex items-start gap-3 ${isUser ? "max-w-[70%]" : "max-w-[75%]"}`}>
        {!isUser && (
          <div className="mt-0.5 flex h-9 w-9 shrink-0 items-center justify-center rounded-full border border-[var(--color-border)] bg-[var(--color-bg-elevated)] text-[var(--color-accent)]">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor">
              <path d="M13 3L4 14h7l-2 7 9-11h-7l2-7z" />
            </svg>
          </div>
        )}
        <div className={`overflow-hidden whitespace-pre-wrap break-words rounded-2xl px-5 py-3.5 text-base leading-7 shadow-sm ${
          isUser
            ? "rounded-br-md bg-[var(--color-accent)] text-white"
            : "rounded-bl-md border border-[var(--color-border)] bg-[var(--color-bg-elevated)] text-[var(--color-text-primary)]"
        }`}>
          {message.content}
        </div>
      </div>
    </div>
  )
}
