import { useState } from "react";

import { Button, Input } from "@/components/ui";
import { Send } from "lucide-react";

export default function MessageInput({
  onSendMessage,
  isStreaming = false,
}) {
  const [message, setMessage] = useState("");

  const handleSendMessage = () => {
    const trimmedMessage = message.trim();

    if (!trimmedMessage || isStreaming) {
      return;
    }

    onSendMessage(trimmedMessage);
    setMessage("");
  };

  const handleKeyDown = (event) => {
    if (event.key === "Enter") {
      handleSendMessage();
    }
  };

  return (
    <div className="border-t-2 border-[var(--color-border)] bg-[var(--color-background)] p-6">
      <div className="flex items-center gap-3">
        
        <Input
          className="min-w-0 flex-1"
          value={message}
          onChange={(event) =>
            setMessage(event.target.value)
          }
          onKeyDown={handleKeyDown}
          placeholder="Type your message..."
          disabled={isStreaming}
        />

        <Button
          size="md"
          onClick={handleSendMessage}
          disabled={!message.trim() || isStreaming}
          className="shrink-0 gap-2 p-6"
        >
          <Send size={18} />
          <span className="uppercase">Send</span>
        </Button>
      </div>
    </div>
  );
}
