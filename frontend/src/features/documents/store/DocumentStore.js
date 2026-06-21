import { create } from "zustand";

import { 
    uploadDocument as uploadDocumentService,
    getDocuments as getDocumentsService,
    deleteDocument as deleteDocumentService
} from "@/features/documents/services/documentService";
import { normalizeDocument } from "@/features/documents/utils/documentUtils";

const getErrorMessage = (error, fallbackMessage) =>
    error?.response?.data?.detail || error?.message || fallbackMessage;

export const useDocumentStore = create((set) => ({
    documents: [],
    isUploading: false,
    uploadError: null, //for error related to the uploads of the files

    isLoading: false,
    deletingDocumentIds: [],
    error: null, // for delete and get errors

    uploadDocument: async (conversationId, file) => {
        try {
            set({ isUploading: true, uploadError: null });

            const response = await uploadDocumentService(conversationId, file);
            const document = normalizeDocument({
                document: response.data,
                file,
                conversationId,
            });

            set((state) => ({
                documents: [
                    document,
                    ...state.documents.filter(
                        (existingDocument) =>
                            String(existingDocument.id) !== String(document.id),
                    ),
                ],
                isUploading: false,
                uploadError: null,
            }));

            return document;
        } catch (error) {
            const message = getErrorMessage(error, "Upload failed");

            set({
                isUploading: false,
                uploadError: message,
            });

            throw new Error(message, { cause: error });
        }
    },

    loadDocuments: async (conversationId, options = {}) => {
        if (!conversationId) {
            return [];
        }

        const { silent = false } = options;

        try {
            set((state) => ({
                isLoading: silent ? state.isLoading : true,
                error: null,
            }));

            const response = await getDocumentsService(conversationId);
            const documents = (response.data || []).map((document) =>
                normalizeDocument({
                    document,
                    conversationId,
                }),
            );

            set((state) => ({
                documents: [
                    ...documents,
                    ...state.documents.filter(
                        (document) =>
                            String(document.conversationId) !==
                            String(conversationId),
                    ),
                ],
                isLoading: silent ? state.isLoading : false,
                error: null,
            }));

            return documents;
        } catch (error) {
            const message = getErrorMessage(
                error,
                "Failed to load documents",
            );

            set((state) => ({
                isLoading: silent ? state.isLoading : false,
                error: message,
            }));

            throw new Error(message, { cause: error });
        }
    },

    deleteDocument: async (conversationId, documentId) => {
        if (!conversationId || !documentId) {
            return false;
        }

        const normalizedDocumentId = String(documentId);

        try {
            set((state) => ({
                error: null,
                deletingDocumentIds: [
                    ...new Set([
                        ...state.deletingDocumentIds,
                        normalizedDocumentId,
                    ]),
                ],
            }));

            await deleteDocumentService(conversationId, documentId);

            set((state) => ({
                documents: state.documents.filter(
                    (document) =>
                        String(document.id) !== normalizedDocumentId,
                ),
                deletingDocumentIds:
                    state.deletingDocumentIds.filter(
                        (id) => id !== normalizedDocumentId,
                    ),
                error: null,
            }));

            return true;
        } catch (error) {
            const message = getErrorMessage(
                error,
                "Failed to delete document",
            );

            set((state) => ({
                deletingDocumentIds:
                    state.deletingDocumentIds.filter(
                        (id) => id !== normalizedDocumentId,
                    ),
                error: message,
            }));

            throw new Error(message, { cause: error });
        }
    },

    removeDocument: (documentId) => {
        set((state) => ({
            documents: state.documents.filter(
                (document) => String(document.id) !== String(documentId),
            ),
        }));
    },

    clearUploadError: () => set({ uploadError: null }),
    clearDocumentError: () => set({ error: null }),

}));
