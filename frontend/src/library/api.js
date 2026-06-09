import axios from "axios";

const api = axios.create({
    baseURL: import.meta.env.VITE_API_BASE_URL || "/api/v1",
});

api.interceptors.request.use(
    (config) => {
        const token = localStorage.getItem("access_token");
        if (token) {
            config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
    },
    (error) => {
        return Promise.reject(error);
    },
);


api.interceptors.response.use((response)=>{
    return response
},(error)=>{
    const requestUrl = error?.config?.url || "";
    const isAuthRequest =
        requestUrl.includes("/auth/login") ||
        requestUrl.includes("/auth/register");

    if(error?.response?.status === 401 && !isAuthRequest){
        localStorage.removeItem("access_token");
        if (window.location.pathname !== "/login") {
            window.location.href = "/login";
        }
    }
    return Promise.reject(error)
})

export default api;
