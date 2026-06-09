import { Navigate, Outlet } from "react-router-dom";
import { Spinner } from "@/components/ui";
import { useAuthStore } from "@/features/auth";

function ProtectedRoute() {
    const { isAuthenticated, isAuthLoading } = useAuthStore();

    if (isAuthLoading) {
        return <Spinner size="lg" />;
    }

    return isAuthenticated ? <Outlet /> : <Navigate to="/login" replace />;
}

export default ProtectedRoute;
