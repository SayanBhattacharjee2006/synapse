import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import ProtectedRoute from "@/routes/ProtectedRoute.jsx";
import ChatPage from "@/features/chat/pages/ChatPage";
import PublicRoute from "@/routes/PublicRoute.jsx";
import { LoginPage, RegisterPage } from "@/features/auth";

export default function AppRouter() {
    return (
        <BrowserRouter>
            <Routes>
                <Route element={<PublicRoute />}>
                    <Route path="/login" element={<LoginPage />} />
                    <Route path="/register" element={<RegisterPage />} />
                </Route>

                <Route element={<ProtectedRoute />}>
                    {/* Redirect Root */}
                    <Route path="/" element={<Navigate to="/chat" replace />} />
                    {/* Chat */}
                    <Route
                        path="/chat/:conversationId?"
                        element={<ChatPage />}
                    />
                </Route>
            </Routes>
        </BrowserRouter>
    );
}
