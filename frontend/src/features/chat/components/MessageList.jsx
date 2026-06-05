import { MessageBubble } from "@/features/chat";

export default function MessageList({
  messages = [],
}) {
  if (messages.length === 0) {
    return (
      <div className="flex h-full items-center justify-center">
        <p className="text-base font-bold uppercase text-[var(--color-muted)]">
          Start a conversation
        </p>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-6 p-8">
      {messages.map((message) => (
        <MessageBubble
          key={message.id}
          sender={message.sender}
          content={message.content}
        />
      ))}
    </div>
  );
}
