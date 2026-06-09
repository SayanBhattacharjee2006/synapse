import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
    AuthFooter,
    AuthForm,
    AuthHeader,
    AuthInput,
    PasswordInput,
    SubmitButton,
    AuthLayout,
} from "@/features/auth/components";
import { useAuthStore } from "@/features/auth/store";
import { LogIn, Mail, Zap } from "lucide-react";

function LoginPage() {
    const navigate = useNavigate();
    const { clearError, error, isLoading, login } = useAuthStore();
    const [formData, setFormData] = useState({
        email: "",
        password: "",
    });

    useEffect(() => {
        clearError();
    }, [clearError]);

    const handleChange = (field) => (event) => {
        clearError();
        setFormData((current) => ({
            ...current,
            [field]: event.target.value,
        }));
    };

    const handleSubmit = async (event) => {
        event.preventDefault();

        const result = await login({
            email: formData.email.trim().toLowerCase(),
            password: formData.password,
        });

        if (result.success) {
            navigate("/chat", { replace: true });
        }
    };

    return (
        <AuthLayout
            navLabel="Get Started"
            navTo="/register"
            navIcon={<Zap size={22} />}
            navVariant="solid"
        >
            <AuthForm>
                <AuthHeader
                    title="Login"
                    icon={<LogIn size={28} />}
                    variant="hero"
                />
                <form
                    className="flex flex-col gap-auth-form-gap"
                    onSubmit={handleSubmit}
                >
                    <AuthInput
                        label="Email"
                        placeholder="YOUR EMAIL"
                        type="email"
                        value={formData.email}
                        onChange={handleChange("email")}
                        icon={<Mail size={20} />}
                        autoComplete="email"
                        required
                    />
                    <PasswordInput
                        value={formData.password}
                        onChange={handleChange("password")}
                        autoComplete="current-password"
                        minLength={6}
                        maxLength={20}
                        required
                    />
                    {error ? (
                        <p className="border-[var(--color-danger)] px-3 py-2 text-xs font-black uppercase tracking-[0.12em] text-[var(--color-danger)] [border-width:var(--auth-border-width)]" role="alert">
                            {error}
                        </p>
                    ) : null}
                    <SubmitButton disabled={isLoading}>
                        {isLoading ? "Logging In" : "Login"}
                    </SubmitButton>
                </form>
                <AuthFooter
                    text="Don't have an account?"
                    linkText="Register"
                    to="/register"
                />
            </AuthForm>
        </AuthLayout>
    );
}

export default LoginPage;
