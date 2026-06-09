import {
    AuthFooter,
    AuthForm,
    AuthHeader,
    AuthInput,
    PasswordInput,
    SubmitButton,
    AuthLayout,
} from "@/features/auth/components";
import { Mail, User, UserPlus } from "lucide-react";

function RegisterPage() {
    return (
        <AuthLayout navLabel="Login" navTo="/login" navVariant="outline">
            <AuthForm hasOffset>
                <AuthHeader
                    title="Create Account"
                    icon={<UserPlus size={28} />}
                />
                <form className="flex flex-col gap-auth-form-gap">
                    <AuthInput
                        label="Display Name"
                        placeholder="YOUR NAME"
                        icon={<User size={20} />}
                    />
                    <AuthInput
                        label="Email"
                        placeholder="YOUR EMAIL"
                        type="email"
                        icon={<Mail size={20} />}
                    />
                    <PasswordInput />
                    <SubmitButton>Create Account</SubmitButton>
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
