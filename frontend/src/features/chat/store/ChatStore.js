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

    isStreaming: false,

    isLoading: false,

    error: null,

    clearMessages: () => {
        set({
            messages: [],
            streamingMessage: "",
            streamingStatus: null,
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

                    const aiMessage = await createMessage(conversationId, {
                        content: get().streamingMessage,

                        sender: "assistant",
                    });                 

                    set((state) => ({
                        messages: [...state.messages, aiMessage.data],

                        isStreaming: false,
                        streamingMessage: "",
                        streamingStatus: null,
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
                        error: error.message,
                    });
                },
            );
        } catch (error) {
            set({
                isLoading: false,
                streamingStatus: null,
                error: error.message,
            });
        }
    },
}));
