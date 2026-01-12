import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { Activity, Camera, Lightbulb, Move, Cpu, Thermometer, Zap, Wifi } from "lucide-react";

interface SystemComponent {
  id: string;
  name: string;
  icon: React.ElementType;
  status: "ok" | "warning" | "error";
  value: string;
  unit: string;
  trend: number[];
}

const HeartbeatPage = () => {
  const [components, setComponents] = useState<SystemComponent[]>([
    { id: "camera", name: "Camera System", icon: Camera, status: "ok", value: "60", unit: "FPS", trend: [58, 60, 59, 60, 61, 60, 60, 59] },
    { id: "lights", name: "LED Lights", icon: Lightbulb, status: "ok", value: "100", unit: "%", trend: [100, 100, 100, 100, 100, 100, 100, 100] },
    { id: "gantry-x", name: "Gantry X-Axis", icon: Move, status: "ok", value: "0.02", unit: "mm/s", trend: [0, 0.01, 0.02, 0.01, 0.02, 0.01, 0.02, 0.02] },
    { id: "gantry-y", name: "Gantry Y-Axis", icon: Move, status: "ok", value: "0.01", unit: "mm/s", trend: [0, 0.01, 0.01, 0.01, 0.01, 0.01, 0.01, 0.01] },
    { id: "gantry-z", name: "Gantry Z-Axis", icon: Move, status: "warning", value: "0.15", unit: "mm/s", trend: [0.1, 0.12, 0.14, 0.13, 0.15, 0.14, 0.15, 0.15] },
    { id: "plc", name: "PLC Controller", icon: Cpu, status: "ok", value: "12", unit: "ms", trend: [10, 11, 12, 11, 12, 12, 12, 12] },
    { id: "temp", name: "System Temperature", icon: Thermometer, status: "ok", value: "42", unit: "°C", trend: [38, 39, 40, 41, 42, 41, 42, 42] },
    { id: "network", name: "Network Latency", icon: Wifi, status: "ok", value: "2.1", unit: "ms", trend: [2.0, 2.1, 2.0, 2.1, 2.2, 2.1, 2.1, 2.1] },
  ]);

  const [uptime, setUptime] = useState("23:45:12");

  // Simulate live updates
  useEffect(() => {
    const interval = setInterval(() => {
      setComponents(prev => prev.map(comp => ({
        ...comp,
        trend: [...comp.trend.slice(1), comp.trend[comp.trend.length - 1] + (Math.random() - 0.5) * 0.1]
      })));
    }, 2000);
    return () => clearInterval(interval);
  }, []);

  const okCount = components.filter(c => c.status === "ok").length;
  const warningCount = components.filter(c => c.status === "warning").length;
  const errorCount = components.filter(c => c.status === "error").length;

  return (
    <div className="h-full grid grid-cols-12 gap-6">
      {/* Main Status Grid */}
      <div className="col-span-8 space-y-6">
        {/* Overview */}
        <div className="grid grid-cols-4 gap-4">
          <StatusOverviewCard label="System Status" value="OPERATIONAL" status="ok" />
          <StatusOverviewCard label="Components OK" value={okCount.toString()} status="ok" />
          <StatusOverviewCard label="Warnings" value={warningCount.toString()} status={warningCount > 0 ? "warning" : "ok"} />
          <StatusOverviewCard label="Errors" value={errorCount.toString()} status={errorCount > 0 ? "error" : "ok"} />
        </div>

        {/* Component Grid */}
        <div className="grid grid-cols-2 gap-4">
          {components.map((component) => (
            <ComponentCard key={component.id} component={component} />
          ))}
        </div>
      </div>

      {/* Side Panel */}
      <div className="col-span-4 space-y-4">
        {/* Uptime */}
        <div className="industrial-panel p-4 text-center">
          <h3 className="text-sm font-medium text-muted-foreground mb-2">SYSTEM UPTIME</h3>
          <p className="text-3xl font-mono font-bold text-primary">{uptime}</p>
          <p className="text-xs text-muted-foreground mt-1">Since last restart</p>
        </div>

        {/* System Resources */}
        <div className="industrial-panel p-4">
          <h3 className="text-sm font-medium text-muted-foreground mb-4">SYSTEM RESOURCES</h3>
          <div className="space-y-4">
            <ResourceBar label="CPU Usage" value={45} />
            <ResourceBar label="Memory" value={62} />
            <ResourceBar label="Disk Space" value={34} />
            <ResourceBar label="Network I/O" value={28} />
          </div>
        </div>

        {/* Recent Events */}
        <div className="industrial-panel p-4 flex-1">
          <h3 className="text-sm font-medium text-muted-foreground mb-4">RECENT EVENTS</h3>
          <div className="space-y-3">
            {[
              { time: "10:45:23", event: "Scan completed successfully", type: "success" },
              { time: "10:42:15", event: "Z-Axis vibration detected", type: "warning" },
              { time: "10:38:47", event: "Camera calibration OK", type: "info" },
              { time: "10:32:11", event: "System health check passed", type: "success" },
              { time: "10:15:33", event: "Operator login: John Smith", type: "info" },
            ].map((event, i) => (
              <div key={i} className="flex items-start gap-3 text-sm">
                <span className="font-mono text-xs text-muted-foreground w-16 flex-shrink-0">{event.time}</span>
                <span className={`w-1.5 h-1.5 rounded-full mt-1.5 flex-shrink-0 ${
                  event.type === "success" ? "bg-success" :
                  event.type === "warning" ? "bg-warning" : "bg-primary"
                }`} />
                <span className="text-foreground text-xs">{event.event}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

const StatusOverviewCard = ({ label, value, status }: { label: string; value: string; status: "ok" | "warning" | "error" }) => (
  <div className={`industrial-panel p-4 border ${
    status === "ok" ? "border-success/30" :
    status === "warning" ? "border-warning/30" : "border-destructive/30"
  }`}>
    <p className="text-xs text-muted-foreground mb-1">{label}</p>
    <p className={`text-xl font-bold font-mono ${
      status === "ok" ? "text-success" :
      status === "warning" ? "text-warning" : "text-destructive"
    }`}>{value}</p>
  </div>
);

const ComponentCard = ({ component }: { component: SystemComponent }) => {
  const Icon = component.icon;
  const maxTrend = Math.max(...component.trend);
  const minTrend = Math.min(...component.trend);
  const range = maxTrend - minTrend || 1;

  return (
    <motion.div
      className={`industrial-panel p-4 border ${
        component.status === "ok" ? "border-border hover:border-success/30" :
        component.status === "warning" ? "border-warning/30" : "border-destructive/30"
      } transition-colors`}
    >
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-3">
          <div className={`w-10 h-10 rounded-md flex items-center justify-center ${
            component.status === "ok" ? "bg-success/10" :
            component.status === "warning" ? "bg-warning/10" : "bg-destructive/10"
          }`}>
            <Icon className={`w-5 h-5 ${
              component.status === "ok" ? "text-success" :
              component.status === "warning" ? "text-warning" : "text-destructive"
            }`} />
          </div>
          <div>
            <h4 className="font-medium text-foreground text-sm">{component.name}</h4>
            <span className={`status-indicator inline-block ${
              component.status === "ok" ? "status-ok" :
              component.status === "warning" ? "status-warning" : "status-error"
            }`} />
          </div>
        </div>
        <div className="text-right">
          <p className="font-mono text-lg text-foreground">{component.value}</p>
          <p className="text-xs text-muted-foreground">{component.unit}</p>
        </div>
      </div>

      {/* Mini chart */}
      <div className="h-8 flex items-end gap-1">
        {component.trend.map((value, i) => (
          <div
            key={i}
            className={`flex-1 rounded-t transition-all ${
              component.status === "ok" ? "bg-success/40" :
              component.status === "warning" ? "bg-warning/40" : "bg-destructive/40"
            }`}
            style={{ height: `${((value - minTrend) / range) * 100}%`, minHeight: "4px" }}
          />
        ))}
      </div>
    </motion.div>
  );
};

const ResourceBar = ({ label, value }: { label: string; value: number }) => (
  <div>
    <div className="flex justify-between text-sm mb-1">
      <span className="text-muted-foreground">{label}</span>
      <span className="font-mono text-foreground">{value}%</span>
    </div>
    <div className="h-2 bg-secondary rounded-full overflow-hidden">
      <motion.div
        className={`h-full rounded-full ${
          value < 60 ? "bg-success" :
          value < 80 ? "bg-warning" : "bg-destructive"
        }`}
        initial={{ width: 0 }}
        animate={{ width: `${value}%` }}
        transition={{ duration: 0.5 }}
      />
    </div>
  </div>
);

export default HeartbeatPage;
