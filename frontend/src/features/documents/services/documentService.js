import api from "@/library/api";

export const uploadDocument = async (conversationId, file) => {
    const formData = new FormData();

    formData.append("file", file);

    const response = await api.post(
        `/conversations/${conversationId}/documents`,
        formData,
        {
            headers: {
                "Content-Type": "multipart/form-data",
            },
        },
    );

    return response;
};

export const getDocuments = async (conversationId) => {
    const response = await api.get(`/conversations/${conversationId}/documents`);
    return response;
};

export const deleteDocument = async (conversationId, documentId) => {
    const response = await api.delete(
        `/conversations/${conversationId}/documents/${documentId}`,
    );
    return response;
};
