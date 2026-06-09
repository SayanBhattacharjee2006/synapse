import { Link } from "react-router-dom";

function AuthLayout({
    children,
    navLabel = "Login",
    navTo = "/login",
    navIcon,
    navVariant = "outline",
}) {
    const navClassName =
        navVariant === "solid"
            ? "border-[var(--auth-line)] bg-[var(--color-primary)] text-black shadow-[var(--auth-button-shadow)] hover:-translate-x-1 hover:-translate-y-1"
            : "border-[var(--auth-line)] bg-[var(--auth-panel-background)] text-[var(--color-foreground)] shadow-[0.375rem_0.375rem_0_var(--color-primary)] hover:-translate-x-1 hover:-translate-y-1";

    return (
        <div className="min-h-app-height overflow-y-auto bg-[var(--auth-page-background)] text-[var(--color-foreground)] transition-colors duration-300">
            <header className="flex h-auth-header items-center border-[var(--auth-header-border)] px-auth-page [border-bottom-width:var(--auth-border-width)]">
                <div className="flex w-full items-center justify-between gap-4">
                    <div className="flex items-center gap-3">
                        <h1 className="font-display text-2xl font-black uppercase leading-none md:text-3xl">
                            SYNAPSE
                        </h1>
                        <span className="hidden h-1 w-[4.5rem] bg-[var(--color-primary)] sm:block" />
                    </div>

                    <Link
                        to={navTo}
                        className={`inline-flex h-10 items-center justify-center gap-2 px-4 font-display text-[0.7rem] font-black uppercase leading-none transition-transform duration-150 [border-width:var(--auth-border-width)] md:h-12 md:px-5 md:text-base ${navClassName}`}
                    >
                        {navIcon}
                        <span>{navLabel}</span>
                    </Link>
                </div>
            </header>

            <main className="flex min-h-auth-main items-center justify-center px-auth-page py-10 md:py-12">
                {children}
            </main>
        </div>
    );
}

export default AuthLayout;
