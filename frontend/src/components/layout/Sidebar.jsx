import { useEffect } from "react";

import { Button, Card } from "@/components/ui";

import { ConversationList } from "@/features/conversations";

import { useConversationStore } from "@/features/conversations/store/ConversationStore";

import { Plus } from "lucide-react";

export default function Sidebar() {
  const {
    conversations,
    activeConversationId,
    loadConversations,
    setActiveConversationId,
    createConversation,
  } = useConversationStore();

  useEffect(() => {
    loadConversations();
  }, []);

  return (
    <aside className="flex h-screen w-[280px] flex-col gap-4 border-r-2 border-[var(--color-border)] bg-[var(--color-background)] p-4">
      
      {/* Logo */}
      <Card className="p-4">
        <h1 className="text-2xl font-black uppercase tracking-tight">
          Synapse
        </h1>
      </Card>

      {/* New Chat */}
      <Button
        className="w-full"
        onClick={createConversation}
      >
        <Plus size={18} />
        New Chat
      </Button>

      {/* Conversation List */}
      <div className="flex-1 overflow-y-auto">
        <ConversationList
          conversations={conversations}
          activeConversationId={activeConversationId}
          onSelectConversation={
            setActiveConversationId
          }
        />
      </div>

      {/* Footer */}
      <Card className="p-4">
        <div className="flex items-center justify-between">
          <span className="text-sm font-bold uppercase">
            Dark Mode
          </span>

          <div className="h-5 w-5 border-2 border-[var(--color-border)] bg-[var(--color-primary)]" />
        </div>
      </Card>
    </aside>
  );
}