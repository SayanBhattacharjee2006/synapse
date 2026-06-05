import { Card, Button } from "@/components/ui";

import { Moon, PanelLeft } from "lucide-react";

export default function ChatHeader({
  title = "New Conversation",
}) {
  return (
    <Card className="flex items-center justify-between border-x-0 border-t-0 p-4">
      
      <div className="flex items-center gap-3">
        
        {/* Mobile Sidebar Toggle */}
        <Button
          variant="secondary"
          size="icon"
          className="md:hidden"
        >
          <PanelLeft size={18} />
        </Button>

        <div>
          <h1 className="text-lg font-black uppercase">
            {title}
          </h1>

          <p className="text-xs uppercase text-[var(--color-muted)]">
            Synapse AI Assistant
          </p>
        </div>
      </div>

      {/* Actions */}
      <div className="flex items-center gap-2">
        <Button
          variant="secondary"
          size="icon"
        >
          <Moon size={18} />
        </Button>
      </div>
    </Card>
  );
}