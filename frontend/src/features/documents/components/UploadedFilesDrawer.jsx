import { Button } from "@/components/ui";
import { UploadFileCard } from "@/features/documents";

import { cn } from "@/lib/utils";

import {
    AlertTriangle,
    Files,
    Loader2,
    Plus,
    X,
} from "lucide-react";

export default function UploadedFilesDrawer({
    files = [],
    isLoading = false,
    error,
    deletingDocumentIds = [],
    open = false,
    onAddMore,
    onClose,
    onRemoveFile,
}) {
    return (
        <aside
            className={cn(
                "absolute bottom-0 right-0 top-0 z-30 flex w-full max-w-[22rem] flex-col border-l-2 border-[var(--color-primary)] bg-[var(--color-background)] shadow-[-6px_0_0_var(--color-primary)] transition-transform duration-200 sm:max-w-[24rem]",
                open
                    ? "translate-x-0"
                    : "pointer-events-none translate-x-[calc(100%+1rem)]",
            )}
            aria-hidden={!open}
        >
            <div className="flex items-start justify-between gap-4 border-b-2 border-[var(--color-primary)] p-5">
                <div>
                    <div className="flex items-center gap-2">
                        <Files size={18} strokeWidth={3} />
                        <h2 className="font-[var(--font-display)] text-lg font-black uppercase tracking-wide">
                            Uploaded Files
                        </h2>
                    </div>
                    <p className="mt-2 text-[10px] font-black uppercase text-[var(--color-primary)]">
                        Files in this conversation
                    </p>
                </div>

                <Button
                    type="button"
                    variant="secondary"
                    size="icon"
                    onClick={onClose}
                    className="h-9 w-9 shrink-0"
                    aria-label="Close uploaded files"
                >
                    <X size={16} strokeWidth={3} />
                </Button>
            </div>

            <div className="min-h-0 flex-1 space-y-4 overflow-y-auto p-5">
                {error && (
                    <div className="flex items-start gap-2 border-2 border-[var(--color-danger)] p-3 text-xs font-black uppercase text-[var(--color-danger)]">
                        <AlertTriangle
                            size={16}
                            strokeWidth={3}
                            className="mt-0.5 shrink-0"
                        />
                        <span>{error}</span>
                    </div>
                )}

                {isLoading ? (
                    <div className="flex items-center justify-center gap-2 border-2 border-dashed border-[var(--color-border)] p-6 text-sm font-black uppercase text-[var(--color-muted)]">
                        <Loader2
                            size={18}
                            strokeWidth={3}
                            className="animate-spin"
                        />
                        Loading files
                    </div>
                ) : files.length > 0 ? (
                    files.map((file) => (
                        <UploadFileCard
                            key={file.id}
                            document={file}
                            isRemoving={deletingDocumentIds.includes(
                                String(file.id),
                            )}
                            onRemove={onRemoveFile}
                        />
                    ))
                ) : (
                    <div className="border-2 border-dashed border-[var(--color-border)] p-6 text-center">
                        <p className="text-sm font-black uppercase text-[var(--color-muted)]">
                            No uploaded files yet
                        </p>
                    </div>
                )}
            </div>

            <div className="border-t-2 border-[var(--color-primary)] p-5">
                <Button
                    type="button"
                    variant="primary"
                    className="w-full gap-2"
                    onClick={onAddMore}
                >
                    <Plus size={16} strokeWidth={3} />
                    Add More Files
                </Button>
            </div>
        </aside>
    );
}
