export default function MessageBubble({ message }) {
  const isUser = message.sender === "user"

  return (
    <div className={`mb-5 flex ${isUser ? "justify-end" : "justify-start"}`}>
      <div className={`max-w-[82%] rounded-2xl px-5 py-4 text-base leading-7 shadow-sm sm:max-w-[78%] lg:max-w-[720px] ${
        isUser
          ? "bg-[var(--color-accent)] text-white rounded-br-sm"
          : "bg-[var(--color-bg-elevated)] text-[var(--color-text-primary)] rounded-bl-sm"
      }`}>
        {message.content}
      </div>
    </div>
  )
}
