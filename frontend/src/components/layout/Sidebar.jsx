import { useEffect } from "react";
import { useNavigate } from "react-router-dom";

import { Button, Card } from "@/components/ui";

import { cn } from "@/lib/utils";

import { ConversationList } from "@/features/conversations";

import { useConversationStore } from "@/features/conversations/store/ConversationStore";
import { useAuthStore } from "@/features/auth";

import {
  LogOut,
  MessageSquare,
  Plus,
  Settings,
  UserRound,
  X,
} from "lucide-react";

export default function Sidebar({
  className,
  isOpen = false,
  onClose,
}) {
  const navigate = useNavigate();

  const {
    conversations,
    activeConversationId,
    loadConversations,
    setActiveConversationId,
    createConversation,
    updateConversation,
    deleteConversation,
    clearConversations,
  } = useConversationStore();

  const { user, logout } = useAuthStore();
  const profileName =
    user?.display_name || user?.email?.split("@")[0] || "User";
  const profileEmail = user?.email || "Signed in";
  const profileInitial =
    profileName?.trim()?.charAt(0)?.toUpperCase() || "U";

  useEffect(() => {
    loadConversations();
  }, [loadConversations]);

  const handleCreateConversation = async () => {
    const conversation = await createConversation();

    if (conversation) {
      navigate(`/chat/${conversation.id}`);
      onClose?.();
    }
  };

  const handleSelectConversation = (conversationId) => {
    setActiveConversationId(conversationId);
    navigate(`/chat/${conversationId}`);
    onClose?.();
  };

  const handleRenameConversation = async (conversationId, title) => {
    return updateConversation(conversationId, { title });
  };

  const handleDeleteConversation = async (conversationId) => {
    const wasActive =
      String(activeConversationId) === String(conversationId);
    const deleted = await deleteConversation(conversationId);

    if (deleted && wasActive) {
      navigate("/chat", { replace: true });
    }
  };

  const handleLogout = () => {
    logout();
    clearConversations();
    navigate("/login", { replace: true });
    onClose?.();
  };

  return (
    <aside
      className={cn(
        "fixed left-0 top-0 z-50 flex h-[var(--app-height)] max-h-[var(--app-height)] w-full flex-col gap-4 border-r-2 border-[var(--color-border)] bg-[var(--color-background)] p-4 pb-[calc(1rem_+_var(--safe-area-bottom))] transition-transform duration-200 md:static md:z-auto md:w-[320px] md:transition-none",
        isOpen
          ? "translate-x-0"
          : "-translate-x-full md:translate-x-0",
        className
      )}
    >
      
      {/* Logo */}
      <div className="flex items-center justify-between p-4 z-20">
        <h1 className="text-4xl font-[var(--font-display)] tracking-[-0.08em] font-black uppercase tracking-tight">
          Synapse
        </h1>

        <Button
          variant="secondary"
          size="icon"
          className="h-10 w-10 md:hidden"
          onClick={onClose}
          aria-label="Close sidebar"
        >
          <X size={16} />
        </Button>
      </div>

      {/* New Chat */}
      <Button
        className="w-full "
        variant="primary"
        onClick={handleCreateConversation}
      >
        <Plus size={18} />
        New Chat
      </Button>

      {/* Separator */}
      <div className="border-t-2 border-[var(--color-border)]"></div>
      <div className="flex items-center gap-2 px-1 text-[var(--color-muted)] uppercase">
        <MessageSquare size={18} className="inline-block mr-2" />
        <span>
          Conversations
        </span>
      </div>

      {/* Conversation List */}
      <div className="flex-1 overflow-y-auto">
        <ConversationList
          conversations={conversations}
          activeConversationId={activeConversationId}
          onSelectConversation={
            handleSelectConversation
          }
          onRenameConversation={
            handleRenameConversation
          }
          onDeleteConversation={
            handleDeleteConversation
          }
        />
      </div>

      {/* Footer */}
      <Card className="p-3">
        <div className="flex items-center gap-3">
          <div className="flex h-11 w-11 shrink-0 items-center justify-center border-2 border-[var(--color-border)] bg-[var(--color-primary)] text-lg font-black text-black">
            {profileInitial}
          </div>

          <div className="min-w-0 flex-1">
            <div className="flex items-center gap-1 text-sm font-black uppercase">
              <UserRound size={15} className="shrink-0" />
              <span className="truncate">
                {profileName}
              </span>
            </div>

            <p className="truncate text-xs uppercase text-[var(--color-muted)]">
              {profileEmail}
            </p>
          </div>

          <Button
            variant="secondary"
            size="icon"
            className="h-10 w-10 shrink-0"
            aria-label="Settings demo"
            title="Settings"
          >
            <Settings size={16} />
          </Button>
        </div>
      </Card>

      <Button
        variant="secondary"
        className="w-full gap-2"
        onClick={handleLogout}
      >
        <LogOut size={18} />
        Logout
      </Button>
    </aside>
  );
}
