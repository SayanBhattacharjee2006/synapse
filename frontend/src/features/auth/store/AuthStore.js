import { create } from "zustand";
import { authCheck, login, register } from "@/features/auth/services";

export const useAuthStore = create((set) => ({
    user: null,
    isAuthenticated: false,
    isAuthLoading: false,
    error: null,
    isLoading: false,
    token: null,

    login: async (data) => {
        try {
            set({
                isLoading: true,
                user: null,
                token: null,
            });

            const response = await login(data);

            localStorage.setItem("access_token", response.data.access_token);

            set({
                isLoading: false,
                user: buildUser(response.data),
                token: response.data.access_token,
                isAuthenticated: true,
                error: null,
            });
        } catch (error) {
            set({
                isLoading: false,
                error: error?.response?.data?.detail || error.message,
            });
        } finally {
            set({
                isLoading: false,
            });
        }
    },

    register: async (data) => {
        try {
            set({
                isLoading: true,
                user: null,
                token: null,
            });

            const response = await register(data);

            localStorage.setItem("access_token", response.data.access_token);

            set({
                isLoading: false,
                user: buildUser(response.data),
                token: response.data.access_token,
                isAuthenticated: true,
                error: null,
            });
        } catch (error) {
            set({
                isLoading: false,
                error: error?.response?.data?.detail || error.message,
            });
        } finally {
            set({
                isLoading: false,
            });
        }
    },

    logout: () => {
        localStorage.removeItem("access_token");
        set({
            user: null,
            isAuthenticated: false,
            token: null,
        });
    },

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
                set({
                    user: buildUser(response.data),
                    token: token,
                    isAuthenticated: true,
                    isAuthLoading: false,
                    error: null,
                });
            } catch (error) {
                localStorage.removeItem("access_token");
                set({
                    user: null,
                    isAuthenticated: false,
                    token: null,
                    isAuthLoading: false,
                    error: error?.response?.data?.detail || error.message,
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
