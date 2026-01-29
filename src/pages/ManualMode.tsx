import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { ArrowUp, ArrowDown, ArrowLeft, ArrowRight, Home, RotateCcw, Zap } from "lucide-react";

const ManualMode = () => {
  const [position, setPosition] = useState({ x: 0, y: 0, z: 0 });
  const [speeds, setSpeeds] = useState({ x: 50, y: 50, z: 50 });
  const [jogDistance, setJogDistance] = useState(10);
  const [plcConnected, setPlcConnected] = useState(false);

  // Poll PLC connection status
  useEffect(() => {
    const checkPlc = async () => {
      try {
        const res = await fetch('http://localhost:5001/plc/status');
        const data = await res.json();
        setPlcConnected(data.connected);
      } catch (e) {
        setPlcConnected(false);
      }
    };

    checkPlc();
    const interval = setInterval(checkPlc, 2000);
    return () => clearInterval(interval);
  }, []);

  const [servoEnabled, setServoEnabled] = useState(false);

  const handleServoToggle = async () => {
    try {
      const newState = !servoEnabled;
      // Optimistic update
      setServoEnabled(newState);
      await fetch('http://localhost:5001/servo/enable', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ enable: newState })
      });
    } catch (error) {
      console.error("Failed to toggle servo:", error);
      // Revert on error
      setServoEnabled(!servoEnabled);
    }
  };

  const handleMove = async (command: string) => {
    if (!servoEnabled) {
      alert("Please Enable Servo First!");
      return;
    }
    try {
      await fetch('http://localhost:5001/servo/move', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ command })
      });
    } catch (error) {
      alert("Move Failed: " + error);
    }
  };

  const handleHome = () => {
    setPosition({ x: 0, y: 0, z: 0 });
  };

  return (
    <div className="h-full grid grid-cols-12 gap-6 relative">
      {/* Blocking Overlay */}
      {!plcConnected && (
        <div className="absolute inset-0 z-50 bg-background/80 backdrop-blur-sm flex items-center justify-center rounded-lg border border-destructive/50">
          <div className="text-center space-y-4 p-8 bg-card border border-destructive rounded-xl shadow-lg">
            <div className="h-12 w-12 rounded-full bg-destructive/20 flex items-center justify-center mx-auto animate-pulse">
              <Zap className="h-6 w-6 text-destructive" />
            </div>
            <div>
              <h3 className="text-xl font-bold text-destructive">PLC DISCONNECTED</h3>
              <p className="text-muted-foreground mt-2">Manual controls are disabled.</p>
              <p className="text-xs text-muted-foreground mt-1">Please check connection in Settings.</p>
            </div>
          </div>
        </div>
      )}

      {/* Main Control Panel */}
      <div className="col-span-8 space-y-6">
        {/* Position Display */}
        <div className="industrial-panel p-6">
          <h3 className="text-sm font-medium text-muted-foreground mb-4">CURRENT POSITION</h3>
          <div className="grid grid-cols-3 gap-6">
            {["X", "Y", "Z"].map((axis) => (
              <div key={axis} className="text-center">
                <div className="data-display text-2xl font-bold text-primary mb-2">
                  {position[axis.toLowerCase() as "x" | "y" | "z"].toFixed(2)}
                  <span className="text-sm text-muted-foreground ml-1">mm</span>
                </div>
                <p className="text-sm text-muted-foreground">{axis}-Axis</p>
              </div>
            ))}
          </div>
        </div>

        {/* Jog Controls */}
        <div className="industrial-panel p-6">
          <h3 className="text-sm font-medium text-muted-foreground mb-4">JOG CONTROLS</h3>

          <div className="grid grid-cols-2 gap-8">
            {/* XY Control */}
            <div>
              <p className="text-xs text-muted-foreground mb-3 text-center">X/Y AXIS</p>
              <div className="grid grid-cols-3 gap-2 max-w-xs mx-auto">
                <div />
                <JogButton icon={ArrowUp} onClick={() => handleMove("y_fwd_12.5")} label="Y+ (12.5mm)" />
                <div />
                <JogButton icon={ArrowLeft} onClick={() => handleMove("x_left_17")} label="X- (17mm)" />
                <button
                  onClick={() => handleMove("x_home")}
                  className="p-4 bg-primary/10 border border-primary/30 rounded-md text-primary hover:bg-primary/20 transition-colors"
                  title="X Home"
                >
                  <Home className="w-5 h-5 mx-auto" />
                </button>
                <JogButton icon={ArrowRight} onClick={() => handleMove("x_right_17")} label="X+ (17mm)" />
                <div />
                <JogButton icon={ArrowDown} onClick={() => handleMove("y_back_12.5")} label="Y- (12.5mm)" />
                <div />
              </div>
            </div>

            {/* Z Control */}
            <div>
              <p className="text-xs text-muted-foreground mb-3 text-center">Z AXIS</p>
              <div className="flex flex-col gap-2 items-center">
                <JogButton icon={ArrowUp} onClick={() => handleMove("z_up_5")} label="Z+ (5mm)" />
                <div className="h-8" />
                <JogButton icon={ArrowDown} onClick={() => handleMove("z_down_5")} label="Z- (5mm)" />
              </div>
            </div>
          </div>
        </div>

        {/* Speed & Distance */}
        <div className="grid grid-cols-2 gap-6">
          <div className="industrial-panel p-4">
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-sm font-medium text-muted-foreground">AXIS SPEEDS</h3>
            </div>
            <div className="space-y-4">
              <div className="grid grid-cols-3 gap-2">
                {/* X Axis */}
                <div className="space-y-1">
                  <div className="flex justify-between text-xs">
                    <span className="font-bold">X</span>
                  </div>
                  <input
                    type="number"
                    min={0}
                    max={50000}
                    value={speeds.x}
                    onChange={(e) => setSpeeds(prev => ({ ...prev, x: Math.max(0, Math.min(50000, Number(e.target.value))) }))}
                    className="w-full bg-secondary border border-border rounded px-2 py-1 text-sm text-center"
                  />
                </div>
                {/* Y Axis */}
                <div className="space-y-1">
                  <div className="flex justify-between text-xs">
                    <span className="font-bold">Y</span>
                  </div>
                  <input
                    type="number"
                    min={0}
                    max={50000}
                    value={speeds.y}
                    onChange={(e) => setSpeeds(prev => ({ ...prev, y: Math.max(0, Math.min(50000, Number(e.target.value))) }))}
                    className="w-full bg-secondary border border-border rounded px-2 py-1 text-sm text-center"
                  />
                </div>
                {/* Z Axis */}
                <div className="space-y-1">
                  <div className="flex justify-between text-xs">
                    <span className="font-bold">Z</span>
                  </div>
                  <input
                    type="number"
                    min={0}
                    max={50000}
                    value={speeds.z}
                    onChange={(e) => setSpeeds(prev => ({ ...prev, z: Math.max(0, Math.min(50000, Number(e.target.value))) }))}
                    className="w-full bg-secondary border border-border rounded px-2 py-1 text-sm text-center"
                  />
                </div>
              </div>
              <button
                onClick={() => {
                  fetch('http://localhost:5001/servo/speeds', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(speeds)
                  })
                    .then(async res => {
                      if (!res.ok) {
                        const err = await res.json();
                        alert(err.detail || "Failed to set speeds");
                      } else {
                        alert("Speeds Set Successfully");
                      }
                    })
                    .catch(err => alert("Connection Error: " + err));
                }}
                className="w-full py-2 bg-primary text-primary-foreground rounded-md text-sm font-medium hover:bg-primary/90 transition-colors mt-2"
              >
                SET SPEEDS
              </button>
            </div>
          </div>

          <div className="industrial-panel p-4">
            <h3 className="text-sm font-medium text-muted-foreground mb-3">JOG DISTANCE</h3>
            <div className="flex gap-2">
              {[1, 10, 50, 100].map((dist) => (
                <button
                  key={dist}
                  onClick={() => setJogDistance(dist)}
                  className={`flex-1 py-2 rounded-md text-sm font-mono transition-colors ${jogDistance === dist
                    ? "bg-primary text-primary-foreground"
                    : "bg-secondary text-foreground hover:bg-secondary/80"
                    }`}
                >
                  {dist}mm
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Side Panel */}
      <div className="col-span-4 space-y-4">
        {/* Quick Actions */}
        <div className="industrial-panel p-4">
          <h3 className="text-sm font-medium text-muted-foreground mb-4">PLC CONTROLS</h3>
          <div className="space-y-2">
            <button
              onClick={async () => {
                try {
                  const res = await fetch("http://localhost:5001/plc/scan-start", { method: "POST" });
                  const data = await res.json();
                  alert(data.success ? "Scan Started (M5 ON)" : data.error);
                } catch (e) { alert("Network Error"); }
              }}
              className="w-full flex items-center gap-3 px-4 py-3 bg-success/10 border border-success/30 rounded-md text-success hover:bg-success/20 transition-colors"
            >
              <Zap className="w-5 h-5" />
              <span className="font-medium">Scan Start (M5)</span>
            </button>
            <button
              onClick={async () => {
                try {
                  const res = await fetch("http://localhost:5001/plc/grid-one", { method: "POST" });
                  const data = await res.json();
                  alert(data.success ? "Grid One Triggered (M4 ON)" : data.error);
                } catch (e) { alert("Network Error"); }
              }}
              className="w-full flex items-center gap-3 px-4 py-3 bg-primary/10 border border-primary/30 rounded-md text-primary hover:bg-primary/20 transition-colors"
            >
              <RotateCcw className="w-5 h-5" />
              <span className="font-medium">Grid One (M4)</span>
            </button>
            <button
              onClick={async () => {
                try {
                  const res = await fetch("http://localhost:5001/plc/cycle-reset", { method: "POST" });
                  const data = await res.json();
                  alert(data.success ? "Cycle Reset (M120 ON)" : data.error);
                } catch (e) { alert("Network Error"); }
              }}
              className="w-full flex items-center gap-3 px-4 py-3 bg-warning/10 border border-warning/30 rounded-md text-warning hover:bg-warning/20 transition-colors"
            >
              <RotateCcw className="w-5 h-5" />
              <span className="font-medium">Cycle Reset (M120)</span>
            </button>
            <button
              onClick={async () => {
                try {
                  const res = await fetch("http://localhost:5001/plc/homing-start", { method: "POST" });
                  const data = await res.json();
                  alert(data.success ? "Homing Started (X6 ON)" : data.error);
                } catch (e) { alert("Network Error"); }
              }}
              className="w-full flex items-center gap-3 px-4 py-3 bg-secondary border border-border rounded-md text-foreground hover:bg-secondary/80 transition-colors"
            >
              <Home className="w-5 h-5" />
              <span className="font-medium">Homing Start (X6)</span>
            </button>
          </div>
        </div>

        {/* Servo Status */}
        <div className="industrial-panel p-4">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-medium text-muted-foreground">SERVO CONTROL</h3>
            <button
              onClick={handleServoToggle}
              className={`px-3 py-1 rounded text-xs font-bold transition-all ${servoEnabled ? "bg-success text-success-foreground" : "bg-destructive text-destructive-foreground"}`}
            >
              {servoEnabled ? "ON" : "OFF"}
            </button>
          </div>

          <div className="space-y-3">
            <div className="flex items-center justify-between p-3 bg-secondary/50 rounded-md">
              <div className="flex items-center gap-3">
                <Zap className={`w-4 h-4 ${servoEnabled ? "text-success" : "text-destructive"}`} />
                <span className="text-sm text-foreground">Main Power (M0)</span>
              </div>
              <span className={`text-xs font-medium ${servoEnabled ? "text-success" : "text-destructive"}`}>
                {servoEnabled ? "ENABLED" : "DISABLED"}
              </span>
            </div>
          </div>
        </div>

        {/* Position History */}
        <div className="industrial-panel p-4 flex-1">
          <h3 className="text-sm font-medium text-muted-foreground mb-4">POSITION LOG</h3>
          <div className="space-y-2 text-xs font-mono">
            <div className="text-muted-foreground">
              {`[${new Date().toLocaleTimeString()}] Position: X:${position.x} Y:${position.y} Z:${position.z}`}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

const JogButton = ({ icon: Icon, onClick, label }: { icon: React.ElementType; onClick: () => void; label: string }) => (
  <motion.button
    whileHover={{ scale: 1.05 }}
    whileTap={{ scale: 0.95 }}
    onClick={onClick}
    className="p-4 bg-secondary border border-border rounded-md text-foreground hover:bg-secondary/80 hover:border-primary/50 transition-colors"
    title={label}
  >
    <Icon className="w-5 h-5 mx-auto" />
  </motion.button>
);

export default ManualMode;
