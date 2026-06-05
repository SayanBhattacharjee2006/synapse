import { Sidebar } from "@/components/layout";

export default function ChatLayout({ children }) {
  return (
    <div className="flex h-screen bg-[var(--color-background)] text-[var(--color-foreground)]">
      
      {/* Desktop Sidebar */}
      <div className="hidden md:block">
        <Sidebar />
      </div>

      {/* Main Content */}
      <main className="flex-1 overflow-hidden">
        {children}
      </main>
    </div>
  );
}