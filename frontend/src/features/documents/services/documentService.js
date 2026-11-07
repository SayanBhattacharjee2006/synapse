import api from "@/library/api";

export const uploadDocument = async (conversationId, file) => {
    // 1. Initiate presigned upload
    const initResponse = await api.post(
        `/conversations/${conversationId}/documents/upload-init`,
        {
            filename: file.name,
            content_type: file.type || "application/octet-stream",
            file_size: file.size,
        },
    );

    const { document_id, presigned_url, upload_url, required_headers } =
        initResponse.data;
    const targetUrl = presigned_url || upload_url;

    // 2. Direct upload to S3 via presigned PUT URL
    const headers = {
        ...(required_headers || {}),
    };
    if (file.type) {
        headers["Content-Type"] = file.type;
    }

    const s3Response = await fetch(targetUrl, {
        method: "PUT",
        headers,
        body: file,
    });

    if (!s3Response.ok) {
        throw new Error(`Direct upload failed with status ${s3Response.status}`);
    }

    // 3. Confirm upload
    const confirmResponse = await api.post(
        `/conversations/${conversationId}/documents/${document_id}/upload-confirm`,
    );

    return confirmResponse;
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
