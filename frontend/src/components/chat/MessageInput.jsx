import { useState } from "react"
import { useChatStore } from "../../stores/chatStore"
import Input from "../ui/Input"
import Button from "../ui/Button"
import Spinner from "../ui/Spinner"

export default function MessageInput() {
  const [input, setInput] = useState("")
  const { activeConversationId, isStreaming, sendMessage } = useChatStore()

  const handleSend = async () => {
    if (!input.trim() || isStreaming || !activeConversationId) return
    const content = input.trim()
    setInput("")
    await sendMessage(activeConversationId, { content, sender: "user" })
  }

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  return (
    <div className="shrink-0 border-t border-[var(--color-border)] bg-[var(--color-bg-secondary)] p-4">
      <div className="w-full">
        {!activeConversationId && (
          <p className="mb-3 text-center text-sm text-[var(--color-text-muted)]">Select or create a conversation to start chatting</p>
        )}
        <div className="flex min-h-12 w-full items-center gap-3">
          <Input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={isStreaming ? "AI is responding..." : "Type a message..."}
            aria-label="Message"
            disabled={isStreaming || !activeConversationId}
            className="min-w-0 flex-1"
          />
          <Button
            onClick={handleSend}
            disabled={isStreaming || !input.trim() || !activeConversationId}
            className="h-12 min-w-[88px] shrink-0 px-5"
          >
            {isStreaming ? <Spinner size="sm" /> : "Send"}
          </Button>
        </div>
      </div>
    </div>
  )
}
