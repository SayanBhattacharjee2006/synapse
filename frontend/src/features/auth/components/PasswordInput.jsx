import { useState } from "react";
import { Eye, EyeOff, Lock } from "lucide-react";

function PasswordInput({ value, onChange, ...inputProps }) {
    const [showPassword, setShowPassword] = useState(false);

    return (
        <div className="flex flex-col gap-auth-field-gap">
            <label className="text-xs font-black uppercase tracking-[0.16em] text-[var(--color-foreground)]">
                Password
            </label>
            <div className="flex h-auth-field items-center gap-3 border-[var(--auth-line)] bg-[var(--auth-panel-background)] px-4 [border-width:var(--auth-border-width)]">
                <Lock size={18} className="shrink-0 text-[var(--auth-icon)]" />
                <input
                    type={showPassword ? "text" : "password"}
                    value={value}
                    onChange={onChange}
                    placeholder="YOUR PASSWORD"
                    {...inputProps}
                    className="h-full w-full bg-transparent text-sm font-medium normal-case text-[var(--color-foreground)] outline-none placeholder:uppercase placeholder:text-[var(--auth-muted)]"
                />
                <button
                    type="button"
                    onClick={() => setShowPassword((prev) => !prev)}
                    className="flex h-10 w-10 shrink-0 items-center justify-center text-[var(--auth-line)]"
                    aria-label={showPassword ? "Hide password" : "Show password"}
                >
                    {showPassword ? (
                        <EyeOff size={18} />
                    ) : (
                        <Eye size={18} />
                    )}
                </button>
            </div>
        </div>
    );
}

export default PasswordInput;
