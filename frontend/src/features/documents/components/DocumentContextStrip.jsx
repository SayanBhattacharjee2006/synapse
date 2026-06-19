import { Button } from "@/components/ui";

import {
    formatFileSize,
    getDocumentExtension,
    getDocumentFileName,
    getDocumentFileSize,
} from "@/features/documents/utils/documentUtils";

import { Files, X } from "lucide-react";

export default function DocumentContextStrip({
    files = [],
    removingFileIds = [],
    onOpenFiles,
    onRemoveFile,
}) {
    if (files.length === 0) {
        return null;
    }

    const visibleFiles = files.slice(0, 3);
    const hiddenCount = files.length - visibleFiles.length;

    return (
        <div className="flex flex-wrap items-center gap-2 border-b-2 border-[var(--color-border)] pb-3 text-[10px] font-black uppercase sm:gap-3">
            <button
                type="button"
                onClick={onOpenFiles}
                className="inline-flex items-center gap-2 text-[var(--color-primary)]"
            >
                <Files size={14} strokeWidth={3} />
                {files.length}{" "}
                {files.length === 1 ? "file" : "files"} in
                context:
            </button>

            {visibleFiles.map((file) => (
                <ContextFileChip
                    key={file.id}
                    file={file}
                    isRemoving={removingFileIds.includes(
                        String(file.id),
                    )}
                    onRemoveFile={onRemoveFile}
                />
            ))}

            {hiddenCount > 0 && (
                <Button
                    type="button"
                    variant="secondary"
                    size="sm"
                    onClick={onOpenFiles}
                    className="h-8 px-3 text-[10px]"
                >
                    +{hiddenCount} more
                </Button>
            )}
        </div>
    );
}

function ContextFileChip({
    file,
    isRemoving = false,
    onRemoveFile,
}) {
    return (
        <span className="inline-flex max-w-full items-center gap-2 border-2 border-[var(--color-border)] bg-[var(--color-primary)] px-2 py-1 text-black">
            <span className="truncate">
                {getDocumentFileName(file)}
            </span>
            <span className="border border-black px-1">
                {getDocumentExtension(file)}
            </span>
            <span className="hidden sm:inline">
                {formatFileSize(getDocumentFileSize(file))}
            </span>
            {onRemoveFile && (
                <button
                    type="button"
                    disabled={isRemoving}
                    onClick={(event) => {
                        event.stopPropagation();
                        onRemoveFile(file);
                    }}
                    className="disabled:cursor-not-allowed disabled:opacity-50"
                    aria-label={`Remove ${getDocumentFileName(file)}`}
                >
                    <X size={12} strokeWidth={3} />
                </button>
            )}
        </span>
    );
}
