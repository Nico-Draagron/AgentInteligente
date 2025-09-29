import { useState } from "react";
import Header from "@/components/layout/Header";
import ChatInterface from "@/components/chat/ChatInterface";
import DataPanel from "@/components/data/DataPanel";



import logo from "@/assets/logo.jpg";

const ONSightsDashboard = () => {
  const [sidebarOpen, setSidebarOpen] = useState(false);

  return (
    <div className="h-screen bg-gradient-surface">
      <Header onToggleSidebar={() => setSidebarOpen(!sidebarOpen)} />
      <div className="flex h-[calc(100vh-4rem)]">
        {/* Main Chat Area */}
        <div className="flex-1">
          <ChatInterface />
        </div>
        {/* Data Panel - Hidden on mobile, visible on large screens */}
        <div className={`w-80 ${sidebarOpen ? 'block' : 'hidden'} lg:block`}>
          <DataPanel />
        </div>
      </div>
    </div>
  );
};

export default ONSightsDashboard;