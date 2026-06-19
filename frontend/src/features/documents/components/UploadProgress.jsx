import { getDocumentStatus } from "@/features/documents/utils/documentUtils";

const progressByStatus = {
    ready: 12,
    uploading: 42,
    pending: 68,
    processing: 76,
    completed: 100,
    indexed: 100,
    failed: 100,
};

export default function UploadProgress({ document }) {
    const status = getDocumentStatus(document);
    const progress = progressByStatus[status] || 20;
    const isFailed = status === "failed";

    return (
        <div className="h-2 w-full border border-[var(--color-border)] bg-[var(--color-background)]">
            <div
                className={
                    isFailed
                        ? "h-full bg-[var(--color-danger)]"
                        : "h-full bg-[var(--color-primary)] transition-all duration-300"
                }
                style={{ width: `${progress}%` }}
            />
        </div>
    );
}
