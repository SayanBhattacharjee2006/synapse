import api from "@/library/api.js";

export const getConversations = async () => {
    const response = await api.get("/conversations");
    return response;
};

export const getConversationsById = async (conversationId) => {
    const response = await api.get(`/conversations/${conversationId}`);
    return response;
};

export const createConversations = async () => {
    const response = await api.post("/conversations", {});
    return response;
};

export const updateConversations = async (conversationId, data) => {
    const response = await api.patch(`/conversations/${conversationId}`, data);
    return response;
};

export const deleteConversations = async (conversationId) => {
    const response = await api.delete(`/conversations/${conversationId}`);
    return response;
};
