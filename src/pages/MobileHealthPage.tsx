import { useState, useEffect, useRef } from "react";
import { useNavigate } from "react-router-dom";
import { motion, AnimatePresence } from "framer-motion";
import { Activity, Camera, Lightbulb, Move, Cpu, ChevronDown, ChevronUp, X, ArrowLeft } from "lucide-react";
import { API_BASE_URL } from "@/lib/api-config";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, ResponsiveContainer } from 'recharts';

interface SystemComponent {
  id: string;
  name: string;
  icon: React.ElementType;
  status: "ok" | "warning" | "error";
  value: string;
  unit: string;
  trend: number[];
}

const MobileHealthPage = () => {
  const navigate = useNavigate();
  const isMounted = useRef(true);
  const [components, setComponents] = useState<SystemComponent[]>([
    { id: "camera", name: "Camera System", icon: Camera, status: "warning", value: "--", unit: "FPS", trend: [0, 0, 0, 0, 0, 0, 0, 0] },
    { id: "lights", name: "LED Lights", icon: Lightbulb, status: "warning", value: "--", unit: "", trend: [0, 0, 0, 0, 0, 0, 0, 0] },
    { id: "gantry-x", name: "Gantry X-Axis", icon: Move, status: "ok", value: "0", unit: "rpm", trend: [0, 0, 0, 0, 0, 0, 0, 0] },
    { id: "gantry-y", name: "Gantry Y-Axis", icon: Move, status: "ok", value: "0", unit: "rpm", trend: [0, 0, 0, 0, 0, 0, 0, 0] },
    { id: "gantry-z", name: "Gantry Z-Axis", icon: Move, status: "ok", value: "0", unit: "rpm", trend: [0, 0, 0, 0, 0, 0, 0, 0] },
    { id: "plc", name: "PLC Controller", icon: Cpu, status: "warning", value: "--", unit: "", trend: [0, 0, 0, 0, 0, 0, 0, 0] },
  ]);

  const [uptime, setUptime] = useState("00:00:00");
  const [startTime] = useState(() => {
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
  const [selectedAxis, setSelectedAxis] = useState<string | null>(null);
  const [axisHistory, setAxisHistory] = useState<Record<string, any[]>>({ x: [], y: [], z: [] });
  const [expandedSection, setExpandedSection] = useState<string | null>("overview");

  useEffect(() => {
    isMounted.current = true;
    return () => {
      isMounted.current = false;
    };
  }, []);

  useEffect(() => {
    let timeoutId: NodeJS.Timeout;
    const fetchHeartbeatData = async () => {
      if (!isMounted.current) return;

      try {
        const cameraRes = await fetch(`${API_BASE_URL}/camera/fps`);
        if (!isMounted.current) return;
        const cameraData = await cameraRes.json();

        const plcRes = await fetch(`${API_BASE_URL}/plc/heartbeat`);
        if (!isMounted.current) return;
        const plcData = await plcRes.json();

        const plcStartTime = performance.now();
        const plcStatusRes = await fetch(`${API_BASE_URL}/plc/status`);
        if (!isMounted.current) return;
        const plcStatusData = await plcStatusRes.json();
        const plcLatency = Math.round(performance.now() - plcStartTime);

        if (!isMounted.current) return;

        setPlcConnected(plcStatusData.connected);

        if (plcData.axis_data) {
          const now = new Date().toLocaleTimeString();
          const axisData = plcData.axis_data;

          setAxisHistory(prev => {
            const updateHistory = (key: string, data: any) => {
              const newHistory = [...(prev[key] || []), { time: now, ...data }];
              return newHistory.slice(-50);
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

        const eventsRes = await fetch(`${API_BASE_URL}/events`);
        if (!isMounted.current) return;
        const eventsData = await eventsRes.json();
        if (eventsData.events) {
          setEvents(eventsData.events);
        }

        const sysRes = await fetch(`${API_BASE_URL}/system/resources`);
        if (!isMounted.current) return;
        const sysData = await sysRes.json();
        setSystemResources(sysData);

      } catch (error) {
        console.error("Failed to fetch heartbeat data:", error);
      }

      if (isMounted.current) {
        timeoutId = setTimeout(fetchHeartbeatData, 1000);
      }
    };

    fetchHeartbeatData();
    return () => clearTimeout(timeoutId);
  }, []);

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

  const toggleSection = (section: string) => {
    setExpandedSection(expandedSection === section ? null : section);
  };

  return (
    <div className="min-h-screen bg-background pb-20">
      {/* Header - Fixed */}
      <div className="sticky top-0 z-50 bg-background/95 backdrop-blur border-b border-border">
        <div className="px-4 py-3">
          <div className="flex items-center justify-between mb-3">
            <h1 className="text-xl font-bold flex items-center gap-2">
              <button
                onClick={() => navigate("/mobile")}
                className="w-8 h-8 flex items-center justify-center rounded-full bg-card/60 border border-border/50"
              >
                <ArrowLeft className="w-4 h-4" />
              </button>
              <Activity className="w-5 h-5 text-primary" />
              System Health
            </h1>
            <div className={`px-3 py-1 rounded-full text-xs font-medium ${
              plcConnected ? "bg-success/20 text-success" : "bg-destructive/20 text-destructive"
            }`}>
              {plcConnected ? "ONLINE" : "OFFLINE"}
            </div>
          </div>
          
          {/* Quick Stats */}
          <div className="grid grid-cols-4 gap-2">
            <div className="bg-card/40 rounded-lg p-2 text-center border border-border/50">
              <div className="text-xs text-muted-foreground mb-1">OK</div>
              <div className="text-lg font-bold text-success">{okCount}</div>
            </div>
            <div className="bg-card/40 rounded-lg p-2 text-center border border-border/50">
              <div className="text-xs text-muted-foreground mb-1">Warn</div>
              <div className="text-lg font-bold text-warning">{warningCount}</div>
            </div>
            <div className="bg-card/40 rounded-lg p-2 text-center border border-border/50">
              <div className="text-xs text-muted-foreground mb-1">Error</div>
              <div className="text-lg font-bold text-destructive">{errorCount}</div>
            </div>
            <div className="bg-card/40 rounded-lg p-2 text-center border border-border/50">
              <div className="text-xs text-muted-foreground mb-1">Uptime</div>
              <div className="text-xs font-mono font-bold text-primary">{uptime.split(':')[0]}h</div>
            </div>
          </div>
        </div>
      </div>

      {/* Content - Scrollable */}
      <div className="px-4 py-4 space-y-3">
        {/* Components Section */}
        <CollapsibleSection
          title="System Components"
          isExpanded={expandedSection === "components"}
          onToggle={() => toggleSection("components")}
          badge={`${okCount}/${components.length}`}
        >
          <div className="space-y-2">
            {components.map((component) => (
              <MobileComponentCard
                key={component.id}
                component={component}
                onClick={component.id.startsWith("gantry-") ? () => setSelectedAxis(component.id.replace("gantry-", "")) : undefined}
              />
            ))}
          </div>
        </CollapsibleSection>

        {/* System Resources Section */}
        <CollapsibleSection
          title="System Resources"
          isExpanded={expandedSection === "resources"}
          onToggle={() => toggleSection("resources")}
        >
          <div className="space-y-3">
            <MobileResourceBar label="CPU" value={Math.round(systemResources.cpu)} />
            <MobileResourceBar label="GPU" value={Math.round(systemResources.gpu)} />
            <MobileResourceBar label="Memory" value={Math.round(systemResources.memory)} />
            <MobileResourceBar label="Disk" value={Math.round(systemResources.disk)} />
          </div>
        </CollapsibleSection>

        {/* Recent Events Section */}
        <CollapsibleSection
          title="Recent Events"
          isExpanded={expandedSection === "events"}
          onToggle={() => toggleSection("events")}
          badge={events.length > 0 ? String(events.length) : undefined}
        >
          <div className="space-y-2">
            {events.length > 0 ? events.slice(0, 10).map((event, i) => (
              <div key={i} className="flex items-start gap-2 text-sm bg-card/30 p-2 rounded border border-border/30">
                <span className={`w-2 h-2 rounded-full mt-1.5 flex-shrink-0 ${
                  event.type === "success" ? "bg-success" :
                  event.type === "warning" ? "bg-warning" :
                  event.type === "error" ? "bg-destructive" : "bg-primary"
                }`} />
                <div className="flex-1 min-w-0">
                  <div className="text-xs text-foreground break-words">{event.event}</div>
                  <div className="text-xs text-muted-foreground mt-0.5">{event.time}</div>
                </div>
              </div>
            )) : (
              <p className="text-sm text-muted-foreground text-center py-4">No recent events</p>
            )}
          </div>
        </CollapsibleSection>

        {/* Full Uptime Display */}
        <div className="bg-card/40 rounded-lg p-4 text-center border border-border/50">
          <div className="text-xs text-muted-foreground mb-2">SYSTEM UPTIME</div>
          <div className="text-3xl font-mono font-bold text-primary">{uptime}</div>
          <div className="text-xs text-muted-foreground mt-1">Since last restart</div>
        </div>
      </div>

      {/* Axis Detail Modal */}
      <AnimatePresence>
        {selectedAxis && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 bg-background/95 backdrop-blur overflow-y-auto"
          >
            <div className="min-h-screen p-4">
              <div className="flex items-center justify-between mb-4 sticky top-0 bg-background/95 py-2">
                <h2 className="text-xl font-bold flex items-center gap-2">
                  <Activity className="w-5 h-5 text-primary" />
                  {selectedAxis.toUpperCase()}-Axis Monitor
                </h2>
                <button
                  onClick={() => setSelectedAxis(null)}
                  className="w-8 h-8 flex items-center justify-center rounded-full bg-card/40 border border-border/50"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>

              <div className="space-y-4">
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
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

const CollapsibleSection = ({ 
  title, 
  isExpanded, 
  onToggle, 
  children, 
  badge 
}: { 
  title: string; 
  isExpanded: boolean; 
  onToggle: () => void; 
  children: React.ReactNode;
  badge?: string;
}) => (
  <div className="bg-card/40 rounded-lg border border-border/50 overflow-hidden">
    <button
      onClick={onToggle}
      className="w-full flex items-center justify-between p-3 text-left"
    >
      <div className="flex items-center gap-2">
        <span className="font-medium text-sm">{title}</span>
        {badge && (
          <span className="px-2 py-0.5 rounded-full bg-primary/20 text-primary text-xs font-medium">
            {badge}
          </span>
        )}
      </div>
      {isExpanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
    </button>
    <AnimatePresence>
      {isExpanded && (
        <motion.div
          initial={{ height: 0, opacity: 0 }}
          animate={{ height: "auto", opacity: 1 }}
          exit={{ height: 0, opacity: 0 }}
          transition={{ duration: 0.2 }}
        >
          <div className="p-3 pt-0 border-t border-border/30">
            {children}
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  </div>
);

const MobileComponentCard = ({ component, onClick }: { component: SystemComponent; onClick?: () => void }) => {
  const Icon = component.icon;
  const maxTrend = Math.max(...component.trend);
  const minTrend = Math.min(...component.trend);
  const range = maxTrend - minTrend || 1;

  return (
    <motion.div
      onClick={onClick}
      className={`bg-card/30 rounded-lg p-3 border ${
        component.status === "ok" ? "border-border/50" :
        component.status === "warning" ? "border-warning/30" : "border-destructive/30"
      } ${onClick ? "active:scale-95" : ""}`}
      whileTap={onClick ? { scale: 0.95 } : {}}
    >
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2">
          <div className={`w-8 h-8 rounded flex items-center justify-center ${
            component.status === "ok" ? "bg-success/10" :
            component.status === "warning" ? "bg-warning/10" : "bg-destructive/10"
          }`}>
            <Icon className={`w-4 h-4 ${
              component.status === "ok" ? "text-success" :
              component.status === "warning" ? "text-warning" : "text-destructive"
            }`} />
          </div>
          <div>
            <div className="text-sm font-medium">{component.name}</div>
            <div className={`text-xs ${
              component.status === "ok" ? "text-success" :
              component.status === "warning" ? "text-warning" : "text-destructive"
            }`}>
              {component.status.toUpperCase()}
            </div>
          </div>
        </div>
        <div className="text-right">
          <div className="font-mono text-lg font-bold">{component.value}</div>
          <div className="text-xs text-muted-foreground">{component.unit}</div>
        </div>
      </div>

      {/* Mini chart */}
      <div className="h-6 flex items-end gap-0.5">
        {component.trend.map((value, i) => (
          <div
            key={i}
            className={`flex-1 rounded-t transition-all ${
              component.status === "ok" ? "bg-success/40" :
              component.status === "warning" ? "bg-warning/40" : "bg-destructive/40"
            }`}
            style={{ height: `${((value - minTrend) / range) * 100}%`, minHeight: "3px" }}
          />
        ))}
      </div>
    </motion.div>
  );
};

const MobileResourceBar = ({ label, value }: { label: string; value: number }) => (
  <div>
    <div className="flex justify-between text-sm mb-1.5">
      <span className="text-muted-foreground">{label}</span>
      <span className="font-mono font-medium">{value}%</span>
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

const AxisChart = ({ title, dataKey, color, data, unit }: { title: string, dataKey: string, color: string, data: any[], unit: string }) => (
  <div className="bg-card/40 border border-border/50 rounded-lg p-3">
    <div className="flex justify-between items-center mb-3">
      <h4 className="text-sm font-medium">{title}</h4>
      <span className="text-xs font-mono">
        {data.length > 0 ? data[data.length - 1][dataKey] : "--"} {unit}
      </span>
    </div>
    <div className="h-48">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data}>
          <CartesianGrid strokeDasharray="3 3" opacity={0.1} stroke="#888" />
          <XAxis hide />
          <YAxis
            tick={{ fontSize: 10, fill: '#888' }}
            domain={['auto', 'auto']}
            width={30}
          />
          <RechartsTooltip
            contentStyle={{ backgroundColor: "#09090b", border: "1px solid #27272a", borderRadius: "6px", fontSize: "12px" }}
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
  </div>
);

export default MobileHealthPage;
