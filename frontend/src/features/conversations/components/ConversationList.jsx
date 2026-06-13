import { ConversationItem } from "@/features/conversations";

export default function ConversationList({
  conversations = [],
  activeConversationId,
  onSelectConversation,
  onRenameConversation,
  onDeleteConversation,
}) {
  if (conversations.length === 0) {
    return (
      <div className="flex h-full items-center justify-center">
        <p className="text-base font-bold uppercase text-[var(--color-muted)]">
          No conversations
        </p>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-3">
      {conversations.map((conversation) => (
        <ConversationItem
          key={conversation.id}
          title={
            conversation.title?.trim() ||
            "New Chat"
          }
          updatedAt={conversation.updatedAt || conversation.updated_at}
          active={String(conversation.id) === String(activeConversationId)}
          onClick={() =>
            onSelectConversation?.(conversation.id)
          }
          onRename={(title) =>
            onRenameConversation?.(conversation.id, title)
          }
          onDelete={() =>
            onDeleteConversation?.(conversation.id)
          }
        />
      ))}
    </div>
  );
}
