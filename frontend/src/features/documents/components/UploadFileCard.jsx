import { Button } from "@/components/ui";
import { UploadProgress } from "@/features/documents";

import { cn } from "@/lib/utils";
import {
    formatFileSize,
    getDocumentExtension,
    getDocumentFileName,
    getDocumentFileSize,
    getDocumentStatus,
    getDocumentStatusLabel,
} from "@/features/documents/utils/documentUtils";

import {
    AlertTriangle,
    CheckCircle2,
    Clock3,
    File,
    FileText,
    Image,
    Loader2,
    Table,
    Trash2,
} from "lucide-react";

const imageExtensions = new Set(["PNG", "JPG", "JPEG", "WEBP"]);
const tableExtensions = new Set(["CSV", "XLSX"]);
const textExtensions = new Set(["PDF", "DOCX", "TXT"]);

const statusClassName = {
    ready: "bg-[var(--color-surface)] text-[var(--color-foreground)]",
    uploading:
        "bg-[var(--color-primary)] text-black",
    pending:
        "bg-[var(--color-primary)] text-black",
    processing:
        "bg-[var(--color-primary)] text-black",
    completed: "bg-emerald-500 text-black",
    indexed: "bg-emerald-500 text-black",
    failed: "bg-[var(--color-danger)] text-white",
};

const renderFileIcon = (extension) => {
    if (imageExtensions.has(extension)) {
        return <Image size={20} strokeWidth={3} />;
    }

    if (tableExtensions.has(extension)) {
        return <Table size={20} strokeWidth={3} />;
    }

    if (textExtensions.has(extension)) {
        return <FileText size={20} strokeWidth={3} />;
    }

    return <File size={20} strokeWidth={3} />;
};

const renderStatusIcon = (status, isUploading) => {
    const className = isUploading ? "animate-spin" : "";

    if (status === "failed") {
        return (
            <AlertTriangle
                size={12}
                strokeWidth={3}
                className={className}
            />
        );
    }

    if (status === "completed" || status === "indexed") {
        return (
            <CheckCircle2
                size={12}
                strokeWidth={3}
                className={className}
            />
        );
    }

    if (
        status === "uploading" ||
        status === "pending" ||
        status === "processing"
    ) {
        return (
            <Loader2
                size={12}
                strokeWidth={3}
                className={className}
            />
        );
    }

    return (
        <Clock3
            size={12}
            strokeWidth={3}
            className={className}
        />
    );
};

export default function UploadFileCard({
    document,
    isRemoving = false,
    onRemove,
    variant = "drawer",
}) {
    const fileName = getDocumentFileName(document);
    const extension = getDocumentExtension(document);
    const fileSize = formatFileSize(getDocumentFileSize(document));
    const status = getDocumentStatus(document);
    const statusLabel = getDocumentStatusLabel(document);
    const isUploading =
        status === "uploading" ||
        status === "pending" ||
        status === "processing";
    const isDrawer = variant === "drawer";

    return (
        <article
            className={cn(
                "border-2 border-[var(--color-primary)] bg-[var(--color-background)] p-3 shadow-[4px_4px_0px_var(--color-primary)]",
                isDrawer ? "space-y-3" : "space-y-2",
            )}
        >
            <div className="flex items-start gap-3">
                <div className="flex h-10 w-10 shrink-0 items-center justify-center border-2 border-[var(--color-border)] bg-[var(--color-primary)] text-black">
                    {renderFileIcon(extension)}
                </div>

                <div className="min-w-0 flex-1">
                    <p className="truncate text-sm font-black uppercase text-[var(--color-foreground)]">
                        {fileName}
                    </p>

                    <div className="mt-1 flex flex-wrap items-center gap-2 text-[10px] font-black uppercase">
                        <span className="border border-[var(--color-border)] bg-[var(--color-primary)] px-1.5 py-0.5 text-black">
                            {extension}
                        </span>
                        <span className="text-[var(--color-muted)]">
                            {fileSize}
                        </span>
                        <span
                            className={cn(
                                "inline-flex items-center gap-1 border border-[var(--color-border)] px-1.5 py-0.5",
                                statusClassName[status],
                            )}
                        >
                            {renderStatusIcon(status, isUploading)}
                            {statusLabel}
                        </span>
                    </div>
                </div>
            </div>

            {variant === "queue" && (
                <UploadProgress document={document} />
            )}

            {document?.errorMessage && (
                <p className="text-xs font-bold uppercase text-[var(--color-danger)]">
                    {document.errorMessage}
                </p>
            )}

            {isDrawer && onRemove && (
                <Button
                    type="button"
                    variant="secondary"
                    size="sm"
                    disabled={isRemoving}
                    onClick={() => onRemove(document)}
                    className="h-10 w-full gap-2 border-[var(--color-danger)] text-[var(--color-danger)] shadow-[3px_3px_0px_var(--color-danger)] hover:bg-[var(--color-danger)] hover:text-white"
                >
                    {isRemoving ? (
                        <Loader2
                            size={14}
                            strokeWidth={3}
                            className="animate-spin"
                        />
                    ) : (
                        <Trash2 size={14} strokeWidth={3} />
                    )}
                    {isRemoving ? "Removing" : "Remove"}
                </Button>
            )}
        </article>
    );
}
