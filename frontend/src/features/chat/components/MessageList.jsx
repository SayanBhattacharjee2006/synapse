import {
  useCallback,
  useLayoutEffect,
  useRef,
  useState,
} from "react";

import { Button } from "@/components/ui";
import { MessageBubble } from "@/features/chat";
import { ArrowDown } from "lucide-react";

const BOTTOM_THRESHOLD = 32;

export default function MessageList({
  conversationId,
  messages = [],
}) {
  const scrollContainerRef = useRef(null);
  const previousConversationIdRef = useRef(conversationId);
  const wasAtBottomRef = useRef(true);
  const [showScrollButton, setShowScrollButton] = useState(false);

  const isAtBottom = useCallback((scrollContainer) => {
    const distanceFromBottom =
      scrollContainer.scrollHeight -
      scrollContainer.scrollTop -
      scrollContainer.clientHeight;

    return distanceFromBottom <= BOTTOM_THRESHOLD;
  }, []);

  const scrollToBottom = useCallback((behavior = "smooth") => {
    const scrollContainer = scrollContainerRef.current;

    if (!scrollContainer) {
      return;
    }

    scrollContainer.scrollTo({
      top: scrollContainer.scrollHeight,
      behavior,
    });

    wasAtBottomRef.current = true;
    setShowScrollButton(false);
  }, []);

  const updateScrollButton = useCallback(() => {
    const scrollContainer = scrollContainerRef.current;

    if (!scrollContainer) {
      return;
    }

    const isScrolledToBottom = isAtBottom(scrollContainer);

    wasAtBottomRef.current = isScrolledToBottom;
    setShowScrollButton(!isScrolledToBottom);
  }, [isAtBottom]);

  const handleScroll = useCallback(() => {
    updateScrollButton();
  }, [updateScrollButton]);

  useLayoutEffect(() => {
    const scrollContainer = scrollContainerRef.current;

    if (!scrollContainer) {
      return;
    }

    if (messages.length === 0) {
      wasAtBottomRef.current = true;
      return;
    }

    const conversationChanged =
      previousConversationIdRef.current !== conversationId;

    if (conversationChanged || wasAtBottomRef.current) {
      scrollToBottom("auto");
    } else {
      updateScrollButton();
    }

    previousConversationIdRef.current = conversationId;
  }, [
    conversationId,
    messages,
    scrollToBottom,
    updateScrollButton,
  ]);

  if (messages.length === 0) {
    return (
      <div className="flex min-h-0 flex-1 items-center justify-center p-8">
        <p className="text-base font-bold uppercase text-[var(--color-muted)]">
          Start a conversation
        </p>
      </div>
    );
  }

  return (
    <div className="relative min-h-0 flex-1">
      <div
        ref={scrollContainerRef}
        className="h-full overflow-y-auto p-8"
        onScroll={handleScroll}
      >
        <div className="flex flex-col gap-6">
          {messages.map((message) => (
            <MessageBubble
              key={message.id}
              sender={message.sender}
              content={message.content}
            />
          ))}
        </div>
      </div>

      {showScrollButton && (
        <Button
          type="button"
          variant="primary"
          size="icon"
          className="absolute bottom-5 right-5 z-20 h-12 w-12 p-0"
          onClick={() => scrollToBottom("auto")}
          aria-label="Scroll to latest message"
          title="Scroll to latest message"
        >
          <ArrowDown size={22} strokeWidth={3} />
        </Button>
      )}
    </div>
  );
}
