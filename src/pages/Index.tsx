import { useState } from "react";
import AppLayout from "@/components/layout/AppLayout";
import Dashboard from "./Dashboard";
import AutomaticMode from "./AutomaticMode";
import ManualMode from "./ManualMode";
import MaintenanceMode from "./MaintenanceMode";
import SettingsPage from "./SettingsPage";
import PastScans from "./PastScans";
import UserManagement from "./UserManagement";
import HeartbeatPage from "./HeartbeatPage";

const Index = () => {
  const [currentPage, setCurrentPage] = useState("dashboard");

  const renderPage = () => {
    switch (currentPage) {
      case "dashboard":
        return <Dashboard onPageChange={setCurrentPage} />;
      case "automatic":
        return <AutomaticMode />;
      case "manual":
        return <ManualMode />;
      case "maintenance":
        return <MaintenanceMode />;
      case "settings":
        return <SettingsPage />;
      case "scans":
        return <PastScans />;
      case "users":
        return <UserManagement />;
      case "heartbeat":
        return <HeartbeatPage />;
      default:
        return <Dashboard onPageChange={setCurrentPage} />;
    }
  };

  return (
    <AppLayout currentPage={currentPage} onPageChange={setCurrentPage}>
      {renderPage()}
    </AppLayout>
  );
};

export default Index;
