import { useEffect, useMemo, useState } from "react";

import Sidebar from "@/components/layout/Sidebar";

import {
    ChatHeader,
    MessageInput,
    MessageList,
} from "@/features/chat";

import {
    UploadedFilesDrawer,
    UploadPanel,
    useDocumentStore,
} from "@/features/documents";

import { useChat } from "@/features/chat/hooks/useChat";
import { useConversationStore } from "@/features/conversations/store/ConversationStore";

export default function ChatPage() {
    const [sidebarOpen, setSidebarOpen] = useState(false);
    const [uploadConversationId, setUploadConversationId] =
        useState(null);
    const [filesDrawerConversationId, setFilesDrawerConversationId] =
        useState(null);

    const {
        activeConversationId,
        messages,
        streamingMessage,
        isStreaming,
        handleSendMessage,
    } = useChat();

    const { conversations } = useConversationStore();
    const {
        documents,
        loadDocuments,
        deleteDocument,
        isLoading,
        deletingDocumentIds,
        error: documentError,
    } = useDocumentStore();

    const activeConversation = conversations.find(
        (conversation) =>
            String(conversation.id) ===
            String(activeConversationId),
    );

    const headerTitle =
        activeConversation?.title?.trim() || "Synapse";
    const hasActiveConversation = Boolean(activeConversationId);
    const conversationDocuments = useMemo(() => {
        if (!activeConversationId) {
            return [];
        }

        return documents.filter(
            (document) =>
                String(document.conversationId) ===
                String(activeConversationId),
        );
    }, [activeConversationId, documents]);
    const fileCount = conversationDocuments.length;
    const isUploadOpen =
        hasActiveConversation &&
        String(uploadConversationId) ===
            String(activeConversationId);
    const isFilesDrawerOpen =
        hasActiveConversation &&
        String(filesDrawerConversationId) ===
            String(activeConversationId);

    useEffect(() => {
        if (!activeConversationId) {
            return;
        }

        loadDocuments(activeConversationId).catch(() => {});
    }, [activeConversationId, loadDocuments]);

    const handleToggleUploadPanel = () => {
        if (!hasActiveConversation) {
            return;
        }

        setUploadConversationId((currentConversationId) =>
            String(currentConversationId) ===
            String(activeConversationId)
                ? null
                : activeConversationId,
        );
        setFilesDrawerConversationId(null);
    };

    const handleOpenFilesDrawer = () => {
        if (!hasActiveConversation) {
            return;
        }

        setFilesDrawerConversationId(activeConversationId);
        setUploadConversationId(null);
    };

    const handleAddMoreFiles = () => {
        setFilesDrawerConversationId(null);
        setUploadConversationId(activeConversationId);
    };

    const handleRemoveDocument = async (document) => {
        if (!activeConversationId) {
            return;
        }

        await deleteDocument(activeConversationId, document.id).catch(
            () => {},
        );
    };

    return (
        <div className="relative flex h-[var(--app-height)] min-h-[var(--app-height)] overflow-hidden bg-[var(--color-background)] text-[var(--color-foreground)]">
            {sidebarOpen && (
                <div
                    className="fixed inset-0 z-40 bg-black/50 backdrop-blur-sm transition-opacity md:hidden"
                    onClick={() => setSidebarOpen(false)}
                />
            )}

            <Sidebar
                isOpen={sidebarOpen}
                onClose={() => setSidebarOpen(false)}
            />

            <main className="flex min-h-0 min-w-0 flex-1 flex-col overflow-hidden bg-[var(--color-background)]">
                <ChatHeader
                    title={headerTitle}
                    onOpenSidebar={() => setSidebarOpen(true)}
                    hasActiveConversation={hasActiveConversation}
                    fileCount={fileCount}
                    isUploadOpen={isUploadOpen}
                    onOpenUploadPanel={handleToggleUploadPanel}
                    onOpenFilesDrawer={handleOpenFilesDrawer}
                />

                {isUploadOpen && activeConversationId && (
                    <UploadPanel
                        conversationId={activeConversationId}
                        onClose={() =>
                            setUploadConversationId(null)
                        }
                    />
                )}

                <div className="relative flex min-h-0 flex-1 flex-col overflow-hidden">
                    <MessageList
                        className="h-full"
                        conversationId={activeConversationId}
                        messages={messages}
                        streamingMessage={streamingMessage}
                        isStreaming={isStreaming}
                    />

                    <UploadedFilesDrawer
                        open={isFilesDrawerOpen}
                        files={conversationDocuments}
                        isLoading={isLoading}
                        error={documentError}
                        deletingDocumentIds={deletingDocumentIds}
                        onAddMore={handleAddMoreFiles}
                        onClose={() =>
                            setFilesDrawerConversationId(null)
                        }
                        onRemoveFile={handleRemoveDocument}
                    />
                </div>

                <MessageInput
                    onSendMessage={handleSendMessage}
                    isStreaming={isStreaming}
                    contextFiles={conversationDocuments}
                    removingFileIds={deletingDocumentIds}
                    onOpenFileContext={handleOpenFilesDrawer}
                    onRemoveContextFile={handleRemoveDocument}
                />
            </main>
        </div>
    );
}
