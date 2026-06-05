import { Sidebar } from "@/components/layout";

export default function ChatLayout({
  children,
  sidebarOpen = false,
  onCloseSidebar,
}) {
  return (
    <div className="relative flex h-[var(--app-height)] overflow-hidden bg-[var(--color-background)] text-[var(--color-foreground)]">
      
      {/* Mobile Overlay */}
      {sidebarOpen && (
        <button
          type="button"
          aria-label="Close sidebar"
          className="fixed inset-0 z-40 bg-black/50 md:hidden"
          onClick={onCloseSidebar}
        />
      )}

      <Sidebar
        className={
          sidebarOpen
            ? "translate-x-0"
            : "-translate-x-full md:translate-x-0"
        }
        onClose={onCloseSidebar}
      />

      {/* Main Content */}
      <main className="flex-1 overflow-hidden">
        {children}
      </main>
    </div>
  );
}
