import { useState } from "react";
import { ChevronDown, ExternalLink, FileText, Globe } from "lucide-react";

import {
    formatWebSourceLabel,
    getSafeUrl,
    hasSources,
    normalizeSources,
} from "@/features/chat/utils/sourceUtils";
import { cn } from "@/lib/utils";

export default function SourcesSection({ sources, className }) {
    const [isExpanded, setIsExpanded] = useState(false);

    if (!hasSources(sources)) {
        return null;
    }

    const { documents, web } = normalizeSources(sources);
    const hasDocuments = documents.length > 0;
    const hasWeb = web.length > 0;

    if (!hasDocuments && !hasWeb) {
        return null;
    }

    return (
        <div className={cn("mt-4 border-t-2 border-black/20 pt-3", className)}>
            <button
                type="button"
                onClick={() => setIsExpanded((prev) => !prev)}
                className="group flex cursor-pointer items-center gap-1.5 text-xs font-black uppercase tracking-wider text-black transition-colors hover:text-black/70 focus:outline-none"
                aria-expanded={isExpanded}
                aria-label={isExpanded ? "Collapse sources" : "Expand sources"}
            >
                <span>Sources</span>
                <ChevronDown
                    size={14}
                    strokeWidth={3}
                    className={cn(
                        "transition-transform duration-200",
                        isExpanded && "rotate-180",
                    )}
                />
            </button>

            {isExpanded && (
                <div className="mt-3 flex flex-col gap-3">
                    {hasDocuments && (
                        <div className="flex flex-col gap-1.5">
                            <span className="text-[11px] font-black uppercase tracking-wider text-[var(--color-muted)]">
                                Documents
                            </span>
                            <div className="flex flex-col gap-1.5">
                                {documents.map((docName, index) => (
                                    <div
                                        key={`doc-${docName}-${index}`}
                                        className="flex items-center gap-2 border-2 border-black bg-white px-3 py-1.5 text-xs font-bold text-black shadow-[2px_2px_0px_black]"
                                    >
                                        <FileText
                                            size={14}
                                            strokeWidth={2.5}
                                            className="shrink-0 text-black"
                                        />
                                        <span
                                            className="truncate"
                                            title={docName}
                                        >
                                            {docName}
                                        </span>
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}

                    {hasWeb && (
                        <div className="flex flex-col gap-1.5">
                            <span className="text-[11px] font-black uppercase tracking-wider text-[var(--color-muted)]">
                                Web
                            </span>
                            <div className="flex flex-col gap-1.5">
                                {web.map((url, index) => {
                                    const safeUrl = getSafeUrl(url);
                                    const label = formatWebSourceLabel(url);

                                    return (
                                        <a
                                            key={`web-${url}-${index}`}
                                            href={safeUrl}
                                            target="_blank"
                                            rel="noopener noreferrer"
                                            title={url}
                                            className="flex items-center justify-between gap-2 border-2 border-black bg-white px-3 py-1.5 text-xs font-bold text-black shadow-[2px_2px_0px_black] transition-all duration-150 hover:translate-x-[1px] hover:translate-y-[1px] hover:bg-[var(--color-primary)] hover:shadow-none"
                                        >
                                            <div className="flex min-w-0 items-center gap-2 truncate">
                                                <Globe
                                                    size={14}
                                                    strokeWidth={2.5}
                                                    className="shrink-0 text-black"
                                                />
                                                <span className="truncate">
                                                    {label}
                                                </span>
                                            </div>
                                            <ExternalLink
                                                size={12}
                                                strokeWidth={2.5}
                                                className="shrink-0 text-black"
                                            />
                                        </a>
                                    );
                                })}
                            </div>
                        </div>
                    )}
                </div>
            )}
        </div>
    );
}
