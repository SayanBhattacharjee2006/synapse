import { fetchEventSource } from "@microsoft/fetch-event-source";

import api from "@/library/api.js";
import {
    readRetrievalPayload,
    readWebPayload,
} from "@/features/chat/utils/sourceUtils.js";

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

const readStatusPayload = (data) => {
    try {
        const payload = JSON.parse(data);

        if (
            !payload ||
            typeof payload !== "object" ||
            Array.isArray(payload) ||
            typeof payload.status !== "string" ||
            typeof payload.message !== "string"
        ) {
            return null;
        }

        return {
            status: payload.status,
            message: payload.message,
        };
    } catch {
        return null;
    }
};

const readErrorPayload = (data) => {
    try {
        const payload = JSON.parse(data);

        if (
            !payload ||
            typeof payload !== "object" ||
            Array.isArray(payload) ||
            typeof payload.message !== "string"
        ) {
            return null;
        }

        return payload;
    } catch {
        return null;
    }
};

const buildStreamUrl = (path) => {
    return `/api/v1${path}`;
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
    onStatus,
    onError,
    onRetrieval,
    onWeb,
) => {
    await fetchEventSource(
        buildStreamUrl(`/conversations/${conversationId}/chat`),
        {
            method: "POST",
            body: JSON.stringify(data),
            headers: buildStreamHeaders(),
            // Keep the same request alive when the tab loses focus. The
            // library otherwise aborts it and opens a new POST on return.
            openWhenHidden: true,
            onmessage: (event) => {
                if (event.data === "[DONE]") {
                    onDone();
                    return;
                }

                if (event.event === "title") {
                    onTitle?.(readTitlePayload(event.data));
                    return;
                }

                if (event.event === "status") {
                    const status = readStatusPayload(event.data);

                    if (status) {
                        onStatus?.(status);
                    }

                    return;
                }

                if (event.event === "retrieval_found") {
                    const docs = readRetrievalPayload(event.data);

                    if (docs && docs.length > 0) {
                        onRetrieval?.(docs);
                    }

                    return;
                }

                if (event.event === "web_found") {
                    const web = readWebPayload(event.data);

                    if (web && web.length > 0) {
                        onWeb?.(web);
                    }

                    return;
                }

                if (event.event === "error") {
                    const error = readErrorPayload(event.data);

                    onError(
                        error ?? new Error("Unable to process your request."),
                    );
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
