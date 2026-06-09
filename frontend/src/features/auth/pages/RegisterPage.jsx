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
import { Mail, User, UserPlus } from "lucide-react";

function RegisterPage() {
    const navigate = useNavigate();
    const { clearError, error, isLoading, register } = useAuthStore();
    const [formData, setFormData] = useState({
        displayName: "",
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

        const result = await register({
            display_name: formData.displayName.trim(),
            email: formData.email.trim().toLowerCase(),
            password: formData.password,
        });

        if (result.success) {
            navigate("/chat", { replace: true });
        }
    };

    return (
        <AuthLayout navLabel="Login" navTo="/login" navVariant="outline">
            <AuthForm hasOffset>
                <AuthHeader
                    title="Create Account"
                    icon={<UserPlus size={28} />}
                />
                <form
                    className="flex flex-col gap-auth-form-gap"
                    onSubmit={handleSubmit}
                >
                    <AuthInput
                        label="Display Name"
                        placeholder="YOUR NAME"
                        value={formData.displayName}
                        onChange={handleChange("displayName")}
                        icon={<User size={20} />}
                        autoComplete="name"
                        minLength={1}
                        maxLength={50}
                        required
                    />
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
                        autoComplete="new-password"
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
                        {isLoading ? "Creating Account" : "Create Account"}
                    </SubmitButton>
                </form>
                <AuthFooter
                    text="Already have an account?"
                    linkText="Login"
                    to="/login"
                />
            </AuthForm>
        </AuthLayout>
    );
}

export default RegisterPage;
