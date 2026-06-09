import { create } from "zustand";
import { authCheck, login, register } from "@/features/auth/services";

const getStoredToken = () => {
    try {
        return localStorage.getItem("access_token");
    } catch {
        return null;
    }
};

const normalizeError = (error) => {
    const detail = error?.response?.data?.detail;

    if (typeof detail === "string") {
        return detail;
    }

    if (Array.isArray(detail)) {
        return detail
            .map((item) => item?.msg || item?.message)
            .filter(Boolean)
            .join(", ");
    }

    return error?.message || "Something went wrong";
};

const initialToken = getStoredToken();

export const useAuthStore = create((set) => ({
    user: null,
    isAuthenticated: false,
    isAuthLoading: Boolean(initialToken),
    error: null,
    isLoading: false,
    token: initialToken,

    login: async (data) => {
        try {
            set({
                isLoading: true,
                error: null,
                user: null,
                token: null,
            });

            const response = await login(data);
            const user = buildUser(response.data);

            localStorage.setItem("access_token", response.data.access_token);

            set({
                isLoading: false,
                user,
                token: response.data.access_token,
                isAuthenticated: true,
                error: null,
            });

            return { success: true, user };
        } catch (error) {
            const message = normalizeError(error);

            set({
                isLoading: false,
                user: null,
                token: null,
                isAuthenticated: false,
                error: message,
            });

            return { success: false, error: message };
        }
    },

    register: async (data) => {
        try {
            set({
                isLoading: true,
                error: null,
                user: null,
                token: null,
            });

            const response = await register(data);
            const user = buildUser(response.data);

            localStorage.setItem("access_token", response.data.access_token);

            set({
                isLoading: false,
                user,
                token: response.data.access_token,
                isAuthenticated: true,
                error: null,
            });

            return { success: true, user };
        } catch (error) {
            const message = normalizeError(error);

            set({
                isLoading: false,
                user: null,
                token: null,
                isAuthenticated: false,
                error: message,
            });

            return { success: false, error: message };
        }
    },

    logout: () => {
        localStorage.removeItem("access_token");
        set({
            user: null,
            isAuthenticated: false,
            token: null,
            error: null,
            isLoading: false,
        });
    },

    clearError: () => set({ error: null }),

    checkAuthentication: async () => {
        set({ isAuthLoading: true });
        const token = localStorage.getItem("access_token");
        if (!token) {
            set({
                token: null,
                isAuthenticated: false,
                user: null,
                isAuthLoading: false,
                error: null,
            });
            return;
        } else {
            try {
                const response = await authCheck();
                console.log(response.data);
                set({
                    user: buildUser(response.data),
                    token: token,
                    isAuthenticated: true,
                    isAuthLoading: false,
                    error: null,
                });
            } catch {
                localStorage.removeItem("access_token");
                set({
                    user: null,
                    isAuthenticated: false,
                    token: null,
                    isAuthLoading: false,
                    error: null,
                });
            }
        }
    },
}));

const buildUser = (data) => ({
    id: data.id,
    email: data.email,
    display_name: data.display_name,
    created_at: data.created_at,
    updated_at: data.updated_at,
});
