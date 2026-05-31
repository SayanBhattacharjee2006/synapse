export default function Button({
    children,
    onClick,
    variant = "primary",
    size = "md",
    disabled = false,
    className = "",
    ...props
}) {
    const base =
        "inline-flex items-center justify-center gap-2 rounded-xl font-medium transition-colors duration-200 cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-accent)] focus-visible:ring-offset-2 focus-visible:ring-offset-[var(--color-bg-primary)]";

    const variants = {
        primary:
            "bg-[var(--color-accent)] hover:bg-[var(--color-accent-hover)] text-white",
        ghost: "bg-transparent hover:bg-[var(--color-bg-elevated)] text-[var(--color-text-secondary)]",
        danger: "bg-transparent hover:bg-red-500/10 text-[var(--color-error)]",
    };

    const sizes = {
        sm: "min-h-10 px-4 py-2 text-sm",
        md: "min-h-12 px-5 py-3 text-base",
        icon: "h-9 w-9 p-0 text-sm",
    };

    return (
        <button
            onClick={onClick}
            disabled={disabled}
            {...props}
            className={`${base} ${sizes[size]} ${variants[variant]} ${className}`}
        >
            {children}
        </button>
    );
}
