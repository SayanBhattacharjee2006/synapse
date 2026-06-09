import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import ProtectedRoute from "@/routes/ProtectedRoute.jsx";
import ChatPage from "@/pages/ChatPage";

export default function AppRouter() {
    return (
        <BrowserRouter>
            <Routes>
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
