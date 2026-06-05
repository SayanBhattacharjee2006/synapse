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
        "w-full border-2 border-[var(--color-border)] bg-[var(--color-background)] p-4 text-left shadow-[4px_4px_0px_var(--color-border)] transition-all duration-150 hover:translate-x-[2px] hover:translate-y-[2px] hover:shadow-none",
        
        active && "bg-[var(--color-primary)]"
      )}
    >
      <div className="flex flex-col gap-1">
        <h3 className="truncate font-bold uppercase text-sm">
          {title}
        </h3>

        <p className="text-xs uppercase text-[var(--color-muted)]">
          {updatedAt}
        </p>
      </div>
    </button>
  );
}