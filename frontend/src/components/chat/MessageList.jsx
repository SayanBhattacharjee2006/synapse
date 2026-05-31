import { useEffect, useRef } from "react"
import { useChatStore } from "../../stores/chatStore"
import MessageBubble from "./MessageBubble"

export default function MessageList() {
  const { messages, isStreaming, streamingMessage } = useChatStore()
  const bottomRef = useRef(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [messages, streamingMessage])

  return (
    <div className="flex-1 overflow-y-auto bg-[var(--color-bg-primary)] px-6 py-4">
      {messages.length === 0 && !isStreaming ? (
        <div className="flex min-h-full w-full items-center justify-center">
          <p className="text-center text-base text-[var(--color-text-muted)]">Send a message to start the conversation</p>
        </div>
      ) : (
        <div className="flex w-full flex-col gap-4 pb-4">
          {messages.map((msg) => (
            <MessageBubble key={msg.id} message={msg} />
          ))}
          {isStreaming && streamingMessage && (
            <MessageBubble message={{ sender: "assistant", content: streamingMessage }} />
          )}
        </div>
      )}
      <div ref={bottomRef} />
    </div>
  )
}
