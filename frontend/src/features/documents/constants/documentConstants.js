export const ACCEPTED_FILE_TYPES = [
    "PDF",
    "DOCX",
    "TXT",
    "CSV",
    "XLSX",
    "PNG",
    "JPG",
    "JPEG",
    "WEBP",
];

export const ACCEPTED_FILE_EXTENSIONS = [
    ".pdf",
    ".docx",
    ".txt",
    ".md",
    ".doc",
];

export const ACCEPTED_FILE_MIME_TYPES = {
    "application/pdf": [".pdf"],
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": [
        ".docx",
    ],
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": [
        ".xlsx",
    ],
    "text/markdown": [".md"],
    "text/x-markdown": [".md"],
    "text/plain": [".txt", ".md"],
};

export const MAX_FILE_SIZE_MB = 20;
export const MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024;

export const DOCUMENT_STATUS_LABELS = {
    ready: "Ready",
    uploading: "Uploading",
    pending: "Processing",
    processing: "Processing",
    completed: "Indexed",
    indexed: "Indexed",
    failed: "Failed",
};
