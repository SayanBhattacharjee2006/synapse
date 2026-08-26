import { cn } from "@/lib/utils";

export default function StreamingLoader({ statusMessage }) {
  return (
    <div className="flex w-full justify-start">
      <div
        className={cn(
          "max-w-[80%] border-2 border-black bg-[#F5F5F5] px-6 py-4 font-extrabold text-black",
          "shadow-[6px_6px_0px_var(--color-primary)]"
        )}
      >
        <div className="flex items-center gap-1.5">
          <span
            className="inline-block h-2.5 w-2.5 rounded-full bg-black animate-[brutal-bounce_1.4s_ease-in-out_infinite]"
            style={{ animationDelay: "0s" }}
          />
          <span
            className="inline-block h-2.5 w-2.5 rounded-full bg-black animate-[brutal-bounce_1.4s_ease-in-out_infinite]"
            style={{ animationDelay: "0.2s" }}
          />
          <span
            className="inline-block h-2.5 w-2.5 rounded-full bg-black animate-[brutal-bounce_1.4s_ease-in-out_infinite]"
            style={{ animationDelay: "0.4s" }}
          />
          {statusMessage && (
            <span className="ml-2 text-sm font-bold text-[var(--color-muted)]">
              {statusMessage}
            </span>
          )}
        </div>
      </div>
    </div>
  );
}
