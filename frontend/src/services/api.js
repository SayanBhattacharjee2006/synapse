import axios from "axios";
import { fetchEventSource } from "@microsoft/fetch-event-source";

const api = axios.create({
    baseURL: "http://localhost:8000/api/v1",
});

const readTitlePayload = (data) => {
    try {
        const payload = JSON.parse(data);

        if (typeof payload === "string") {
            return payload;
        }

        return payload?.title ?? payload?.titel;
    } catch {
        return data;
    }
};

// Conversations services
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

// Messages services
export const getMessages = async (conversationsId) => {
    const response = await api.get(
        `/conversations/${conversationsId}/messages`,
    );
    return response;
};

export const createMessage = async (conversationId, data) => {
    const response = await api.post(
        `/conversations/${conversationId}/messages`,
        data,
    );
    return response;
};

export const deleteMessage = async (conversationId, messageId) => {
    const response = await api.delete(
        `/conversations/${conversationId}/messages/${messageId}`,
    );
    return response;
};

export const streamChat = async (
    conversationId,
    data,
    onToken,
    onDone,
    onTitle,
    onError,
) => {
    await fetchEventSource(`http://localhost:8000/api/v1/conversations/${conversationId}/chat`,{
        method: "POST",
        body: JSON.stringify(data),
        headers: { "Content-Type": "application/json" },
        onmessage: (event) => {
            if(event.data === "[DONE]"){
                onDone();
                return ;
            }

            if (event.event === "title") {
                onTitle?.(readTitlePayload(event.data));
                return;
            }

            try {
                const payload = JSON.parse(event.data);
                const title = payload.title ?? payload.titel;

                if (title) {
                    onTitle?.(title);
                    return;
                }
            } catch {
                // Non-JSON data is a streamed assistant token.
            }

            onToken(event.data);
        },
        onerror(err) {
            onError(err);
            throw err;
        }
    });
};
