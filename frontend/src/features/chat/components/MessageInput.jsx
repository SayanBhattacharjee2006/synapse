import { useState } from "react";

import { Button, Input } from "@/components/ui";
import { DocumentContextStrip } from "@/features/documents";
import { Send } from "lucide-react";

export default function MessageInput({
  onSendMessage,
  isStreaming = false,
  contextFiles = [],
  removingFileIds = [],
  onOpenFileContext,
  onRemoveContextFile,
}) {
  const [message, setMessage] = useState("");
  const hasContextFiles = contextFiles.length > 0;

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
    <div className="shrink-0 border-t-2 border-[var(--color-border)] bg-[var(--color-background)] p-4 pb-[calc(1rem_+_var(--safe-area-bottom))] sm:p-6 sm:pb-[calc(1.5rem_+_var(--safe-area-bottom))]">
      <DocumentContextStrip
        files={contextFiles}
        removingFileIds={removingFileIds}
        onOpenFiles={onOpenFileContext}
        onRemoveFile={onRemoveContextFile}
      />

      <div className="flex items-center gap-3 pt-0 data-[has-files=true]:pt-3" data-has-files={hasContextFiles}>
        <Input
          className="min-w-0 flex-1"
          value={message}
          onChange={(event) =>
            setMessage(event.target.value)
          }
          onKeyDown={handleKeyDown}
          placeholder={
            hasContextFiles
              ? "Ask anything about your files..."
              : "Type your message..."
          }
          disabled={isStreaming}
        />

        <Button
          size="md"
          onClick={handleSendMessage}
          disabled={!message.trim() || isStreaming}
          className="shrink-0 gap-2 p-6"
        >
          <Send size={18} />
          <span className="uppercase hidden md:inline">Send</span>
        </Button>
      </div>
    </div>
  );
}
