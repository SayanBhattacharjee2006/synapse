import { create } from "zustand";

import {
    createMessage,
    getMessages,
    streamChat,
} from "@/features/chat/services/chatService";
import { useConversationStore } from "@/features/conversations/store/ConversationStore";

export const useChatStore = create((set, get) => ({
    messages: [],

    streamingMessage: "",

    streamingStatus: null,

    streamingSources: null,

    isStreaming: false,

    isLoading: false,

    error: null,

    clearMessages: () => {
        set({
            messages: [],
            streamingMessage: "",
            streamingStatus: null,
            streamingSources: null,
            isStreaming: false,
            isLoading: false,
            error: null,
        });
    },

    loadMessages: async (conversationId) => {
        try {
            set({
                isLoading: true,
                error: null,
                streamingSources: null,
            });

            const response = await getMessages(conversationId);

            set({
                messages: response.data,

                isLoading: false,
                error: null,
            });
        } catch (error) {
            set({
                isLoading: false,
                error: error.message,
            });
        }
    },

    sendMessage: async (conversationId, data) => {
        try {
            set({
                isLoading: true,
                error: null,
            });

            const createdMessage = await createMessage(conversationId, data);

            set((state) => ({
                messages: [...state.messages, createdMessage.data],

                isStreaming: true,
                streamingMessage: "",
                streamingStatus: null,
                streamingSources: null,

                isLoading: false,
            }));

            await streamChat(
                conversationId,

                data,

                (token) => {
                    set((state) => ({
                        streamingMessage: state.streamingMessage + token,
                    }));
                },

                async () => {
                    if (!get().isStreaming) {
                        return;
                    }

                    set({ streamingStatus: null });

                    const currentSources = get().streamingSources;
                    const hasValidSources =
                        currentSources &&
                        ((Array.isArray(currentSources.documents) &&
                            currentSources.documents.length > 0) ||
                            (Array.isArray(currentSources.web) &&
                                currentSources.web.length > 0));

                    const aiMessage = await createMessage(conversationId, {
                        content: get().streamingMessage,

                        sender: "assistant",
                    });

                    const messageWithSources = {
                        ...aiMessage.data,
                        ...(hasValidSources ? { sources: currentSources } : {}),
                    };

                    set((state) => ({
                        messages: [...state.messages, messageWithSources],

                        isStreaming: false,
                        streamingMessage: "",
                        streamingStatus: null,
                        streamingSources: null,
                    }));
                },
                (title) => {
                    useConversationStore
                        .getState()
                        .setConversationTitle(conversationId, title);
                },
                (status) => {
                    set({ streamingStatus: status });
                },
                (error) => {
                    set({
                        isLoading: false,
                        isStreaming: false,
                        streamingMessage: "",
                        streamingStatus: null,
                        streamingSources: null,
                        error: error.message,
                    });
                },
                (retrievedDocs) => {
                    if (!retrievedDocs || retrievedDocs.length === 0) {
                        return;
                    }

                    set((state) => {
                        const currentDocs =
                            state.streamingSources?.documents || [];
                        const currentWeb = state.streamingSources?.web || [];
                        const mergedDocs = Array.from(
                            new Set([...currentDocs, ...retrievedDocs]),
                        );

                        return {
                            streamingSources: {
                                documents: mergedDocs,
                                web: currentWeb,
                            },
                        };
                    });
                },
                (webSources) => {
                    if (!webSources || webSources.length === 0) {
                        return;
                    }

                    set((state) => {
                        const currentDocs =
                            state.streamingSources?.documents || [];
                        const currentWeb = state.streamingSources?.web || [];
                        const mergedWeb = Array.from(
                            new Set([...currentWeb, ...webSources]),
                        );

                        return {
                            streamingSources: {
                                documents: currentDocs,
                                web: mergedWeb,
                            },
                        };
                    });
                },
            );
        } catch (error) {
            set({
                isLoading: false,
                isStreaming: false,
                streamingStatus: null,
                streamingSources: null,
                error: error.message,
            });
        }
    },
}));
