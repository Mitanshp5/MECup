import { motion } from "framer-motion";
import { 
  Home, 
  Play, 
  Hand, 
  Wrench, 
  Settings, 
  History, 
  Users, 
  Activity,
  ChevronLeft,
  ChevronRight,
  MessageSquare
} from "lucide-react";

interface SidebarProps {
  collapsed: boolean;
  onCollapse: (collapsed: boolean) => void;
  currentPage: string;
  onPageChange: (page: string) => void;
}

const navItems = [
  { id: "dashboard", label: "Dashboard", icon: Home },
  { id: "automatic", label: "Automatic Mode", icon: Play },
  { id: "manual", label: "Manual Mode", icon: Hand },
  { id: "maintenance", label: "Maintenance", icon: Wrench },
  { id: "troubleshoot", label: "Troubleshoot Agent", icon: MessageSquare },
  { id: "settings", label: "Settings", icon: Settings },
  { id: "scans", label: "Past Scans", icon: History },
  { id: "users", label: "User Management", icon: Users },
  { id: "heartbeat", label: "System Heartbeat", icon: Activity },
];

const Sidebar = ({ collapsed, onCollapse, currentPage, onPageChange }: SidebarProps) => {
  return (
    <motion.aside
      initial={false}
      animate={{ width: collapsed ? 72 : 240 }}
      transition={{ duration: 0.2 }}
      className="h-full bg-sidebar border-r border-sidebar-border flex flex-col"
    >
      {/* Logo */}
      <div className="h-16 flex items-center px-4 border-b border-sidebar-border">
        <div className="flex items-center gap-3 overflow-hidden">
          <div className="w-10 h-10 rounded-md bg-primary/10 flex items-center justify-center flex-shrink-0 border border-primary/30">
            <span className="text-primary font-mono font-bold text-sm">CS</span>
          </div>
          {!collapsed && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="overflow-hidden"
            >
              <h1 className="font-semibold text-foreground text-sm whitespace-nowrap">CON-SOL-E</h1>
              <p className="text-xs text-muted-foreground font-mono">v5.0</p>
            </motion.div>
          )}
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 py-4 px-2 space-y-1 overflow-y-auto">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = currentPage === item.id;
          
          return (
            <button
              key={item.id}
              onClick={() => onPageChange(item.id)}
              className={`
                w-full flex items-center gap-3 px-3 py-2.5 rounded-md transition-all duration-200
                ${isActive 
                  ? "bg-primary/15 text-primary border border-primary/30" 
                  : "text-sidebar-foreground hover:bg-sidebar-accent hover:text-sidebar-accent-foreground border border-transparent"
                }
              `}
            >
              <Icon className={`w-5 h-5 flex-shrink-0 ${isActive ? "text-primary" : ""}`} />
              {!collapsed && (
                <motion.span
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  className="text-sm font-medium whitespace-nowrap"
                >
                  {item.label}
                </motion.span>
              )}
              {isActive && !collapsed && (
                <motion.div
                  layoutId="activeIndicator"
                  className="ml-auto w-1.5 h-1.5 rounded-full bg-primary"
                  style={{ boxShadow: "0 0 8px hsl(var(--primary))" }}
                />
              )}
            </button>
          );
        })}
      </nav>

      {/* Collapse toggle */}
      <div className="p-2 border-t border-sidebar-border">
        <button
          onClick={() => onCollapse(!collapsed)}
          className="w-full flex items-center justify-center py-2 text-muted-foreground hover:text-foreground transition-colors"
        >
          {collapsed ? <ChevronRight className="w-5 h-5" /> : <ChevronLeft className="w-5 h-5" />}
        </button>
      </div>
    </motion.aside>
  );
};

export default Sidebar;
