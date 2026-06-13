import { create } from "zustand";

import {
    createConversations,
    deleteConversations,
    getConversations,
    updateConversations,
} from "@/features/conversations/services/conversationService";

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

    clearConversations: () => {
        set({
            conversations: [],
            activeConversationId: null,
            isLoading: false,
            error: null,
        });
    },

    setConversationTitle: (conversationId, title) => {
        const nextTitle = title?.trim();

        if (!nextTitle) {
            return;
        }

        set((state) => ({
            conversations: state.conversations.map((conversation) =>
                String(conversation.id) === String(conversationId)
                    ? {
                          ...conversation,
                          title: nextTitle,
                          slug: nextTitle.toLowerCase().replace(/\s+/g, "-"),
                      }
                    : conversation,
            ),
        }));
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
                    String(conversation.id) === String(conversationId)
                        ? response.data
                        : conversation,
                ),

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

    deleteConversation: async (conversationId) => {
        try {
            set({
                isLoading: true,
                error: null,
            });

            await deleteConversations(conversationId);

            set((state) => ({
                conversations: state.conversations.filter(
                    (conversation) =>
                        String(conversation.id) !== String(conversationId),
                ),

                activeConversationId:
                    String(state.activeConversationId) === String(conversationId)
                        ? null
                        : state.activeConversationId,

                isLoading: false,
                error: null,
            }));

            return true;
        } catch (error) {
            set({
                isLoading: false,
                error: error.message,
            });
        }
    },
}));
