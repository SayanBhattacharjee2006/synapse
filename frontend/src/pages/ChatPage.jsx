import Sidebar from "../components/ui/Sidebar"
import MessageList from "../components/chat/MessageList"
import MessageInput from "../components/chat/MessageInput"
import RightSidebar from "../components/ui/RightSidebar"

export default function ChatPage() {
  return (
    <div className="flex h-screen min-h-screen overflow-hidden bg-[var(--color-bg-primary)] text-[var(--color-text-primary)]">
      <Sidebar />
      <main className="flex min-h-0 min-w-0 flex-1 flex-col overflow-hidden bg-[var(--color-bg-primary)]">
        <MessageList />
        <MessageInput />
      </main>
      <RightSidebar />
    </div>
  )
}
