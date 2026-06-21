import { useMemo, useState } from "react";

import { Button } from "@/components/ui";
import { UploadDropzone, UploadFileCard } from "@/features/documents";

import { useDocumentStore } from "@/features/documents";
import {
    createLocalDocumentId,
    normalizeDocument,
} from "@/features/documents/utils/documentUtils";

import { AlertTriangle, X } from "lucide-react";

export default function UploadPanel({
    conversationId,
    onClose,
}) {
    const [queuedDocuments, setQueuedDocuments] =
        useState([]);
    const [rejectionMessage, setRejectionMessage] =
        useState("");

    const {
        documents,
        uploadDocument,
        isUploading,
        uploadError,
    } = useDocumentStore();

    const updateQueuedDocument = (queueId, patch) => {
        setQueuedDocuments((currentDocuments) =>
            currentDocuments.map((document) =>
                document.queueId === queueId
                    ? { ...document, ...patch }
                    : document,
            ),
        );
    };

    const syncedQueuedDocuments = useMemo(
        () =>
            queuedDocuments.map((queuedDocument) => {
                const syncedDocument = documents.find(
                    (document) =>
                        String(document.id) ===
                        String(queuedDocument.id),
                );

                if (!syncedDocument) {
                    return queuedDocument;
                }

                return {
                    ...queuedDocument,
                    ...syncedDocument,
                    queueId: queuedDocument.queueId,
                    file: queuedDocument.file,
                    uiStatus:
                        syncedDocument.processing_status ||
                        syncedDocument.processingStatus ||
                        queuedDocument.uiStatus,
                };
            }),
        [documents, queuedDocuments],
    );

    const handleFilesSelected = async (
        acceptedFiles,
        fileRejections = [],
    ) => {
        if (fileRejections.length > 0) {
            const rejectedNames = fileRejections
                .map(({ file, errors }) => {
                    const reason =
                        errors?.[0]?.message || "Unsupported file";

                    return `${file.name}: ${reason}`;
                })
                .join(" ");

            setRejectionMessage(rejectedNames);
        } else {
            setRejectionMessage("");
        }

        if (!acceptedFiles.length || !conversationId) {
            return;
        }

        const nextQueuedDocuments = acceptedFiles.map((file) => ({
            ...normalizeDocument({
                file,
                conversationId,
                status: "uploading",
            }),
            queueId: createLocalDocumentId("queue"),
            file,
            uiStatus: "uploading",
        }));

        setQueuedDocuments((currentDocuments) => [
            ...nextQueuedDocuments,
            ...currentDocuments,
        ]);

        for (const queuedDocument of nextQueuedDocuments) {
            try {
                const uploadedDocument = await uploadDocument(
                    conversationId,
                    queuedDocument.file,
                );

                updateQueuedDocument(queuedDocument.queueId, {
                    ...uploadedDocument,
                    uiStatus:
                        uploadedDocument.processing_status ||
                        "processing",
                });
            } catch (error) {
                updateQueuedDocument(queuedDocument.queueId, {
                    uiStatus: "failed",
                    errorMessage:
                        error?.message || "Upload failed",
                });
            }
        }
    };

    const statusMessage =
        rejectionMessage || uploadError;

    return (
        <section
            className="
                m-4
                border-2
                border-[var(--color-primary)]
                bg-[var(--color-background)]
                shadow-[6px_6px_0px_var(--color-primary)]
            "
        >
            <div className="flex items-center justify-between gap-4 border-b-2 border-[var(--color-primary)] px-4 py-3 sm:px-6">
                <div>
                    <p className="font-[var(--font-display)] text-sm font-black uppercase tracking-wide">
                        Upload files to this conversation
                    </p>
                    <p className="mt-1 text-[10px] font-bold uppercase text-[var(--color-muted)]">
                        Files are added to the current chat context.
                    </p>
                </div>

                <Button
                    type="button"
                    variant="secondary"
                    size="icon"
                    onClick={onClose}
                    className="h-9 w-9 shrink-0"
                    aria-label="Close upload panel"
                >
                    <X size={16} strokeWidth={3} />
                </Button>
            </div>

            <div className="space-y-4 p-4 sm:p-6">
                <UploadDropzone
                    onFilesSelected={handleFilesSelected}
                    disabled={isUploading}
                    isUploading={isUploading}
                />

                {statusMessage && (
                    <div className="flex items-start gap-2 border-2 border-[var(--color-danger)] bg-[var(--color-background)] p-3 text-xs font-black uppercase text-[var(--color-danger)]">
                        <AlertTriangle
                            size={16}
                            strokeWidth={3}
                            className="mt-0.5 shrink-0"
                        />
                        <span>{statusMessage}</span>
                    </div>
                )}

                {syncedQueuedDocuments.length > 0 && (
                    <div className="grid gap-3 md:grid-cols-2">
                        {syncedQueuedDocuments.map((document) => (
                            <UploadFileCard
                                key={document.queueId}
                                document={document}
                                variant="queue"
                            />
                        ))}
                    </div>
                )}
            </div>
        </section>
    );
}
