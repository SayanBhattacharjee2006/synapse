import { DOCUMENT_STATUS_LABELS } from "@/features/documents/constants/documentConstants";

const FALLBACK_FILE_NAME = "uploaded-file";

export const createLocalDocumentId = (prefix = "document") => {
    if (typeof crypto !== "undefined" && crypto.randomUUID) {
        return crypto.randomUUID();
    }

    return `${prefix}-${Date.now()}-${Math.random()
        .toString(36)
        .slice(2)}`;
};

export const getDocumentFileName = (document) =>
    document?.filename || document?.name || FALLBACK_FILE_NAME;

export const getDocumentFileSize = (document) =>
    document?.file_size ?? document?.size ?? 0;

export const getDocumentExtension = (document) => {
    const fileName = getDocumentFileName(document);
    const extension = fileName.split(".").pop();

    if (!extension || extension === fileName) {
        return "FILE";
    }

    return extension.toUpperCase();
};

export const formatFileSize = (bytes = 0) => {
    if (!bytes) {
        return "0 KB";
    }

    if (bytes < 1024 * 1024) {
        return `${Math.max(1, Math.round(bytes / 1024))} KB`;
    }

    return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
};

export const getDocumentStatus = (document) =>
    document?.uiStatus ||
    document?.processing_status ||
    document?.processingStatus ||
    "ready";

export const getDocumentStatusLabel = (document) => {
    const status = getDocumentStatus(document);

    return DOCUMENT_STATUS_LABELS[status] || status;
};

export const normalizeDocument = ({
    document = {},
    file,
    conversationId,
    status,
}) => ({
    ...document,
    id: document.id || createLocalDocumentId("document"),
    filename:
        document.filename || file?.name || FALLBACK_FILE_NAME,
    mime_type:
        document.mime_type ||
        file?.type ||
        "application/octet-stream",
    file_size: document.file_size ?? file?.size ?? 0,
    processing_status:
        document.processing_status ||
        document.processingStatus ||
        status ||
        "processing",
    conversationId: String(conversationId),
    uploadedAt:
        document.created_at ||
        document.createdAt ||
        new Date().toISOString(),
});
