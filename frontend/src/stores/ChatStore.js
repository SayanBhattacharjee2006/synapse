import { create } from "zustand";
import {
    getConversations,
    createConversations,
    updateConversations,
    deleteConversations,
    createMessage,
    getMessages,
    streamChat
} from "../services/api";

export const useChatStore = create((set,get) => ({
    conversations: [],
    activeConversationId: null,
    messages: [],
    isStreaming: false,
    streamingMessage: "",
    isLoading: false,
    error: null,

    loadConversations: async () => {
        try {
            set({
                isLoading: true,
                error: null,
            });

            const fetchedConversations = await getConversations();

            set({
                conversations: fetchedConversations.data,
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
                conversations: state.conversations.filter((convo) => convo.id !== conversationId),
                activeConversationId: state.activeConversationId === conversationId ? null : state.activeConversationId,
                isLoading: false,
                error: null,
            }))
        } catch (error) {
            set({
                isLoading: false,
                error: error.message,
            });
        }
    },

    updateConversations: async (conversationId, data) => {
        try {
            set({
                isLoading: true,
                error: null,
            });

            const response = await updateConversations(conversationId, data);

            set((state) => ({
                conversations: state.conversations.map((convo) => convo.id === conversationId ? response.data : convo),
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
                activeConversationId: conversationId
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
                isLoading: false,
                isStreaming: true,
                messages: [...state.messages, createdMessage.data],
            }))

            await streamChat(
                conversationId,
                data,
                (token) => set((state) => ({
                    streamingMessage: state.streamingMessage + token,
                })),
                async ()=>{

                    const aimessage = await createMessage(conversationId, {content: get().streamingMessage, sender: "assistant"});

                    set((state) => ({
                        isStreaming: false,
                        messages: [...state.messages, aimessage.data],
                        streamingMessage: ""
                    }))
                },
                (err) =>{
                    set({
                        isStreaming: false,
                        error: err.message,
                    });
                }
            )
        
        } catch (error) {
            set({
                isLoading: false,
                error: error.message,
            });
        }
    }
}));
