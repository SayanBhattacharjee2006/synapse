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
    <div className="border-t-2 border-[var(--color-border)] bg-[var(--color-background)] p-4">
      <div className="flex items-center gap-3">
        
        <Input
          value={message}
          onChange={(event) =>
            setMessage(event.target.value)
          }
          onKeyDown={handleKeyDown}
          placeholder="Type your message..."
          disabled={isStreaming}
        />

        <Button
          size="icon"
          onClick={handleSendMessage}
          disabled={!message.trim() || isStreaming}
        >
          <Send size={18} />
        </Button>
      </div>
    </div>
  );
}