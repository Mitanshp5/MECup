import { Bell, MessageCircle, User, Wifi, WifiOff } from "lucide-react";
import { useEffect, useState } from "react";

interface HeaderProps {
  currentPage: string;
  onChatbotToggle: () => void;
  chatbotOpen: boolean;
}

const pageTitles: Record<string, string> = {
  dashboard: "Dashboard",
  automatic: "Automatic Mode",
  manual: "Manual Mode",
  maintenance: "Maintenance Mode",
  settings: "Settings",
  scans: "Past Scans",
  users: "User Management",
  heartbeat: "System Heartbeat",
};

const Header = ({ currentPage, onChatbotToggle, chatbotOpen }: HeaderProps) => {
  const [plcStatus, setPlcStatus] = useState<{ connected: boolean; error?: string }>({
    connected: false,
  });

  useEffect(() => {
    const interval = setInterval(async () => {
      try {
        const res = await fetch("http://localhost:5001/plc/status");
        const data = await res.json();
        console.log("PLC Status Poll:", data);
        setPlcStatus(data);
      } catch {
        console.warn("PLC Status Poll Failed");
        setPlcStatus({ connected: false, error: "No backend" });
      }
    }, 2000);
    return () => clearInterval(interval);
  }, []);

  return (
    <header className="h-16 bg-card border-b border-border flex items-center justify-between px-6">
      <div className="flex items-center gap-4">
        <h2 className="text-lg font-semibold text-foreground">
          {pageTitles[currentPage] || "Dashboard"}
        </h2>
        <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-secondary/50 border border-border">
          {plcStatus.connected ? (
            <>
              <Wifi className="w-4 h-4 text-success" />
              <span className="text-xs font-medium text-success">PLC Connected</span>
            </>
          ) : (
            <>
              <WifiOff className="w-4 h-4 text-destructive" />
              <span className="text-xs font-medium text-destructive">Disconnected</span>
            </>
          )}
        </div>
      </div>

      <div className="flex items-center gap-3">
        {/* System time */}
        <div className="font-mono text-sm text-muted-foreground px-3 py-1.5 bg-secondary/30 rounded border border-border">
          <SystemTime />
        </div>

        {/* Notifications */}
        <button className="relative p-2 rounded-md hover:bg-secondary transition-colors">
          <Bell className="w-5 h-5 text-muted-foreground" />
          <span className="absolute top-1 right-1 w-2 h-2 bg-destructive rounded-full" />
        </button>

        {/* Chatbot toggle */}
        <button
          onClick={onChatbotToggle}
          className={`p-2 rounded-md transition-all ${chatbotOpen
            ? "bg-primary/15 text-primary border border-primary/30"
            : "hover:bg-secondary text-muted-foreground"
            }`}
        >
          <MessageCircle className="w-5 h-5" />
        </button>

        {/* User menu */}
        <button className="flex items-center gap-2 px-3 py-1.5 rounded-md hover:bg-secondary transition-colors">
          <div className="w-8 h-8 rounded-full bg-primary/20 flex items-center justify-center">
            <User className="w-4 h-4 text-primary" />
          </div>
          <span className="text-sm font-medium text-foreground">Operator</span>
        </button>
      </div>
    </header>
  );
};

const SystemTime = () => {
  const [time, setTime] = useState(new Date());

  useState(() => {
    const interval = setInterval(() => setTime(new Date()), 1000);
    return () => clearInterval(interval);
  });

  return <span>{time.toLocaleTimeString("en-US", { hour12: false })}</span>;
};

export default Header;
