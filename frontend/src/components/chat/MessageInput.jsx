import { useEffect, useRef, useState } from "react"
import { useChatStore } from "../../stores/chatStore"
import Spinner from "../ui/Spinner"

export default function MessageInput() {
  const [input, setInput] = useState("")
  const textareaRef = useRef(null)
  const { activeConversationId, isStreaming, sendMessage } = useChatStore()
  const canSend = Boolean(input.trim() && !isStreaming && activeConversationId)

  useEffect(() => {
    const textarea = textareaRef.current
    if (!textarea) return

    textarea.style.height = "auto"
    textarea.style.height = `${Math.min(textarea.scrollHeight, 200)}px`
    textarea.style.overflowY = textarea.scrollHeight > 200 ? "auto" : "hidden"
  }, [input])

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
    <div className="w-full flex flex-col items-center px-4 pb-5 pt-2">
      <div className="w-full max-w-[780px]">
        {!activeConversationId && (
          <p className="mb-3 text-center text-base text-[var(--color-text-muted)]">Select or create a conversation to start chatting</p>
        )}
        <div className="rounded-2xl border border-[var(--color-border)] bg-[var(--color-bg-elevated)] px-4 py-3 shadow-lg">
          <div className="flex items-end gap-3">
            <button
              type="button"
              className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full text-[var(--color-text-secondary)] transition-colors duration-200 hover:bg-[var(--color-bg-secondary)] hover:text-[var(--color-text-primary)] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-accent)]"
              aria-label="Add attachment"
              title="Add attachment"
            >
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M21.44 11.05l-9.19 9.19a6 6 0 0 1-8.49-8.49l9.19-9.19a4 4 0 0 1 5.66 5.66l-9.2 9.19a2 2 0 0 1-2.83-2.83l8.49-8.48" />
              </svg>
            </button>
            <textarea
              ref={textareaRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              rows={1}
              placeholder={isStreaming ? "AI is responding..." : "Message Synapse..."}
              aria-label="Message"
              disabled={isStreaming || !activeConversationId}
              className="max-h-[200px] min-h-[56px] min-w-0 flex-1 resize-none bg-transparent px-3 py-3 text-base leading-7 text-[var(--color-text-primary)] outline-none placeholder:text-[var(--color-text-muted)] disabled:cursor-not-allowed disabled:opacity-60"
            />
            <div className="flex shrink-0 items-center gap-1.5">
              <button
                type="button"
                className="flex h-10 w-10 items-center justify-center rounded-full text-[var(--color-text-secondary)] transition-colors duration-200 hover:bg-[var(--color-bg-secondary)] hover:text-[var(--color-text-primary)] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-accent)]"
                aria-label="Voice input"
                title="Voice input"
              >
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <rect x="9" y="2" width="6" height="12" rx="3" />
                  <path d="M5 10a7 7 0 0 0 14 0" />
                  <line x1="12" y1="19" x2="12" y2="22" />
                </svg>
              </button>
              <button
                type="button"
                className="flex h-10 w-10 items-center justify-center rounded-full text-[var(--color-text-secondary)] transition-colors duration-200 hover:bg-[var(--color-bg-secondary)] hover:text-[var(--color-text-primary)] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-accent)]"
                aria-label="Audio mode"
                title="Audio mode"
              >
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M9 18V5l12-2v13" />
                  <circle cx="6" cy="18" r="3" />
                  <circle cx="18" cy="16" r="3" />
                </svg>
              </button>
              <button
                type="button"
                onClick={handleSend}
                disabled={!canSend}
                className={`flex h-10 w-10 items-center justify-center rounded-full transition-colors duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-accent)] ${
                  canSend
                    ? "bg-[var(--color-accent)] text-white hover:bg-[var(--color-accent-hover)]"
                    : "cursor-not-allowed bg-[var(--color-bg-secondary)] text-[var(--color-text-muted)]"
                }`}
                aria-label="Send message"
                title="Send message"
              >
                {isStreaming ? <Spinner size="sm" /> : (
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M12 19V5" />
                    <path d="M5 12l7-7 7 7" />
                  </svg>
                )}
              </button>
            </div>
          </div>
        </div>
        <p className="mt-2.5 text-center text-[13px] text-[var(--color-text-muted)]">Synapse can make mistakes. Verify important info.</p>
      </div>
    </div>
  )
}
