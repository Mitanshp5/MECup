import { useState } from "react";
import { motion } from "framer-motion";
import { ArrowUp, ArrowDown, ArrowLeft, ArrowRight, Home, RotateCcw, Zap } from "lucide-react";

const ManualMode = () => {
  const [position, setPosition] = useState({ x: 0, y: 0, z: 0 });
  const [speed, setSpeed] = useState(50);
  const [jogDistance, setJogDistance] = useState(10);

  const handleJog = (axis: "x" | "y" | "z", direction: 1 | -1) => {
    setPosition(prev => ({
      ...prev,
      [axis]: Math.round((prev[axis] + (jogDistance * direction)) * 100) / 100
    }));
  };

  const handleHome = () => {
    setPosition({ x: 0, y: 0, z: 0 });
  };

  return (
    <div className="h-full grid grid-cols-12 gap-6">
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
                <JogButton icon={ArrowUp} onClick={() => handleJog("y", 1)} label="Y+" />
                <div />
                <JogButton icon={ArrowLeft} onClick={() => handleJog("x", -1)} label="X-" />
                <button
                  onClick={handleHome}
                  className="p-4 bg-primary/10 border border-primary/30 rounded-md text-primary hover:bg-primary/20 transition-colors"
                >
                  <Home className="w-5 h-5 mx-auto" />
                </button>
                <JogButton icon={ArrowRight} onClick={() => handleJog("x", 1)} label="X+" />
                <div />
                <JogButton icon={ArrowDown} onClick={() => handleJog("y", -1)} label="Y-" />
                <div />
              </div>
            </div>

            {/* Z Control */}
            <div>
              <p className="text-xs text-muted-foreground mb-3 text-center">Z AXIS</p>
              <div className="flex flex-col gap-2 items-center">
                <JogButton icon={ArrowUp} onClick={() => handleJog("z", 1)} label="Z+" />
                <div className="h-20 w-16 bg-secondary rounded-md flex items-center justify-center border border-border">
                  <span className="font-mono text-lg text-foreground">{position.z.toFixed(1)}</span>
                </div>
                <JogButton icon={ArrowDown} onClick={() => handleJog("z", -1)} label="Z-" />
              </div>
            </div>
          </div>
        </div>

        {/* Speed & Distance */}
        <div className="grid grid-cols-2 gap-6">
          <div className="industrial-panel p-4">
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-sm font-medium text-muted-foreground">JOG SPEED</h3>
              <span className="font-mono text-primary">{speed}%</span>
            </div>
            <input
              type="range"
              min={1}
              max={100}
              value={speed}
              onChange={(e) => setSpeed(Number(e.target.value))}
              className="w-full accent-primary"
            />
            <div className="flex justify-between text-xs text-muted-foreground mt-2">
              <span>Slow</span>
              <span>Fast</span>
            </div>
          </div>

          <div className="industrial-panel p-4">
            <h3 className="text-sm font-medium text-muted-foreground mb-3">JOG DISTANCE</h3>
            <div className="flex gap-2">
              {[1, 10, 50, 100].map((dist) => (
                <button
                  key={dist}
                  onClick={() => setJogDistance(dist)}
                  className={`flex-1 py-2 rounded-md text-sm font-mono transition-colors ${
                    jogDistance === dist
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
          <h3 className="text-sm font-medium text-muted-foreground mb-4">QUICK ACTIONS</h3>
          <div className="space-y-2">
            <button 
              onClick={handleHome}
              className="w-full flex items-center gap-3 px-4 py-3 bg-secondary border border-border rounded-md text-foreground hover:bg-secondary/80 transition-colors"
            >
              <Home className="w-5 h-5" />
              <span className="font-medium">Home All Axes</span>
            </button>
            <button className="w-full flex items-center gap-3 px-4 py-3 bg-secondary border border-border rounded-md text-foreground hover:bg-secondary/80 transition-colors">
              <RotateCcw className="w-5 h-5" />
              <span className="font-medium">Reset Position</span>
            </button>
          </div>
        </div>

        {/* Servo Status */}
        <div className="industrial-panel p-4">
          <h3 className="text-sm font-medium text-muted-foreground mb-4">SERVO STATUS</h3>
          <div className="space-y-3">
            {["X-Axis Servo", "Y-Axis Servo", "Z-Axis Servo"].map((servo, i) => (
              <div key={i} className="flex items-center justify-between p-3 bg-secondary/50 rounded-md">
                <div className="flex items-center gap-3">
                  <Zap className="w-4 h-4 text-success" />
                  <span className="text-sm text-foreground">{servo}</span>
                </div>
                <span className="text-xs font-medium text-success">ENABLED</span>
              </div>
            ))}
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
