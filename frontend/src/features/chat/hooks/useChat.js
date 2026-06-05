import { useEffect } from "react";

import { useChatStore } from "@/features/chat/store/ChatStore";

import { useConversationStore } from "@/features/conversations/store/ConversationStore";

export function useChat() {
  const {
    activeConversationId,
  } = useConversationStore();

  const {
    messages,
    streamingMessage,
    isStreaming,
    loadMessages,
    sendMessage,
  } = useChatStore();

  useEffect(() => {
    if (!activeConversationId) {
      return;
    }

    loadMessages(activeConversationId);
  }, [activeConversationId]);

  const handleSendMessage = async (
    content
  ) => {
    if (!activeConversationId) {
      return;
    }

    await sendMessage(
      activeConversationId,
      {
        content,
        sender: "user",
      }
    );
  };

  return {
    messages,
    streamingMessage,
    isStreaming,

    activeConversationId,

    handleSendMessage,
  };
}