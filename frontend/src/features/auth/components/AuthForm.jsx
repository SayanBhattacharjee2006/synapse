function AuthForm({ children, hasOffset = false }) {
    return (
        <div className="relative w-full max-w-auth-panel">
            {hasOffset ? (
                <div className="absolute left-auth-panel-offset top-auth-panel-offset h-full w-full bg-[var(--color-primary)]" />
            ) : null}
            <div className="relative flex flex-col gap-auth-panel-gap border-[var(--auth-line)] bg-[var(--auth-panel-background)] p-auth-panel-padding [border-width:var(--auth-border-width)]">
                {children}
            </div>
        </div>
    );
}

export default AuthForm;
