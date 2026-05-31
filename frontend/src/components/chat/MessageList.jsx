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
    <div className="flex flex-1 flex-col items-center overflow-y-auto bg-[var(--color-bg-primary)] py-6 px-4">
      <div className="w-full max-w-[780px]">
        {messages.length === 0 && !isStreaming ? (
          <div className="flex min-h-[60vh] w-full items-center justify-center">
            <p className="text-center text-lg text-[var(--color-text-muted)]">Send a message to start the conversation</p>
          </div>
        ) : (
          <div className="flex w-full flex-col gap-5 pb-4">
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
    </div>
  )
}
