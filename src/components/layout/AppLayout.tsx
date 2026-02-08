import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Outlet, useLocation } from "react-router-dom";
import Sidebar from "./Sidebar";
import Header from "./Header";
import Chatbot from "../chatbot/Chatbot";

import LoginModal from "../LoginModal";

const AppLayout = () => {
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [chatbotOpen, setChatbotOpen] = useState(false);
  const [loginModalOpen, setLoginModalOpen] = useState(false);
  const location = useLocation();

  return (
    <div className="flex h-screen bg-background overflow-hidden">
      <Sidebar
        collapsed={sidebarCollapsed}
        onCollapse={setSidebarCollapsed}
      />

      <div className="flex-1 flex flex-col overflow-hidden">
        <Header
          onChatbotToggle={() => setChatbotOpen(!chatbotOpen)}
          chatbotOpen={chatbotOpen}
          onLoginClick={() => setLoginModalOpen(true)}
        />

        <main className="flex-1 overflow-auto p-6 grid-overlay">
          <AnimatePresence mode="wait">
            <motion.div
              key={location.pathname}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              transition={{ duration: 0.2 }}
              className="h-full"
            >
              <Outlet />
            </motion.div>
          </AnimatePresence>
        </main>
      </div>

      <Chatbot isOpen={chatbotOpen} onClose={() => setChatbotOpen(false)} />
      <LoginModal isOpen={loginModalOpen} onClose={() => setLoginModalOpen(false)} />
    </div>
  );
};

export default AppLayout;
