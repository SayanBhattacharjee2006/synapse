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
    <div className="flex-1 overflow-y-auto px-6 py-8 lg:px-10">
      {messages.length === 0 && !isStreaming ? (
        <div className="flex h-full items-center justify-center">
          <p className="text-lg text-[var(--color-text-muted)]">Send a message to start the conversation</p>
        </div>
      ) : (
        <div className="mx-auto w-full max-w-4xl">
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
