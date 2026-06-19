import { useDropzone } from "react-dropzone";

import { Button } from "@/components/ui";

import {
    ACCEPTED_FILE_MIME_TYPES,
    ACCEPTED_FILE_TYPES,
    MAX_FILE_SIZE_BYTES,
    MAX_FILE_SIZE_MB,
} from "@/features/documents/constants/documentConstants";
import { cn } from "@/lib/utils";

import { CloudUpload, FolderOpen } from "lucide-react";

export default function UploadDropzone({
    onFilesSelected,
    disabled = false,
    isUploading = false,
}) {
    const {
        getRootProps,
        getInputProps,
        isDragActive,
        isDragReject,
        open,
    } = useDropzone({
        accept: ACCEPTED_FILE_MIME_TYPES,
        maxSize: MAX_FILE_SIZE_BYTES,
        multiple: true,
        disabled,
        noClick: true,
        noKeyboard: true,
        onDrop: (acceptedFiles, fileRejections) =>
            onFilesSelected?.(acceptedFiles, fileRejections),
    });

    return (
        <div
            {...getRootProps()}
            className={cn(
                "border-2 border-dashed border-[var(--color-primary)] bg-[var(--color-surface)] p-5 text-center transition-all sm:p-8",
                isDragActive &&
                    "translate-x-[2px] translate-y-[2px] bg-[var(--color-primary)] text-black shadow-none",
                isDragReject && "border-[var(--color-danger)]",
                disabled && "cursor-not-allowed opacity-60",
            )}
        >
            <input {...getInputProps()} />

            <div className="flex flex-col items-center gap-3">
                <CloudUpload size={34} strokeWidth={3} />

                <div>
                    <p className="font-[var(--font-display)] text-sm font-black uppercase tracking-wide">
                        Drop files here
                    </p>

                    <p className="mt-1 text-[11px] font-bold uppercase text-[var(--color-muted)]">
                        or click to browse
                    </p>
                </div>

                <div className="flex flex-wrap justify-center gap-2">
                    {ACCEPTED_FILE_TYPES.map((fileType) => (
                        <span
                            key={fileType}
                            className="border-2 border-[var(--color-border)] bg-[var(--color-primary)] px-2 py-1 text-[10px] font-black uppercase text-black"
                        >
                            {fileType}
                        </span>
                    ))}
                </div>

                <p className="text-[10px] font-bold uppercase text-[var(--color-muted)]">
                    Max {MAX_FILE_SIZE_MB} MB per file
                </p>
            </div>

            <Button
                type="button"
                variant="primary"
                size="sm"
                onClick={open}
                disabled={disabled}
                className="mt-5 w-full gap-2"
            >
                <FolderOpen size={16} strokeWidth={3} />
                {isUploading ? "Uploading" : "Browse Files"}
            </Button>
        </div>
    );
}
