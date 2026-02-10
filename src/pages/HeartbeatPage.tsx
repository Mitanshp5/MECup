import { useState, useEffect, useRef } from "react";
import { motion } from "framer-motion";
import { Activity, Camera, Lightbulb, Move, Cpu, Zap } from "lucide-react";
import { API_BASE_URL } from "@/lib/api-config";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, ResponsiveContainer, Legend } from 'recharts';


interface SystemComponent {
  id: string;
  name: string;
  icon: React.ElementType;
  status: "ok" | "warning" | "error";
  value: string;
  unit: string;
  trend: number[];
}

interface AxisData {
  load: number;
  torque: number;
  peak: number;
  current: number;
  speed: number;
}

const AxisChart = ({ title, dataKey, color, data, unit }: { title: string, dataKey: string, color: string, data: any[], unit: string }) => (
  <div className="h-64 industrial-panel p-4 bg-card/40 border border-border/50">
    <div className="flex justify-between items-center mb-4">
      <h4 className="text-sm font-medium text-muted-foreground">{title}</h4>
      <span className="text-xs font-mono text-foreground">
        {data.length > 0 ? data[data.length - 1][dataKey] : "--"} {unit}
      </span>
    </div>
    <ResponsiveContainer width="100%" height="80%">
      <LineChart data={data}>
        <CartesianGrid strokeDasharray="3 3" opacity={0.1} stroke="#888" />
        <YAxis
          tick={{ fontSize: 10, fill: '#888' }}
          domain={['auto', 'auto']}
          width={30}
        />
        <RechartsTooltip
          contentStyle={{ backgroundColor: "#09090b", border: "1px solid #27272a", borderRadius: "6px" }}
          itemStyle={{ color: "#fafafa" }}
          labelStyle={{ color: "#a1a1a1", marginBottom: "4px" }}
        />
        <Line
          type="monotone"
          dataKey={dataKey}
          stroke={color}
          strokeWidth={2}
          dot={false}
          isAnimationActive={false}
        />
      </LineChart>
    </ResponsiveContainer>
  </div>
);

const HeartbeatPage = () => {
  const isMounted = useRef(true);
  const [components, setComponents] = useState<SystemComponent[]>([
    { id: "camera", name: "Camera System", icon: Camera, status: "warning", value: "--", unit: "FPS", trend: [0, 0, 0, 0, 0, 0, 0, 0] },
    { id: "lights", name: "LED Lights", icon: Lightbulb, status: "warning", value: "--", unit: "", trend: [0, 0, 0, 0, 0, 0, 0, 0] },
    { id: "gantry-x", name: "Gantry X-Axis", icon: Move, status: "ok", value: "0", unit: "mm/s", trend: [0, 0, 0, 0, 0, 0, 0, 0] },
    { id: "gantry-y", name: "Gantry Y-Axis", icon: Move, status: "ok", value: "0", unit: "mm/s", trend: [0, 0, 0, 0, 0, 0, 0, 0] },
    { id: "gantry-z", name: "Gantry Z-Axis", icon: Move, status: "ok", value: "0", unit: "mm/s", trend: [0, 0, 0, 0, 0, 0, 0, 0] },
    { id: "plc", name: "PLC Controller", icon: Cpu, status: "warning", value: "--", unit: "", trend: [0, 0, 0, 0, 0, 0, 0, 0] },
  ]);

  const [uptime, setUptime] = useState("00:00:00");
  const [startTime] = useState(() => {
    // Get stored start time or create new one
    const stored = localStorage.getItem("mecup-uptime-start");
    if (stored) {
      return parseInt(stored, 10);
    }
    const now = Date.now();
    localStorage.setItem("mecup-uptime-start", now.toString());
    return now;
  });
  const [plcConnected, setPlcConnected] = useState(false);
  const [events, setEvents] = useState<{ time: string; event: string; type: string }[]>([]);
  const [systemResources, setSystemResources] = useState({ cpu: 0, gpu: 0, memory: 0, disk: 0, network: 0 });

  // Axis Monitoring State
  const [selectedAxis, setSelectedAxis] = useState<string | null>(null);
  const [axisHistory, setAxisHistory] = useState<Record<string, any[]>>({ x: [], y: [], z: [] });

  // Cleanup on unmount
  useEffect(() => {
    isMounted.current = true;
    return () => {
      isMounted.current = false;
    };
  }, []);

  // Fetch real data from backend
  useEffect(() => {
    let timeoutId: NodeJS.Timeout;
    const fetchHeartbeatData = async () => {
      if (!isMounted.current) return;

      try {
        // Fetch camera FPS
        const cameraRes = await fetch(`${API_BASE_URL}/camera/fps`);
        if (!isMounted.current) return;
        const cameraData = await cameraRes.json();

        // Fetch PLC heartbeat (Y1 for LED)
        const plcRes = await fetch(`${API_BASE_URL}/plc/heartbeat`);
        if (!isMounted.current) return;
        const plcData = await plcRes.json();

        // Fetch PLC status with latency measurement
        const plcStartTime = performance.now();
        const plcStatusRes = await fetch(`${API_BASE_URL}/plc/status`);
        if (!isMounted.current) return;
        const plcStatusData = await plcStatusRes.json();
        const plcLatency = Math.round(performance.now() - plcStartTime);

        if (!isMounted.current) return;

        // Update PLC connection state
        setPlcConnected(plcStatusData.connected);

        // Process Axis Data
        if (plcData.axis_data) {
          const now = new Date().toLocaleTimeString();
          const axisData = plcData.axis_data;

          setAxisHistory(prev => {
            const updateHistory = (key: string, data: any) => {
              const newHistory = [...(prev[key] || []), { time: now, ...data }];
              return newHistory.slice(-50); // Keep last 50 points
            };
            return {
              x: updateHistory("x", axisData.x),
              y: updateHistory("y", axisData.y),
              z: updateHistory("z", axisData.z)
            };
          });
        }

        setComponents(prev => prev.map(comp => {
          if (comp.id === "camera") {
            const fps = cameraData.fps || 0;
            const isOpen = cameraData.is_open;
            return {
              ...comp,
              value: isOpen ? String(fps) : "OFF",
              status: isOpen ? (fps > 0 ? "ok" : "warning") : "error",
              trend: [...comp.trend.slice(1), fps]
            };
          }
          if (comp.id === "lights") {
            const y1On = plcData.y1 === 1;
            const connected = plcData.connected;
            return {
              ...comp,
              value: connected ? (y1On ? "ON" : "OFF") : "--",
              status: connected ? (y1On ? "ok" : "warning") : "error",
              trend: [...comp.trend.slice(1), y1On ? 100 : 0]
            };
          }
          if (comp.id === "gantry-x" && plcData.axis_data?.x) {
            const val = plcData.axis_data.x.speed;
            return {
              ...comp,
              value: String(val),
              status: plcStatusData.connected ? "ok" : "error",
              trend: [...comp.trend.slice(1), val]
            };
          }
          if (comp.id === "gantry-y" && plcData.axis_data?.y) {
            const val = plcData.axis_data.y.speed;
            return {
              ...comp,
              value: String(val),
              status: plcStatusData.connected ? "ok" : "error",
              trend: [...comp.trend.slice(1), val]
            };
          }
          if (comp.id === "gantry-z" && plcData.axis_data?.z) {
            const val = plcData.axis_data.z.speed;
            return {
              ...comp,
              value: String(val),
              status: plcStatusData.connected ? "ok" : "error",
              trend: [...comp.trend.slice(1), val]
            };
          }
          if (comp.id === "plc") {
            const connected = plcStatusData.connected;
            return {
              ...comp,
              value: connected ? String(plcLatency) : "OFF",
              unit: connected ? "ms" : "",
              status: connected ? (plcLatency < 50 ? "ok" : plcLatency < 100 ? "warning" : "error") : "error",
              trend: [...comp.trend.slice(1), connected ? plcLatency : 0]
            };
          }
          return comp;
        }));

        // Fetch events
        const eventsRes = await fetch(`${API_BASE_URL}/events`);
        if (!isMounted.current) return;
        const eventsData = await eventsRes.json();
        if (eventsData.events) {
          setEvents(eventsData.events);
        }

        // Fetch System Resources
        const sysRes = await fetch(`${API_BASE_URL}/system/resources`);
        if (!isMounted.current) return;
        const sysData = await sysRes.json();
        setSystemResources(sysData);

      } catch (error) {
        console.error("Failed to fetch heartbeat data:", error);
      }

      if (isMounted.current) {
        timeoutId = setTimeout(fetchHeartbeatData, 1000); // 1 Second Polling
      }
    };

    fetchHeartbeatData();
    return () => clearTimeout(timeoutId);
  }, []);

  // Update uptime
  useEffect(() => {
    const interval = setInterval(() => {
      const elapsed = Date.now() - startTime;
      const hours = Math.floor(elapsed / 3600000);
      const minutes = Math.floor((elapsed % 3600000) / 60000);
      const seconds = Math.floor((elapsed % 60000) / 1000);
      setUptime(`${String(hours).padStart(2, '0')}:${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`);
    }, 1000);
    return () => clearInterval(interval);
  }, [startTime]);

  const okCount = components.filter(c => c.status === "ok").length;
  const warningCount = components.filter(c => c.status === "warning").length;
  const errorCount = components.filter(c => c.status === "error").length;

  return (
    <div className="h-full grid grid-cols-12 gap-6">
      {/* Main Status Grid */}
      <div className="col-span-8 space-y-6">
        {/* Overview */}
        <div className="grid grid-cols-4 gap-4">
          <StatusOverviewCard label="System Status" value={plcConnected ? "OPERATIONAL" : "DISCONNECTED"} status={plcConnected ? "ok" : "error"} />
          <StatusOverviewCard label="Components OK" value={okCount.toString()} status="ok" />
          <StatusOverviewCard label="Warnings" value={warningCount.toString()} status={warningCount > 0 ? "warning" : "ok"} />
          <StatusOverviewCard label="Errors" value={errorCount.toString()} status={errorCount > 0 ? "error" : "ok"} />
        </div>

        {/* Component Grid */}
        <div className="grid grid-cols-2 gap-4">
          {components.map((component) => (
            <ComponentCard
              key={component.id}
              component={component}
              onClick={component.id.startsWith("gantry-") ? () => setSelectedAxis(component.id.replace("gantry-", "")) : undefined}
            />
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
            <ResourceBar label="CPU Usage" value={Math.round(systemResources.cpu)} />
            <ResourceBar label="GPU Usage" value={Math.round(systemResources.gpu)} />
            <ResourceBar label="Memory" value={Math.round(systemResources.memory)} />
            <ResourceBar label="Disk Space" value={Math.round(systemResources.disk)} />

          </div>
        </div>

        {/* Recent Events */}
        <div className="industrial-panel p-4 flex-1">
          <h3 className="text-sm font-medium text-muted-foreground mb-4">RECENT EVENTS</h3>
          <div className="space-y-3">
            {events.length > 0 ? events.map((event, i) => (
              <div key={i} className="flex items-start gap-3 text-sm">
                <span className="font-mono text-xs text-muted-foreground w-16 flex-shrink-0">{event.time}</span>
                <span className={`w-1.5 h-1.5 rounded-full mt-1.5 flex-shrink-0 ${event.type === "success" ? "bg-success" :
                  event.type === "warning" ? "bg-warning" :
                    event.type === "error" ? "bg-destructive" : "bg-primary"
                  }`} />
                <span className="text-foreground text-xs">{event.event}</span>
              </div>
            )) : (
              <p className="text-xs text-muted-foreground">No recent events</p>
            )}
          </div>
        </div>
      </div>
      {/* Axis Detail Modal */}
      <Dialog open={!!selectedAxis} onOpenChange={(open) => !open && setSelectedAxis(null)}>
        <DialogContent className="max-w-4xl max-h-[85vh] overflow-y-auto bg-background/95 backdrop-blur">
          <DialogHeader>
            <DialogTitle className="text-2xl font-bold flex items-center gap-2">
              <Activity className="w-6 h-6 text-primary" />
              {selectedAxis?.toUpperCase()}-Axis Real-time Monitoring
            </DialogTitle>
          </DialogHeader>

          {selectedAxis && (
            <div className="space-y-6 pt-4">
              <div className="grid grid-cols-2 gap-4">

                <AxisChart
                  title="Motor Current (%)"
                  dataKey="current"
                  color="#3b82f6"
                  data={axisHistory[selectedAxis]}
                  unit="%"
                />
                <AxisChart
                  title="Regenerative Load Ratio (%)"
                  dataKey="load"
                  color="#f59e0b"
                  data={axisHistory[selectedAxis]}
                  unit="%"
                />
                <AxisChart
                  title="Effective Load Torque (%)"
                  dataKey="torque"
                  color="#ec4899"
                  data={axisHistory[selectedAxis]}
                  unit="%"
                />
                <AxisChart
                  title="Peak Torque Ratio (%)"
                  dataKey="peak"
                  color="#ef4444"
                  data={axisHistory[selectedAxis]}
                  unit="%"
                />
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div >
  );
};

const StatusOverviewCard = ({ label, value, status }: { label: string; value: string; status: "ok" | "warning" | "error" }) => (
  <div className={`industrial-panel p-4 border ${status === "ok" ? "border-success/30" :
    status === "warning" ? "border-warning/30" : "border-destructive/30"
    }`}>
    <p className="text-xs text-muted-foreground mb-1">{label}</p>
    <p className={`text-xl font-bold font-mono ${status === "ok" ? "text-success" :
      status === "warning" ? "text-warning" : "text-destructive"
      }`}>{value}</p>
  </div>
);

const ComponentCard = ({ component, onClick }: { component: SystemComponent; onClick?: () => void }) => {
  const Icon = component.icon;
  const maxTrend = Math.max(...component.trend);
  const minTrend = Math.min(...component.trend);
  const range = maxTrend - minTrend || 1;

  return (
    <motion.div
      onClick={onClick}
      className={`industrial-panel p-4 border ${component.status === "ok" ? "border-border hover:border-success/30" :
        component.status === "warning" ? "border-warning/30" : "border-destructive/30"
        } transition-colors ${onClick ? "cursor-pointer hover:bg-accent/5" : ""}`}
    >
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-3">
          <div className={`w-10 h-10 rounded-md flex items-center justify-center ${component.status === "ok" ? "bg-success/10" :
            component.status === "warning" ? "bg-warning/10" : "bg-destructive/10"
            }`}>
            <Icon className={`w-5 h-5 ${component.status === "ok" ? "text-success" :
              component.status === "warning" ? "text-warning" : "text-destructive"
              }`} />
          </div>
          <div>
            <h4 className="font-medium text-foreground text-sm">{component.name}</h4>
            <span className={`status-indicator inline-block ${component.status === "ok" ? "status-ok" :
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
            className={`flex-1 rounded-t transition-all ${component.status === "ok" ? "bg-success/40" :
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
  <div
    role="progressbar"
    aria-label={label}
    aria-valuenow={value}
    aria-valuemin={0}
    aria-valuemax={100}
  >
    <div className="flex justify-between text-sm mb-1" aria-hidden="true">
      <span className="text-muted-foreground">{label}</span>
      <span className="font-mono text-foreground">{value}%</span>
    </div>
    <div className="h-2 bg-secondary rounded-full overflow-hidden">
      <motion.div
        className={`h-full rounded-full ${value < 60 ? "bg-success" :
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