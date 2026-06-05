import { useState } from "react";

import Sidebar from "@/components/layout/Sidebar";

import {
    ChatHeader,
    MessageInput,
    MessageList,
} from "@/features/chat";
import { useChat } from "@/features/chat/hooks/useChat";
import { useConversationStore } from "@/features/conversations/store/ConversationStore";

export default function ChatPage() {
    const [sidebarOpen, setSidebarOpen] = useState(false);
    const {
        activeConversationId,
        messages,
        isStreaming,
        handleSendMessage,
    } = useChat();
    const { conversations } = useConversationStore();

    const activeConversation = conversations.find(
        (conversation) =>
            String(conversation.id) === String(activeConversationId)
    );
    const headerTitle =
        activeConversation?.title?.trim() || "Synapse";

    return (
        <div className="relative flex h-[var(--app-height)] min-h-[var(--app-height)] overflow-hidden bg-[var(--color-bg-primary)] text-[var(--color-text-primary)]">
            {sidebarOpen && (
                <div
                    className="fixed inset-0 z-40 bg-black/50 backdrop-blur-sm transition-opacity md:hidden"
                    onClick={() => setSidebarOpen(false)}
                />
            )}

            <Sidebar
                isOpen={sidebarOpen}
                onClose={() => setSidebarOpen(false)}
            />

            <main className="flex min-h-0 min-w-0 flex-1 flex-col overflow-hidden bg-[var(--color-bg-primary)]">
                <ChatHeader
                    title={headerTitle}
                    onOpenSidebar={() => setSidebarOpen(true)}
                />

                <MessageList
                    conversationId={activeConversationId}
                    messages={messages}
                />

                <MessageInput
                    onSendMessage={handleSendMessage}
                    isStreaming={isStreaming}
                />
            </main>
        </div>
    );
}
