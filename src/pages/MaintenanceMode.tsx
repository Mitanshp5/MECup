import { useState } from "react";
import { motion } from "framer-motion";
import { Camera, Lightbulb, Move, Cpu, CheckCircle, XCircle, Play, RotateCcw } from "lucide-react";

interface TestResult {
  component: string;
  status: "idle" | "testing" | "pass" | "fail";
  message: string;
}

const MaintenanceMode = () => {
  const [tests, setTests] = useState<TestResult[]>([
    { component: "Camera", status: "idle", message: "Ready to test" },
    { component: "LED Lights", status: "idle", message: "Ready to test" },
    { component: "Gantry X-Axis", status: "idle", message: "Ready to test" },
    { component: "Gantry Y-Axis", status: "idle", message: "Ready to test" },
    { component: "Gantry Z-Axis", status: "idle", message: "Ready to test" },
    { component: "PLC Connection", status: "idle", message: "Ready to test" },
  ]);

  const runTest = (index: number) => {
    setTests(prev => prev.map((t, i) => 
      i === index ? { ...t, status: "testing", message: "Testing..." } : t
    ));

    setTimeout(() => {
      const passed = Math.random() > 0.2;
      setTests(prev => prev.map((t, i) => 
        i === index ? { 
          ...t, 
          status: passed ? "pass" : "fail", 
          message: passed ? "Test passed successfully" : "Test failed - check component"
        } : t
      ));
    }, 2000);
  };

  const runAllTests = () => {
    tests.forEach((_, index) => {
      setTimeout(() => runTest(index), index * 500);
    });
  };

  const resetTests = () => {
    setTests(prev => prev.map(t => ({ ...t, status: "idle", message: "Ready to test" })));
  };

  const getIcon = (component: string) => {
    switch (component) {
      case "Camera": return Camera;
      case "LED Lights": return Lightbulb;
      case "PLC Connection": return Cpu;
      default: return Move;
    }
  };

  return (
    <div className="h-full grid grid-cols-12 gap-6">
      {/* Test Panel */}
      <div className="col-span-8">
        <div className="industrial-panel p-6 h-full">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h3 className="text-lg font-semibold text-foreground">Component Tests</h3>
              <p className="text-sm text-muted-foreground">Run diagnostics on system components</p>
            </div>
            <div className="flex gap-2">
              <button
                onClick={runAllTests}
                className="flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 transition-colors"
              >
                <Play className="w-4 h-4" />
                Run All Tests
              </button>
              <button
                onClick={resetTests}
                className="flex items-center gap-2 px-4 py-2 bg-secondary text-foreground rounded-md hover:bg-secondary/80 transition-colors"
              >
                <RotateCcw className="w-4 h-4" />
                Reset
              </button>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            {tests.map((test, index) => {
              const Icon = getIcon(test.component);
              return (
                <motion.div
                  key={test.component}
                  className={`p-4 rounded-md border transition-all ${
                    test.status === "pass" ? "bg-success/5 border-success/30" :
                    test.status === "fail" ? "bg-destructive/5 border-destructive/30" :
                    test.status === "testing" ? "bg-primary/5 border-primary/30" :
                    "bg-secondary/50 border-border"
                  }`}
                >
                  <div className="flex items-start justify-between mb-3">
                    <div className="flex items-center gap-3">
                      <div className={`w-10 h-10 rounded-md flex items-center justify-center ${
                        test.status === "pass" ? "bg-success/10" :
                        test.status === "fail" ? "bg-destructive/10" :
                        test.status === "testing" ? "bg-primary/10" :
                        "bg-secondary"
                      }`}>
                        <Icon className={`w-5 h-5 ${
                          test.status === "pass" ? "text-success" :
                          test.status === "fail" ? "text-destructive" :
                          test.status === "testing" ? "text-primary" :
                          "text-muted-foreground"
                        }`} />
                      </div>
                      <div>
                        <h4 className="font-medium text-foreground">{test.component}</h4>
                        <p className="text-xs text-muted-foreground">{test.message}</p>
                      </div>
                    </div>
                    
                    {test.status === "pass" && <CheckCircle className="w-5 h-5 text-success" />}
                    {test.status === "fail" && <XCircle className="w-5 h-5 text-destructive" />}
                    {test.status === "testing" && (
                      <div className="w-5 h-5 border-2 border-primary border-t-transparent rounded-full animate-spin" />
                    )}
                  </div>

                  <button
                    onClick={() => runTest(index)}
                    disabled={test.status === "testing"}
                    className={`w-full py-2 text-sm font-medium rounded transition-colors ${
                      test.status === "testing"
                        ? "bg-muted text-muted-foreground cursor-not-allowed"
                        : "bg-secondary hover:bg-secondary/80 text-foreground"
                    }`}
                  >
                    {test.status === "testing" ? "Testing..." : "Run Test"}
                  </button>
                </motion.div>
              );
            })}
          </div>
        </div>
      </div>

      {/* Calibration Panel */}
      <div className="col-span-4 space-y-4">
        <div className="industrial-panel p-4">
          <h3 className="text-sm font-medium text-muted-foreground mb-4">CALIBRATION</h3>
          <div className="space-y-2">
            {["Camera Focus", "Color Balance", "Gantry Alignment", "Light Intensity"].map((item) => (
              <button
                key={item}
                className="w-full flex items-center justify-between px-4 py-3 bg-secondary border border-border rounded-md text-foreground hover:bg-secondary/80 transition-colors"
              >
                <span className="text-sm">{item}</span>
                <span className="text-xs text-muted-foreground">Calibrate</span>
              </button>
            ))}
          </div>
        </div>

        <div className="industrial-panel p-4">
          <h3 className="text-sm font-medium text-muted-foreground mb-4">TEST SUMMARY</h3>
          <div className="grid grid-cols-3 gap-2 text-center">
            <div className="p-3 bg-success/10 rounded">
              <p className="text-xl font-bold text-success font-mono">
                {tests.filter(t => t.status === "pass").length}
              </p>
              <p className="text-xs text-muted-foreground">Passed</p>
            </div>
            <div className="p-3 bg-destructive/10 rounded">
              <p className="text-xl font-bold text-destructive font-mono">
                {tests.filter(t => t.status === "fail").length}
              </p>
              <p className="text-xs text-muted-foreground">Failed</p>
            </div>
            <div className="p-3 bg-muted rounded">
              <p className="text-xl font-bold text-muted-foreground font-mono">
                {tests.filter(t => t.status === "idle" || t.status === "testing").length}
              </p>
              <p className="text-xs text-muted-foreground">Pending</p>
            </div>
          </div>
        </div>

        <div className="industrial-panel p-4">
          <h3 className="text-sm font-medium text-muted-foreground mb-4">SYSTEM INFO</h3>
          <div className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-muted-foreground">Firmware</span>
              <span className="font-mono text-foreground">v5.0.12</span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">Last Calibration</span>
              <span className="font-mono text-foreground">2024-01-10</span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">Operating Hours</span>
              <span className="font-mono text-foreground">1,247 hrs</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default MaintenanceMode;
