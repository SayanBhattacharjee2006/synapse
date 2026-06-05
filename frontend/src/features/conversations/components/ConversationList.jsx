import { ConversationItem } from "@/features/conversations";

export default function ConversationList({
  conversations = [],
  activeConversationId,
  onSelectConversation,
}) {
  if (conversations.length === 0) {
    return (
      <div className="flex h-full items-center justify-center">
        <p className="text-sm font-bold uppercase text-[var(--color-muted)]">
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
          title={conversation.title}
          updatedAt={conversation.updatedAt}
          active={conversation.id === activeConversationId}
          onClick={() =>
            onSelectConversation(conversation.id)
          }
        />
      ))}
    </div>
  );
}