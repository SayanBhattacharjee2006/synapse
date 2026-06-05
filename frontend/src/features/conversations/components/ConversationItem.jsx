import { cn } from "@/lib/utils";

export default function ConversationItem({
  title,
  updatedAt,
  active = false,
  onClick,
}) {
  return (
    <button
      onClick={onClick}
      className={cn(
        "w-full border-2 border-[var(--color-border)] bg-[var(--color-convo)] p-4 text-left transition-all duration-150 hover:translate-x-[2px] hover:translate-y-[2px] hover:shadow-none dark:font-extrabold dark:text-white",
        
        active && "border-black bg-[var(--color-primary)] font-extrabold text-black shadow-[4px_4px_0px_black] dark:shadow-[4px_4px_0px_white]" 
      )}
    >
      <div className="flex flex-col gap-1">
        <h3
          className={cn(
            "truncate uppercase text-base",
            active && "font-extrabold text-black"
          )}
        >
          {title}
        </h3>

        <p
          className={cn(
            "text-sm uppercase",
            active
              ? "text-black"
              : "text-[var(--color-muted)] dark:text-white"
          )}
        >
          {updatedAt}
        </p>
      </div>
    </button>
  );
}
