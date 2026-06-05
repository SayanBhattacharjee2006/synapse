import { cn } from "@/lib/utils";

export default function Button({
  children,
  onClick,
  variant = "primary",
  size = "md",
  disabled = false,
  className,
  ...props
}) { 
  const base =
    "inline-flex items-center justify-center border-2 border-[var(--color-border)] font-bold uppercase transition-all duration-150 active:translate-x-[4px] active:translate-y-[4px] disabled:opacity-50 disabled:pointer-events-none";

  const variants = {
    primary:
      "border-black bg-[var(--color-primary)] font-extrabold text-black shadow-[4px_4px_0px_black] dark:shadow-[4px_4px_0px_white] hover:translate-x-[2px] hover:translate-y-[2px] hover:shadow-none",

    secondary:
      "bg-[var(--color-background)] text-[var(--color-foreground)] shadow-[4px_4px_0px_var(--color-border)] hover:translate-x-[2px] hover:translate-y-[2px] hover:shadow-none",

    ghost:
      "bg-transparent text-[var(--color-foreground)] hover:bg-[var(--color-surface)]",
  };

  const sizes = {
    sm: "h-10 px-4 text-base",
    md: "h-12 px-6 text-base",
    lg: "h-14 px-8 text-lg",
    icon: "h-12 w-12",
  };

  return (
    <button
      onClick={onClick}
      disabled={disabled}
      className={cn(base, variants[variant], sizes[size], className)}
      {...props}
    >
      {children}
    </button>
  );
}
