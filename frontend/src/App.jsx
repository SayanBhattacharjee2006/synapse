import { useEffect } from "react";
import AppRouter from "@/routes/AppRouter";
import { useAuthStore } from "@/features/auth";

export default function App() {
  const checkAuthentication = useAuthStore((state) => state.checkAuthentication);

  useEffect(() => {
    checkAuthentication();
  }, [checkAuthentication]);

  return <AppRouter />;
}
