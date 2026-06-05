import { cn } from "@/lib/utils";

export default function Input({
  value,
  onChange,
  onKeyDown,
  placeholder,
  disabled = false,
  className,
  type = "text",
  ...props
}) {
  const base =
    "w-full border-2 border-[var(--color-border)] bg-[var(--color-background)] px-4 py-3 text-[var(--color-foreground)] outline-none shadow-[4px_4px_0px_var(--color-border)] transition-all duration-150 placeholder:text-[var(--color-muted)] focus:translate-x-[2px] focus:translate-y-[2px] focus:shadow-none disabled:cursor-not-allowed disabled:opacity-50";

  return (
    <input
      type={type}
      value={value}
      onChange={onChange}
      onKeyDown={onKeyDown}
      placeholder={placeholder}
      disabled={disabled}
      className={cn(base, className)}
      {...props}
    />
  );
}