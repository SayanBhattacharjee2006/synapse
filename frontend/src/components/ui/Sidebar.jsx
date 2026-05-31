import { useEffect } from "react"
import { useChatStore } from "../../stores/chatStore"
import ConversationItem from "../conversation/ConversationItem"
import Button from "../ui/Button"
import Spinner from "../ui/Spinner"

export default function Sidebar() {
  const { conversations, activeConversationId, isLoading, loadConversations, createConversation, deleteConversation, loadMessages } = useChatStore()

  useEffect(() => {
    loadConversations()
  }, [loadConversations])

  return (
    <aside className="flex h-screen w-72 shrink-0 flex-col border-r border-[var(--color-border)] bg-[var(--color-bg-secondary)] xl:w-80">
      <div className="border-b border-[var(--color-border)] p-6">
        <h1 className="mb-5 text-2xl font-semibold text-[var(--color-accent)]">Synapse</h1>
        <Button onClick={createConversation} className="w-full" disabled={isLoading}>
          + New Chat
        </Button>
      </div>

      <div className="flex-1 space-y-1 overflow-y-auto p-3">
        {isLoading && conversations.length === 0 ? (
          <div className="mt-6 flex justify-center"><Spinner size="md" /></div>
        ) : conversations.length === 0 ? (
          <p className="mt-6 text-center text-base text-[var(--color-text-muted)]">No conversations yet</p>
        ) : (
          conversations.map((convo) => (
            <ConversationItem
              key={convo.id}
              conversation={convo}
              isActive={activeConversationId === convo.id}
              onSelect={(id) => loadMessages(id)}
              onDelete={deleteConversation}
              onRename={() => {}}
            />
          ))
        )}
      </div>
    </aside>
  )
}
