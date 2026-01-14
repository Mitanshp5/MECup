import { Canvas } from "@react-three/fiber";
import { OrbitControls, PerspectiveCamera } from "@react-three/drei";
import { motion } from "framer-motion";
import { Play, Settings, Activity, History } from "lucide-react";

interface DashboardProps {
  onPageChange: (page: string) => void;
}

const MachineModel = () => {
  return (
    <group>
      {/* Base platform */}
      <mesh position={[0, -1.5, 0]}>
        <boxGeometry args={[4, 0.2, 3]} />
        <meshStandardMaterial color="#1a1f2e" metalness={0.2} roughness={0.7} />
      </mesh>

      {/* Gantry rails */}
      <mesh position={[-1.8, -0.5, 0]}>
        <boxGeometry args={[0.1, 2, 0.1]} />
        <meshStandardMaterial color="#2a3441" metalness={0.3} roughness={0.6} />
      </mesh>
      <mesh position={[1.8, -0.5, 0]}>
        <boxGeometry args={[0.1, 2, 0.1]} />
        <meshStandardMaterial color="#2a3441" metalness={0.3} roughness={0.6} />
      </mesh>

      {/* Gantry crossbar */}
      <mesh position={[0, 0.5, 0]}>
        <boxGeometry args={[3.8, 0.15, 0.15]} />
        <meshStandardMaterial color="#3a4555" metalness={0.3} roughness={0.6} />
      </mesh>

      {/* Camera head */}
      <group position={[0, 0.5, 0]}>
        <mesh position={[0, -0.3, 0.2]}>
          <boxGeometry args={[0.4, 0.5, 0.3]} />
          <meshStandardMaterial color="#0d1117" metalness={0.3} roughness={0.7} />
        </mesh>
        {/* Camera lens */}
        <mesh position={[0, -0.4, 0.4]} rotation={[Math.PI / 2, 0, 0]}>
          <cylinderGeometry args={[0.08, 0.1, 0.15, 16]} />
          <meshStandardMaterial color="#00d4ff" emissive="#00d4ff" emissiveIntensity={0.5} />
        </mesh>
        {/* LED ring */}
        <mesh position={[0, -0.4, 0.36]}>
          <torusGeometry args={[0.15, 0.02, 8, 24]} />
          <meshStandardMaterial color="#00ff88" emissive="#00ff88" emissiveIntensity={0.8} />
        </mesh>
      </group>

      {/* Control box */}
      <mesh position={[2.3, -0.8, 1]}>
        <boxGeometry args={[0.5, 1.2, 0.4]} />
        <meshStandardMaterial color="#1a1f2e" metalness={0.2} roughness={0.7} />
      </mesh>

      {/* Status lights on control box */}
      <mesh position={[2.05, -0.4, 1.05]}>
        <sphereGeometry args={[0.04, 16, 16]} />
        <meshStandardMaterial color="#00ff88" emissive="#00ff88" emissiveIntensity={1} />
      </mesh>
      <mesh position={[2.05, -0.55, 1.05]}>
        <sphereGeometry args={[0.04, 16, 16]} />
        <meshStandardMaterial color="#00ff88" emissive="#00ff88" emissiveIntensity={1} />
      </mesh>
      <mesh position={[2.05, -0.7, 1.05]}>
        <sphereGeometry args={[0.04, 16, 16]} />
        <meshStandardMaterial color="#00d4ff" emissive="#00d4ff" emissiveIntensity={1} />
      </mesh>
    </group>
  );
};

const StatCard = ({ title, value, subtitle, icon: Icon, onClick }: {
  title: string;
  value: string;
  subtitle: string;
  icon: React.ElementType;
  onClick?: () => void;
}) => (
  <motion.div
    whileHover={{ scale: 1.02, y: -2 }}
    whileTap={{ scale: 0.98 }}
    onClick={onClick}
    className="industrial-panel p-4 cursor-pointer transition-all hover:border-primary/50"
  >
    <div className="flex items-start justify-between mb-3">
      <div className="w-10 h-10 rounded-md bg-primary/10 flex items-center justify-center border border-primary/20">
        <Icon className="w-5 h-5 text-primary" />
      </div>
      <span className="status-indicator status-ok" />
    </div>
    <h3 className="text-2xl font-bold text-foreground font-mono">{value}</h3>
    <p className="text-sm font-medium text-foreground mt-1">{title}</p>
    <p className="text-xs text-muted-foreground">{subtitle}</p>
  </motion.div>
);

const Dashboard = ({ onPageChange }: DashboardProps) => {
  return (
    <div className="h-full grid grid-cols-12 gap-6">
      {/* Left: 3D Model */}
      <div className="col-span-8 industrial-panel overflow-hidden relative">
        <div className="absolute top-4 left-4 z-10">
          <h3 className="text-sm font-medium text-muted-foreground mb-1">MACHINE VIEW</h3>
          <p className="text-xs text-muted-foreground font-mono">CON-SOL-E 5.0 Gantry System</p>
        </div>

        <Canvas className="w-full h-full">
          <PerspectiveCamera makeDefault position={[4, 2, 4]} />
          <OrbitControls
            enablePan={false}
            minDistance={3}
            maxDistance={10}
            autoRotate
            autoRotateSpeed={0.5}
          />
          <ambientLight intensity={0.3} />
          <directionalLight position={[5, 5, 5]} intensity={1} />
          <pointLight position={[-3, 3, -3]} intensity={0.5} color="#00d4ff" />
          <MachineModel />
        </Canvas>

        {/* System status overlay */}
        <div className="absolute bottom-4 left-4 right-4 flex gap-4">
          <div className="flex-1 bg-background/80 backdrop-blur-sm rounded-md p-3 border border-border">
            <div className="flex items-center justify-between">
              <span className="text-xs text-muted-foreground">System Status</span>
              <span className="flex items-center gap-1.5 text-xs font-medium text-success">
                <span className="status-indicator status-ok" />
                OPERATIONAL
              </span>
            </div>
          </div>
          <div className="flex-1 bg-background/80 backdrop-blur-sm rounded-md p-3 border border-border">
            <div className="flex items-center justify-between">
              <span className="text-xs text-muted-foreground">Gantry Position</span>
              <span className="text-xs font-mono text-foreground">X: 0.00 Y: 0.00 Z: 0.00</span>
            </div>
          </div>
        </div>
      </div>

      {/* Right: Quick stats and actions */}
      <div className="col-span-4 space-y-4">
        <div className="grid grid-cols-2 gap-4">
          <StatCard
            title="Scans Today"
            value="24"
            subtitle="3 defects found"
            icon={History}
            onClick={() => onPageChange("scans")}
          />
          <StatCard
            title="Uptime"
            value="99.2%"
            subtitle="Last 30 days"
            icon={Activity}
            onClick={() => onPageChange("heartbeat")}
          />
        </div>

        {/* Quick Actions */}
        <div className="industrial-panel p-4">
          <h3 className="text-sm font-medium text-muted-foreground mb-4">QUICK ACTIONS</h3>
          <div className="space-y-2">
            <button
              onClick={() => onPageChange("automatic")}
              className="w-full flex items-center gap-3 px-4 py-3 bg-primary/10 border border-primary/30 rounded-md text-primary hover:bg-primary/20 transition-colors"
            >
              <Play className="w-5 h-5" />
              <span className="font-medium">Start New Scan</span>
            </button>
            <button
              onClick={() => onPageChange("manual")}
              className="w-full flex items-center gap-3 px-4 py-3 bg-secondary border border-border rounded-md text-foreground hover:bg-secondary/80 transition-colors"
            >
              <Settings className="w-5 h-5" />
              <span className="font-medium">Manual Control</span>
            </button>
          </div>
        </div>

        {/* Recent Activity */}
        <div className="industrial-panel p-4 flex-1">
          <h3 className="text-sm font-medium text-muted-foreground mb-4">RECENT ACTIVITY</h3>
          <div className="space-y-3">
            {[
              { time: "10:45", event: "Scan completed", status: "success" },
              { time: "10:32", event: "Defect detected", status: "warning" },
              { time: "10:15", event: "System calibrated", status: "success" },
              { time: "09:58", event: "Operator login", status: "info" },
            ].map((item, i) => (
              <div key={i} className="flex items-center gap-3 text-sm">
                <span className="font-mono text-muted-foreground text-xs w-12">{item.time}</span>
                <span className={`status-indicator ${item.status === "success" ? "status-ok" :
                  item.status === "warning" ? "status-warning" : "bg-primary"
                  }`} />
                <span className="text-foreground">{item.event}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
