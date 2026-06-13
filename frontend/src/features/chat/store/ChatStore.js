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

    isStreaming: false,

    isLoading: false,

    error: null,

    clearMessages: () => {
        set({
            messages: [],
            streamingMessage: "",
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
                    const aiMessage = await createMessage(conversationId, {
                        content: get().streamingMessage,

                        sender: "assistant",
                    });                 

                    set((state) => ({
                        messages: [...state.messages, aiMessage.data],

                        isStreaming: false,
                        streamingMessage: "",
                    }));
                },
                (title) => {
                    useConversationStore
                        .getState()
                        .setConversationTitle(conversationId, title);
                },
                (error) => {
                    set({
                        isStreaming: false,
                        error: error.message,
                    });
                },
            );
        } catch (error) {
            set({
                isLoading: false,
                error: error.message,
            });
        }
    },
}));
