import { Navigate, Outlet } from "react-router-dom";
import { Spinner } from "@/components/ui";
import { useAuthStore } from "@/features/auth";

function PublicRoute() {
    const { isAuthenticated, isAuthLoading } = useAuthStore();
    return isAuthLoading ? (
        <Spinner size="lg" />
    ) : isAuthenticated ? (
        <Navigate to="/chat" replace />
    ) : (
        <Outlet />
    );
}

export default PublicRoute;
