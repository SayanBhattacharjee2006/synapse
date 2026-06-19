import { Button } from "@/components/ui";

import { cn } from "@/lib/utils";

import { Files, Paperclip, Upload } from "lucide-react";

export default function UploadButton({
    active = false,
    fileCount = 0,
    label,
    mode = "upload",
    onClick,
    className,
    ...props
}) {
    const Icon = mode === "view" ? Files : active ? Upload : Paperclip;
    const buttonLabel =
        label ||
        (mode === "view" ? "View Uploaded Files" : "Upload Files");

    return (
        <Button
            type="button"
            variant={active ? "secondary" : "primary"}
            size="sm"
            onClick={onClick}
            className={cn("gap-2 text-xs sm:text-sm", className)}
            {...props}
        >
            <Icon size={16} strokeWidth={3} />
            <span className="hidden uppercase sm:inline">
                {buttonLabel}
            </span>
            {fileCount > 0 && (
                <span className="ml-1 inline-flex min-w-6 items-center justify-center border-2 border-black bg-black px-1.5 py-0.5 text-xs font-black text-[var(--color-primary)] dark:border-white">
                    {fileCount}
                </span>
            )}
        </Button>
    );
}
