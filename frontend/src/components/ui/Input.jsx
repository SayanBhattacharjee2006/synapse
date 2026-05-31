export default function Input({
    value,
    onChange,
    onKeyDown,
    placeholder,
    "aria-label": ariaLabel,
    disabled = false,
    className = "",
}) {
    return (
        <input
            value={value}
            onChange={onChange}
            onKeyDown={onKeyDown}
            placeholder={placeholder}
            aria-label={ariaLabel}
            disabled={disabled}
            className={`min-h-12 w-full rounded-xl border border-[var(--color-border)] bg-[var(--color-bg-elevated)] px-5 py-3 text-base leading-6 text-[var(--color-text-primary)] outline-none transition-colors duration-200 placeholder:text-[var(--color-text-muted)] focus:border-[var(--color-accent)] focus:ring-2 focus:ring-[var(--color-accent)]/20 disabled:cursor-not-allowed disabled:opacity-60 ${className}`}
        />
    );
}
