import {
  BrowserRouter,
  Navigate,
  Route,
  Routes,
} from "react-router-dom";

import ChatPage from "@/pages/ChatPage";

export default function AppRouter() {
  return (
    <BrowserRouter>
      <Routes>

        {/* Redirect Root */}
        <Route
          path="/"
          element={
            <Navigate
              to="/chat"
              replace
            />
          }
        />

        {/* Chat */}
        <Route
          path="/chat/:conversationId?"
          element={<ChatPage />}
        />

      </Routes>
    </BrowserRouter>
  );
}