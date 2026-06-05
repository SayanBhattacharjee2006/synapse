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
          "max-w-[80%] border-2 border-[var(--color-border)] px-6 py-4 shadow-[4px_4px_0px_var(--color-border)]",

          isUser
            ? "border-black bg-[var(--color-primary)] font-extrabold text-black shadow-[4px_4px_0px_black] dark:shadow-[4px_4px_0px_white]"
            : "border-black bg-[#F5F5F5] font-extrabold text-black shadow-[6px_6px_0px_var(--color-primary)]"
        )}
      >
        <p className="whitespace-pre-wrap break-words text-base font-extrabold">
          {content}
        </p>
      </div>
    </div>
  );
}
