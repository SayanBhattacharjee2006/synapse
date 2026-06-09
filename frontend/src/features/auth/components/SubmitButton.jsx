function SubmitButton({ children, type = "submit", disabled = false }) {
    return (
        <button
            type={type}
            disabled={disabled}
            className="flex h-auth-field w-full items-center justify-center border-[var(--auth-line)] bg-[var(--color-primary)] px-6 font-display text-sm font-black uppercase text-black shadow-[var(--auth-button-shadow)] transition-transform duration-150 [border-width:var(--auth-border-width)] hover:-translate-x-1 hover:-translate-y-1 disabled:pointer-events-none disabled:opacity-60 md:text-base"
        >
            {children}
        </button>
    );
}

export default SubmitButton;
