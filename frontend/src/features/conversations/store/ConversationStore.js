import { create } from "zustand";

import {
    getConversations,
    createConversations,
    updateConversations,
    deleteConversations,
} from "@/services/api";

export const useConversationStore = create((set) => ({
    conversations: [],
    activeConversationId: null,

    isLoading: false,
    error: null,

    setActiveConversationId: (conversationId) => {
        set({
            activeConversationId: conversationId,
        });
    },

    loadConversations: async () => {
        try {
            set({
                isLoading: true,
                error: null,
            });

            const response = await getConversations();

            set({
                conversations: response.data,
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

    createConversation: async () => {
        try {
            set({
                isLoading: true,
                error: null,
            });

            const response = await createConversations();

            set((state) => ({
                conversations: [response.data, ...state.conversations],

                activeConversationId: response.data.id,

                isLoading: false,
                error: null,
            }));

            return response.data;
        } catch (error) {
            set({
                isLoading: false,
                error: error.message,
            });
        }
    },

    updateConversation: async (conversationId, data) => {
        try {
            set({
                isLoading: true,
                error: null,
            });

            const response = await updateConversations(conversationId, data);

            set((state) => ({
                conversations: state.conversations.map((conversation) =>
                    conversation.id === conversationId
                        ? response.data
                        : conversation,
                ),

                isLoading: false,
                error: null,
            }));
        } catch (error) {
            set({
                isLoading: false,
                error: error.message,
            });
        }
    },

    deleteConversation: async (conversationId) => {
        try {
            set({
                isLoading: true,
                error: null,
            });

            await deleteConversations(conversationId);

            set((state) => ({
                conversations: state.conversations.filter(
                    (conversation) => conversation.id !== conversationId,
                ),

                activeConversationId:
                    state.activeConversationId === conversationId
                        ? null
                        : state.activeConversationId,

                isLoading: false,
                error: null,
            }));
        } catch (error) {
            set({
                isLoading: false,
                error: error.message,
            });
        }
    },
}));
