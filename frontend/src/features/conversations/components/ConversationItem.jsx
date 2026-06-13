import { useState } from "react";

import { cn } from "@/lib/utils";
import { Check, Pencil, Trash2, X } from "lucide-react";

const formatUpdatedAt = (value) => {
  if (!value) {
    return "No activity";
  }

  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return new Intl.DateTimeFormat(undefined, {
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
  }).format(date);
};

export default function ConversationItem({
  title,
  updatedAt,
  active = false,
  onClick,
  onRename,
  onDelete,
}) {
  const [isEditing, setIsEditing] = useState(false);
  const [draftTitle, setDraftTitle] = useState(title);

  const handleStartEdit = () => {
    setDraftTitle(title);
    setIsEditing(true);
  };

  const handleCancelEdit = () => {
    setDraftTitle(title);
    setIsEditing(false);
  };

  const handleRename = async (event) => {
    event.preventDefault();

    const nextTitle = draftTitle.trim();

    if (!nextTitle) {
      return;
    }

    await onRename?.(nextTitle);
    setIsEditing(false);
  };

  const handleDelete = async () => {
    const shouldDelete = window.confirm(
      "Delete this conversation?"
    );

    if (!shouldDelete) {
      return;
    }

    await onDelete?.();
  };

  const actionButtonClass = cn(
    "flex h-9 w-9 shrink-0 items-center justify-center border-2 border-[var(--color-border)] bg-[var(--color-background)] text-[var(--color-foreground)] transition-all duration-150 hover:translate-x-[1px] hover:translate-y-[1px]",
    active && "border-black bg-white text-black"
  );

  return (
    <div
      className={cn(
        "w-full border-2 border-[var(--color-border)] bg-[var(--color-convo)] p-3 text-left transition-all duration-150 hover:translate-x-[2px] hover:translate-y-[2px] hover:shadow-none dark:font-extrabold dark:text-white",
        
        active && "border-black bg-[var(--color-primary)] font-extrabold text-black shadow-[4px_4px_0px_black] dark:shadow-[4px_4px_0px_white]" 
      )}
    >
      {isEditing ? (
        <form
          className="flex items-center gap-2"
          onSubmit={handleRename}
        >
          <input
            className="min-w-0 flex-1 border-2 border-[var(--color-border)] bg-[var(--color-background)] px-3 py-2 text-sm font-bold uppercase text-[var(--color-foreground)] outline-none focus:shadow-[3px_3px_0px_var(--color-border)]"
            value={draftTitle}
            onChange={(event) => setDraftTitle(event.target.value)}
            autoFocus
            aria-label="Conversation title"
          />

          <button
            type="submit"
            className={actionButtonClass}
            aria-label="Save conversation title"
            title="Save"
          >
            <Check size={16} />
          </button>

          <button
            type="button"
            className={actionButtonClass}
            onClick={handleCancelEdit}
            aria-label="Cancel title edit"
            title="Cancel"
          >
            <X size={16} />
          </button>
        </form>
      ) : (
        <div className="flex items-start gap-2">
          <button
            type="button"
            onClick={onClick}
            className="min-w-0 flex-1 text-left"
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
                  "text-sm uppercase font-semibold tracking-wide",
                  active
                    ? "text-black"
                    : "text-[var(--color-muted)] dark:text-white"
                )}
              >
                {formatUpdatedAt(updatedAt)}
              </p>
            </div>
          </button>

          <div className="flex shrink-0 items-center gap-1">
            <button
              type="button"
              className={actionButtonClass}
              onClick={handleStartEdit}
              aria-label={`Rename ${title}`}
              title="Rename"
            >
              <Pencil size={15} />
            </button>

            <button
              type="button"
              className={cn(
                actionButtonClass,
                "hover:bg-[var(--color-danger)] hover:text-white"
              )}
              onClick={handleDelete}
              aria-label={`Delete ${title}`}
              title="Delete"
            >
              <Trash2 size={15} />
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
