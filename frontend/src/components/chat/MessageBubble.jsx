export default function MessageBubble({ message }) {
  const isUser = message.sender === "user"

  return (
    <div className={`flex w-full ${isUser ? "justify-end" : "justify-start"}`}>
      <div className={`max-w-[70%] whitespace-pre-wrap break-words rounded-2xl py-3 px-4 text-[15px] leading-7 shadow-sm ${
        isUser
          ? "rounded-br-md bg-[var(--color-accent)] text-white"
          : "rounded-bl-md border border-[var(--color-border)] bg-[var(--color-bg-elevated)] text-[var(--color-text-primary)]"
      }`}>
        {message.content}
      </div>
    </div>
  )
}
