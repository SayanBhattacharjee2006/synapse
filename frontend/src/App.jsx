import { useState } from "react";

import { ChatLayout } from "@/components/layout";

import {
  ChatHeader,
  MessageInput,
  MessageList,
} from "@/features/chat";

import { useChat } from "@/features/chat/hooks/useChat";

import { useConversationStore } from "@/features/conversations/store/ConversationStore";

export default function App() {
  const [sidebarOpen, setSidebarOpen] =
    useState(false);

  const { conversations, activeConversationId } =
    useConversationStore();

  const {
    messages,
    streamingMessage,
    isStreaming,
    handleSendMessage,
  } = useChat();

  const activeConversation = conversations.find(
    (conversation) =>
      conversation.id === activeConversationId
  );

  const headerTitle =
    activeConversationId && activeConversation
      ? activeConversation.title?.trim() ||
        "New Chat"
      : "Synapse";

  return (
    <ChatLayout
      sidebarOpen={sidebarOpen}
      onCloseSidebar={() => setSidebarOpen(false)}
    >
      <div className="flex h-full flex-col">
        
        <ChatHeader
          title={headerTitle}
          onOpenSidebar={() => setSidebarOpen(true)}
        />

        {/* Messages */}
        <div className="flex-1 overflow-y-auto">
          <MessageList
            messages={[
              ...messages,

              ...(streamingMessage
                ? [
                    {
                      id: "streaming",
                      sender: "assistant",
                      content: streamingMessage,
                    },
                  ]
                : []),
            ]}
          />
        </div>

        {/* Input */}
        <MessageInput
          onSendMessage={handleSendMessage}
          isStreaming={isStreaming}
        />
      </div>
    </ChatLayout>
  );
}
