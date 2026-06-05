import { useEffect } from "react";

import { Button, Card } from "@/components/ui";

import { cn } from "@/lib/utils";

import { ConversationList } from "@/features/conversations";

import { useConversationStore } from "@/features/conversations/store/ConversationStore";

import { Moon, Plus, Sun, X , MessageSquare} from "lucide-react";

import { useThemeStore } from "@/stores/themeStore";

export default function Sidebar({
  className,
  onClose,
}) {
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
  }, []);

  const handleCreateConversation = async () => {
    const conversation = await createConversation();

    if (conversation) {
      onClose?.();
    }
  };

  const handleSelectConversation = (conversationId) => {
    setActiveConversationId(conversationId);
    onClose?.();
  };

  return (
    <aside
      className={cn(
        "fixed inset-y-0 left-0 z-50 flex h-screen w-[320px] flex-col gap-4 border-r-2 border-[var(--color-border)] bg-[var(--color-background)] p-4 transition-transform duration-200 md:static md:z-auto md:transition-none",
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
