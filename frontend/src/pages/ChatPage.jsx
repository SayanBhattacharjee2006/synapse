import Sidebar from "../components/ui/Sidebar"
import MessageList from "../components/chat/MessageList"
import MessageInput from "../components/chat/MessageInput"

export default function ChatPage() {
  return (
    <div className="flex h-screen min-h-screen bg-[var(--color-bg-primary)] text-base">
      <Sidebar />
      <main className="flex min-w-0 flex-1 flex-col overflow-hidden">
        <MessageList />
        <MessageInput />
      </main>
    </div>
  )
}
