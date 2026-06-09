import api from "@/library/api.js";

export const login = async (data) => {
    const response = await api.post("/auth/login", data);
    return response;
}

export const register = async (data) => {
    const response = await api.post("/auth/register", data);
    return response;
}

export const authCheck = async () => {
    const response = await api.get("/auth/me");
    return response;
}