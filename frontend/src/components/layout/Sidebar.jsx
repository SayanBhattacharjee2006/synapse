import { useEffect } from "react";
import { useNavigate } from "react-router-dom";

import { Button, Card } from "@/components/ui";

import { cn } from "@/lib/utils";

import { ConversationList } from "@/features/conversations";

import { useConversationStore } from "@/features/conversations/store/ConversationStore";

import { Moon, Plus, Sun, X , MessageSquare} from "lucide-react";

import { useThemeStore } from "@/stores/themeStore";

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
  } = useConversationStore();

  const { theme, toggleTheme } = useThemeStore();

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
        />
      </div>

      {/* Footer */}
      <Card className="p-2">
        <div className="flex items-center justify-between">
          <span className="text-base font-bold uppercase">
            {theme === "dark" ? "Dark Mode" : "Light Mode"}
          </span>

          <Button
            variant="secondary"
            size="icon"
            className="h-10 w-10"
            onClick={toggleTheme}
            aria-label={
              theme === "dark"
                ? "Switch to light mode"
                : "Switch to dark mode"
            }
            aria-pressed={theme === "dark"}
          >
            {theme === "dark" ? (
              <Sun size={16} />
            ) : (
              <Moon size={16} />
            )}
          </Button>
        </div>
      </Card>
    </aside>
  );
}
