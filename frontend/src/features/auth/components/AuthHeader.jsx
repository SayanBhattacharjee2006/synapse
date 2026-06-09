function AuthHeader({ title, icon, variant = "compact" }) {
    const isHero = variant === "hero";

    return (
        <div className="flex flex-col gap-3">
            <div className="flex items-center gap-3">
                <div
                    className={
                        isHero
                            ? "flex h-12 w-12 shrink-0 items-center justify-center border-[var(--auth-line)] bg-[var(--color-primary)] text-black [border-width:var(--auth-border-width)]"
                            : "flex shrink-0 items-center justify-center text-[var(--auth-icon)]"
                    }
                >
                    {icon}
                </div>
                <h1 className="font-display text-2xl font-black uppercase leading-none text-[var(--color-foreground)] md:text-4xl">
                    {title}
                </h1>
            </div>
            <div
                className={
                    isHero
                        ? "h-auth-line w-full bg-[var(--auth-line)]"
                        : "h-auth-line w-28 bg-[var(--color-primary)]"
                }
            />
        </div>
    );
}

export default AuthHeader;
