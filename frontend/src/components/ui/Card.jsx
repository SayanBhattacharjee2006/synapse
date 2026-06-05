import { cn } from "@/lib/utils";

export default function Card({
  children,
  className,
  ...props
}) {
  const base =
    "border-2 border-[var(--color-border)] bg-[var(--color-background)] shadow-[6px_6px_0px_var(--color-border)]";

  return (
    <div
      className={cn(base, className)}
      {...props}
    >
      {children}
    </div>
  );
}