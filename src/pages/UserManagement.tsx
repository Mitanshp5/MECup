import { useAuth } from "@/context/AuthContext";
import { useEffect, useState } from "react";
// import LoginModal from "@/components/LoginModal"; 
import { X, Lock, UserPlus, Edit2, Trash2, User, Search, Shield } from "lucide-react";

// Update interface to match API response more closely
interface SystemUser {
  id: number;
  username: string;
  role: "admin" | "operator" | "viewer";
  is_active: boolean;
  // Computed/Mapped fields
  status: "active" | "inactive";
}

const API_BASE_URL = "http://127.0.0.1:5001";

const AddUserModal = ({ onClose, onSuccess, token }: { onClose: () => void, onSuccess: () => void, token: string }) => {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [role, setRole] = useState("operator");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError("");

    try {
      const res = await fetch(`${API_BASE_URL}/users`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${token}`
        },
        body: JSON.stringify({ username, password, role })
      });

      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "Failed to create user");
      }
      onSuccess();
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
      <div className="bg-card w-full max-w-sm rounded-lg border border-border shadow-xl overflow-hidden">
        <div className="flex items-center justify-between p-4 border-b border-border bg-secondary/50">
          <h2 className="text-lg font-semibold text-foreground">Add New User</h2>
          <button onClick={onClose}><X className="w-5 h-5" /></button>
        </div>
        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          {error && <div className="text-red-500 text-sm">{error}</div>}
          <div className="space-y-2">
            <label className="text-sm">Username</label>
            <input className="w-full p-2 bg-background border rounded" value={username} onChange={e => setUsername(e.target.value)} required />
          </div>
          <div className="space-y-2">
            <label className="text-sm">Password</label>
            <input className="w-full p-2 bg-background border rounded" type="password" value={password} onChange={e => setPassword(e.target.value)} />
          </div>
          <div className="space-y-2">
            <label className="text-sm">Role</label>
            <select className="w-full p-2 bg-background border rounded" value={role} onChange={e => setRole(e.target.value)}>
              <option value="admin">Admin</option>
              <option value="operator">Operator</option>
              <option value="viewer">Viewer</option>
            </select>
          </div>
          <button disabled={loading} className="w-full py-2 bg-primary text-primary-foreground rounded">
            {loading ? "Creating..." : "Create User"}
          </button>
        </form>
      </div>
    </div>
  );
};

const UserManagement = () => {
  const { token, hasRole } = useAuth();
  const [users, setUsers] = useState<SystemUser[]>([]);
  const [searchTerm, setSearchTerm] = useState("");
  const [loading, setLoading] = useState(false);
  const [showAddModal, setShowAddModal] = useState(false);

  // Fetch Users
  const fetchUsers = async () => {
    if (!token) return;
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE_URL}/users`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        if (Array.isArray(data)) {
          const mappedUsers = data.map((u: any) => ({
            id: u.id,
            username: u.username || 'Unknown',
            role: u.role || 'viewer',
            is_active: !!u.is_active,
            status: u.is_active ? "active" : "inactive"
          }));
          setUsers(mappedUsers);
        } else {
          console.error("API returned non-array:", data);
          setUsers([]);
        }
      }
    } catch (err) {
      console.error("Failed to fetch users", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchUsers();
  }, [token]);

  // Guard against null/undefined API data
  const safeUsers = Array.isArray(users) ? users : [];

  const filteredUsers = safeUsers.filter(user =>
    user && user.username && user.username.toLowerCase().includes(searchTerm.toLowerCase())
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
            {hasRole(['admin']) && (
              <button
                onClick={() => setShowAddModal(true)}
                className="flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 transition-colors">
                <UserPlus className="w-4 h-4" />
                Add User
              </button>
            )}
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
            <div
              key={user.id}
              className="p-4 bg-secondary/30 rounded-md border border-border hover:border-primary/30 transition-colors"
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-4">
                  <div className="w-12 h-12 rounded-full bg-primary/10 flex items-center justify-center border border-primary/20">
                    <User className="w-6 h-6 text-primary" />
                  </div>
                  <div>
                    <h4 className="font-medium text-foreground">{user.username}</h4>
                    <p className="text-sm text-muted-foreground">ID: {user.id}</p>
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
                <span>Status: {user.status}</span>
              </div>
            </div>
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

      {/* Add User Modal */}
      {showAddModal && (
        <AddUserModal
          onClose={() => setShowAddModal(false)}
          onSuccess={() => {
            setShowAddModal(false);
            fetchUsers();
          }}
          token={token!}
        />
      )}
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
