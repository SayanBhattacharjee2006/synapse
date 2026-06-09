import { Link } from "react-router-dom";

function AuthFooter({ text, linkText, to }) {
    return (
        <div className="text-center">
            <Link
                to={to}
                className="text-xs font-black uppercase tracking-[0.12em] text-[var(--auth-link)] underline underline-offset-4"
            >
                {text} {linkText}
            </Link>
        </div>
    );
}

export default AuthFooter;
