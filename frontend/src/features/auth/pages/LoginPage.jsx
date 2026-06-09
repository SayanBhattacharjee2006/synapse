import {
    AuthFooter,
    AuthForm,
    AuthHeader,
    AuthInput,
    PasswordInput,
    SubmitButton,
    AuthLayout,
} from "@/features/auth/components";
import { LogIn, Mail, Zap } from "lucide-react";

function LoginPage() {
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
                <form className="flex flex-col gap-auth-form-gap">
                    <AuthInput
                        label="Email"
                        placeholder="YOUR EMAIL"
                        type="email"
                        icon={<Mail size={20} />}
                    />
                    <PasswordInput />
                    <SubmitButton>Login</SubmitButton>
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
