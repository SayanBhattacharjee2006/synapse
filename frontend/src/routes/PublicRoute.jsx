import Spinner from "@/components/ui/Spinner.jsx";
import { useAuthStore } from "@/features/auth/store/AuthStore.js";
import { Navigate, Outlet } from "react-router-dom";
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
