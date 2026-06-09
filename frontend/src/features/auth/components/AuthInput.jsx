function AuthInput({
    label,
    placeholder,
    type = "text",
    icon,
    value,
    onChange,
    textCase = type === "email" ? "lowercase" : "normal",
}) {
    const textCaseClassName =
        textCase === "lowercase"
            ? "lowercase"
            : textCase === "uppercase"
              ? "uppercase"
              : "normal-case";

    return (
        <div className="flex flex-col gap-auth-field-gap">
            <label className="text-xs font-black uppercase tracking-[0.16em] text-[var(--color-foreground)]">
                {label}
            </label>
            <div className="flex h-auth-field items-center gap-3 border-[var(--auth-line)] bg-[var(--auth-panel-background)] px-4 [border-width:var(--auth-border-width)]">
                <div className="flex shrink-0 text-[var(--auth-icon)]">{icon}</div>
                <input
                    type={type}
                    value={value}
                    onChange={onChange}
                    placeholder={placeholder}
                    className={`h-full w-full bg-transparent text-sm font-medium ${textCaseClassName} text-[var(--color-foreground)] outline-none placeholder:uppercase placeholder:text-[var(--auth-muted)]`}
                />
            </div>
        </div>
    );
}

export default AuthInput;
