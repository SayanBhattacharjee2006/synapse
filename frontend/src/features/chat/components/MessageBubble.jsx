import { cn } from "@/lib/utils";

export default function MessageBubble({
  sender = "assistant",
  content,
}) {
  const isUser = sender === "user";

  return (
    <div
      className={cn(
        "flex w-full",
        isUser ? "justify-end" : "justify-start"
      )}
    >
      <div
        className={cn(
          "max-w-[80%] border-2 border-[var(--color-border)] px-4 py-3 shadow-[4px_4px_0px_var(--color-border)]",

          isUser
            ? "bg-[var(--color-primary)] text-[var(--color-foreground)]"
            : "bg-[var(--color-background)] text-[var(--color-foreground)]"
        )}
      >
        <p className="whitespace-pre-wrap break-words text-sm font-medium">
          {content}
        </p>
      </div>
    </div>
  );
}