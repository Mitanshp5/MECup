import { useState } from "react";
import { motion } from "framer-motion";
import { UserPlus, Edit2, Trash2, Shield, User, Search, MoreVertical } from "lucide-react";

interface SystemUser {
  id: string;
  name: string;
  email: string;
  role: "admin" | "operator" | "viewer";
  status: "active" | "inactive";
  lastLogin: string;
}

const mockUsers: SystemUser[] = [
  { id: "1", name: "Admin", email: "admin@example.com", role: "admin", status: "active", lastLogin: "2025-01-12 10:45" },
  { id: "2", name: "Operator", email: "operator@example.com", role: "operator", status: "active", lastLogin: "2025-01-12 09:32" },
  { id: "3", name: "Viewer", email: "viewer@example.com", role: "viewer", status: "active", lastLogin: "2025-01-11 16:22" },
];

const UserManagement = () => {
  const [users] = useState<SystemUser[]>(mockUsers);
  const [searchTerm, setSearchTerm] = useState("");

  const filteredUsers = users.filter(user =>
    user.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    user.email.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const getRoleBadge = (role: string) => {
    const styles = {
      admin: "bg-primary/10 text-primary border-primary/30",
      operator: "bg-success/10 text-success border-success/30",
      viewer: "bg-muted text-muted-foreground border-border",
    };
    return styles[role as keyof typeof styles] || styles.viewer;
  };

  return (
    <div className="h-full grid grid-cols-12 gap-6">
      {/* User List */}
      <div className="col-span-8 industrial-panel flex flex-col">
        <div className="p-4 border-b border-border">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-foreground">Users</h3>
            <button className="flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 transition-colors">
              <UserPlus className="w-4 h-4" />
              Add User
            </button>
          </div>

          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
            <input
              type="text"
              placeholder="Search users..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-10 pr-4 py-2 bg-secondary border border-border rounded-md text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-primary"
            />
          </div>
        </div>

        <div className="flex-1 overflow-y-auto p-4 space-y-3">
          {filteredUsers.map((user) => (
            <motion.div
              key={user.id}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className="p-4 bg-secondary/30 rounded-md border border-border hover:border-primary/30 transition-colors"
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-4">
                  <div className="w-12 h-12 rounded-full bg-primary/10 flex items-center justify-center border border-primary/20">
                    <User className="w-6 h-6 text-primary" />
                  </div>
                  <div>
                    <h4 className="font-medium text-foreground">{user.name}</h4>
                    <p className="text-sm text-muted-foreground">{user.email}</p>
                  </div>
                </div>

                <div className="flex items-center gap-4">
                  <span className={`px-3 py-1 text-xs font-medium rounded border capitalize ${getRoleBadge(user.role)}`}>
                    {user.role}
                  </span>
                  <span className={`flex items-center gap-1.5 text-xs ${user.status === "active" ? "text-success" : "text-muted-foreground"
                    }`}>
                    <span className={`w-2 h-2 rounded-full ${user.status === "active" ? "bg-success" : "bg-muted-foreground"
                      }`} />
                    {user.status}
                  </span>

                  <div className="flex items-center gap-1">
                    <button className="p-2 hover:bg-secondary rounded-md transition-colors">
                      <Edit2 className="w-4 h-4 text-muted-foreground" />
                    </button>
                    <button className="p-2 hover:bg-secondary rounded-md transition-colors">
                      <Trash2 className="w-4 h-4 text-destructive" />
                    </button>
                  </div>
                </div>
              </div>

              <div className="mt-3 pt-3 border-t border-border/50 flex items-center text-xs text-muted-foreground">
                <span>Last login: {user.lastLogin}</span>
              </div>
            </motion.div>
          ))}
        </div>
      </div>

      {/* Role Management */}
      <div className="col-span-4 space-y-4">
        <div className="industrial-panel p-4">
          <h3 className="text-sm font-medium text-muted-foreground mb-4">ROLES & PERMISSIONS</h3>
          <div className="space-y-3">
            <RoleCard
              role="Admin"
              description="Full system access, user management, settings"
              count={users.filter(u => u.role === "admin").length}
              color="primary"
            />
            <RoleCard
              role="Operator"
              description="Run scans, manual control, view reports"
              count={users.filter(u => u.role === "operator").length}
              color="success"
            />
            <RoleCard
              role="Viewer"
              description="View-only access to reports and history"
              count={users.filter(u => u.role === "viewer").length}
              color="muted"
            />
          </div>
        </div>

        <div className="industrial-panel p-4">
          <h3 className="text-sm font-medium text-muted-foreground mb-4">STATISTICS</h3>
          <div className="grid grid-cols-2 gap-3">
            <div className="p-3 bg-secondary/50 rounded-md text-center">
              <p className="text-2xl font-bold text-foreground font-mono">{users.length}</p>
              <p className="text-xs text-muted-foreground">Total Users</p>
            </div>
            <div className="p-3 bg-secondary/50 rounded-md text-center">
              <p className="text-2xl font-bold text-success font-mono">
                {users.filter(u => u.status === "active").length}
              </p>
              <p className="text-xs text-muted-foreground">Active</p>
            </div>
          </div>
        </div>

        <div className="industrial-panel p-4">
          <h3 className="text-sm font-medium text-muted-foreground mb-4">QUICK ACTIONS</h3>
          <div className="space-y-2">
            <button className="w-full flex items-center gap-3 px-4 py-3 bg-secondary border border-border rounded-md text-foreground hover:bg-secondary/80 transition-colors">
              <Shield className="w-5 h-5 text-primary" />
              <span className="text-sm">Manage Permissions</span>
            </button>
            <button className="w-full flex items-center gap-3 px-4 py-3 bg-secondary border border-border rounded-md text-foreground hover:bg-secondary/80 transition-colors">
              <UserPlus className="w-5 h-5" />
              <span className="text-sm">Bulk Import Users</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

const RoleCard = ({ role, description, count, color }: { role: string; description: string; count: number; color: string }) => (
  <div className="p-3 bg-secondary/50 rounded-md border border-border">
    <div className="flex items-center justify-between mb-1">
      <span className={`font-medium ${color === "primary" ? "text-primary" : color === "success" ? "text-success" : "text-muted-foreground"}`}>
        {role}
      </span>
      <span className="text-sm font-mono text-foreground">{count}</span>
    </div>
    <p className="text-xs text-muted-foreground">{description}</p>
  </div>
);

export default UserManagement;
