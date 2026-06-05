import { ChatLayout } from "@/components/layout";

import {
  ChatHeader,
  MessageInput,
  MessageList,
} from "@/features/chat";

import { useChat } from "@/features/chat/hooks/useChat";

export default function App() {
  const {
    messages,
    streamingMessage,
    isStreaming,
    handleSendMessage,
  } = useChat();

  return (
    <ChatLayout>
      <div className="flex h-full flex-col">
        
        <ChatHeader title="Synapse" />

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