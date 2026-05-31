export default function Spinner({ size = "sm" }) {
    const sizes = { sm: "w-4 h-4", md: "w-6 h-6", lg: "w-8 h-8" };
    return (
        <div
            className={`${sizes[size]} rounded-full border-2 border-[var(--color-border)] border-t-[var(--color-accent)] animate-spin`}
        />
    );
}
