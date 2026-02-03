import { Bell, MessageCircle, User, Wifi, WifiOff, LogOut, LogIn } from "lucide-react";
import { useEffect, useState } from "react";
import { useAuth } from "@/context/AuthContext";

interface HeaderProps {
  currentPage: string;
  onChatbotToggle: () => void;
  chatbotOpen: boolean;
  onLoginClick: () => void;
}
// ... (pageTitles map remains same, I should omit it or include it from context if I can't partial edit properly. I will include the full start of component)

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

const Header = ({ currentPage, onChatbotToggle, chatbotOpen, onLoginClick }: HeaderProps) => {
  const { user, logout, isAuthenticated } = useAuth();
  const [plcStatus, setPlcStatus] = useState<{ connected: boolean; error?: string }>({
    connected: false,
  });

  useEffect(() => {
    // ... (keep useEffect for polling)
    const interval = setInterval(async () => {
      try {
        const res = await fetch("http://localhost:5001/plc/status");
        const data = await res.json();
        if (data.connected && data.error === null) {
          setPlcStatus({ connected: true });
        } else {
          setPlcStatus({ connected: false });
        }
      } catch (err) {
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

        {/* User menu / Login */}
        {isAuthenticated && user ? (
          <div className="flex items-center gap-2">
            <div className="flex items-center gap-2 px-3 py-1.5 rounded-md bg-secondary/50 transition-colors">
              <div className="w-8 h-8 rounded-full bg-primary/20 flex items-center justify-center">
                <User className="w-4 h-4 text-primary" />
              </div>
              <div className="flex flex-col items-start leading-none">
                <span className="text-sm font-medium text-foreground">{user.username}</span>
                <span className="text-[10px] text-muted-foreground uppercase">{user.role}</span>
              </div>
            </div>
            <button
              onClick={logout}
              className="p-2 text-muted-foreground hover:text-destructive transition-colors"
              title="Logout"
            >
              <LogOut className="w-5 h-5" />
            </button>
          </div>
        ) : (
          <button
            onClick={onLoginClick}
            className="flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 transition-colors shadow-sm"
          >
            <LogIn className="w-4 h-4" />
            <span className="font-medium text-sm">Login</span>
          </button>
        )}
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
