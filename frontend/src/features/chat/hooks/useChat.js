import { useEffect } from "react";

import { useParams } from "react-router-dom";

import { useChatStore } from "@/features/chat/store/ChatStore";

import { useConversationStore } from "@/features/conversations/store/ConversationStore";

export function useChat() {
  const { conversationId } = useParams();

  const {
    setActiveConversationId,
  } = useConversationStore();

  const {
    messages,
    streamingMessage,
    isStreaming,
    clearMessages,
    loadMessages,
    sendMessage,
  } = useChatStore();

  useEffect(() => {
    if (!conversationId) {
      setActiveConversationId(null);
      clearMessages();
      return;
    }

    setActiveConversationId(
      conversationId
    );

    loadMessages(conversationId);
  }, [
    conversationId,
    clearMessages,
    loadMessages,
    setActiveConversationId,
  ]);

  const handleSendMessage = async (
    content
  ) => {
    if (!conversationId) {
      return;
    }

    await sendMessage(
      conversationId,
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

    activeConversationId:
      conversationId,

    handleSendMessage,
  };
}
