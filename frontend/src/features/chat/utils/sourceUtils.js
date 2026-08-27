/**
 * Safely parse document retrieval payload from SSE data.
 * Supports standard and fallback property names:
 * - retrieved_doc_names
 * - retreived_doc_names (common backend typo fallback)
 * - retrieved_document_names
 * - documents
 */
export const readRetrievalPayload = (data) => {
    try {
        const payload = typeof data === "string" ? JSON.parse(data) : data;

        if (!payload || typeof payload !== "object" || Array.isArray(payload)) {
            return [];
        }

        const raw =
            payload.retrieved_doc_names ??
            payload.retreived_doc_names ??
            payload.retrieved_document_names ??
            payload.documents ??
            payload.docs;

        if (Array.isArray(raw)) {
            return Array.from(
                new Set(
                    raw
                        .map((item) =>
                            typeof item === "string" ? item.trim() : "",
                        )
                        .filter((item) => item.length > 0),
                ),
            );
        }

        return [];
    } catch {
        return [];
    }
};

/**
 * Safely parse web sources payload from SSE data.
 * Supports standard and fallback property names:
 * - web_sources
 * - webSources
 * - sources
 * - web
 */
export const readWebPayload = (data) => {
    try {
        const payload = typeof data === "string" ? JSON.parse(data) : data;

        if (!payload || typeof payload !== "object" || Array.isArray(payload)) {
            return [];
        }

        const raw =
            payload.web_sources ??
            payload.webSources ??
            payload.sources ??
            payload.web;

        if (Array.isArray(raw)) {
            return Array.from(
                new Set(
                    raw
                        .map((item) =>
                            typeof item === "string" ? item.trim() : "",
                        )
                        .filter((item) => item.length > 0),
                ),
            );
        }

        return [];
    } catch {
        return [];
    }
};

/**
 * Normalize any source input into a unified structure:
 * { documents: string[], web: string[] }
 */
export const normalizeSources = (sources) => {
    if (!sources || typeof sources !== "object") {
        return { documents: [], web: [] };
    }

    const documents = Array.isArray(sources.documents)
        ? Array.from(
              new Set(
                  sources.documents
                      .map((item) =>
                          typeof item === "string" ? item.trim() : "",
                      )
                      .filter((item) => item.length > 0),
              ),
          )
        : [];

    const web = Array.isArray(sources.web)
        ? Array.from(
              new Set(
                  sources.web
                      .map((item) =>
                          typeof item === "string" ? item.trim() : "",
                      )
                      .filter((item) => item.length > 0),
              ),
          )
        : [];

    return { documents, web };
};

/**
 * Check if a sources object contains at least one document or web source.
 */
export const hasSources = (sources) => {
    if (!sources || typeof sources !== "object") {
        return false;
    }

    const docCount = Array.isArray(sources.documents)
        ? sources.documents.length
        : 0;
    const webCount = Array.isArray(sources.web) ? sources.web.length : 0;

    return docCount > 0 || webCount > 0;
};

/**
 * Format a URL into a clean, human-readable label.
 */
export const formatWebSourceLabel = (url) => {
    if (!url || typeof url !== "string") {
        return "";
    }

    try {
        const fullUrl = /^https?:\/\//i.test(url) ? url : `https://${url}`;
        const parsed = new URL(fullUrl);
        const host = parsed.hostname.replace(/^www\./, "");
        const path = parsed.pathname === "/" ? "" : parsed.pathname;

        if (path && path.length <= 25) {
            return `${host}${path}`;
        }

        return host || url;
    } catch {
        return url;
    }
};

/**
 * Ensure URL has a valid web protocol for opening safely in a new tab.
 */
export const getSafeUrl = (url) => {
    if (!url || typeof url !== "string") {
        return "#";
    }

    const trimmed = url.trim();
    if (/^https?:\/\//i.test(trimmed)) {
        return trimmed;
    }

    return `https://${trimmed}`;
};
