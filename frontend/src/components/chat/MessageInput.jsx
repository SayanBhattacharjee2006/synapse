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
    <div className="border-t border-[var(--color-border)] px-6 py-5 lg:px-10">
      <div className="mx-auto w-full max-w-4xl">
        {!activeConversationId && (
          <p className="mb-3 text-center text-sm text-[var(--color-text-muted)]">Select or create a conversation to start chatting</p>
        )}
        <div className="flex items-center gap-3">
          <Input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={isStreaming ? "AI is responding..." : "Type a message..."}
            aria-label="Message"
            disabled={isStreaming || !activeConversationId}
          />
          <Button onClick={handleSend} disabled={isStreaming || !input.trim() || !activeConversationId}>
            {isStreaming ? <Spinner size="sm" /> : "Send"}
          </Button>
        </div>
      </div>
    </div>
  )
}
