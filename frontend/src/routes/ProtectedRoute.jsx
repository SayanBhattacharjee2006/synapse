import {useAuthStore} from "@/features/auth/store/AuthStore.js";
import Spinner from "@/components/ui/Spinner.jsx";
import { Navigate, Outlet } from "react-router-dom"

function ProtectedRoute() {
    const { isAuthenticated, isAuthLoading } = useAuthStore();

    if (isAuthLoading) {
        return <Spinner size="lg" />;
    }

    return isAuthenticated ? <Outlet/> : < Navigate to="/login" replace/>;
}

export default ProtectedRoute