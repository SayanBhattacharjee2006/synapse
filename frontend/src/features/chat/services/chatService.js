import { fetchEventSource } from "@microsoft/fetch-event-source";

import api from "@/library/api.js";

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

const buildStreamUrl = (path) => {
    const baseURL = api.defaults.baseURL || "/api/v1";

    return `${baseURL.replace(/\/$/, "")}${path}`;
};

const buildStreamHeaders = () => {
    const headers = { "Content-Type": "application/json" };
    const token = localStorage.getItem("access_token");

    if (token) {
        headers.Authorization = `Bearer ${token}`;
    }

    return headers;
};

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
    await fetchEventSource(
        buildStreamUrl(`/conversations/${conversationId}/chat`),
        {
            method: "POST",
            body: JSON.stringify(data),
            headers: buildStreamHeaders(),
            onmessage: (event) => {
                if (event.data === "[DONE]") {
                    onDone();
                    return;
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
            },
        },
    );
};
