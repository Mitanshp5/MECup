import { Canvas } from "@react-three/fiber";
import { OrbitControls, PerspectiveCamera, useGLTF, Html } from "@react-three/drei";
import { motion } from "framer-motion";
import { Activity, TrendingUp, Shield, Zap, Award, Users, Target, Cpu, Loader2 } from "lucide-react";
import { Suspense } from "react";

interface DashboardProps {
  onPageChange: (page: string) => void;
}

// Loading component for 3D model
const Loader = () => {
  return (
    <Html center>
      <div className="flex flex-col items-center gap-3 bg-background/80 backdrop-blur-sm px-6 py-4 rounded-lg border border-primary/20">
        <Loader2 className="w-8 h-8 text-primary animate-spin" />
        <p className="text-sm font-medium text-foreground">Loading 3D Model...</p>
      </div>
    </Html>
  );
};

// GLB Model component
const GLBModel = () => {
  const { scene } = useGLTF("/assets/DoorChecker.glb");

  return (
    <primitive
      object={scene}
      scale={1}
      position={[0, 0, 0]}
    />
  );
};

const MetricCard = ({ title, value, trend, icon: Icon, color = "primary" }: {
  title: string;
  value: string;
  trend?: string;
  icon: React.ElementType;
  color?: string;
}) => (
  <motion.div
    whileHover={{ scale: 1.02, y: -2 }}
    className="industrial-panel p-5 transition-all hover:border-primary/50"
  >
    <div className="flex items-start justify-between mb-3">
      <div className={`w-11 h-11 rounded-lg bg-${color}/10 flex items-center justify-center border border-${color}/20`}>
        <Icon className={`w-6 h-6 text-${color}`} />
      </div>
      {trend && (
        <div className="flex items-center gap-1 text-xs font-medium text-success">
          <TrendingUp className="w-3 h-3" />
          {trend}
        </div>
      )}
    </div>
    <h3 className="text-3xl font-bold text-foreground font-mono mb-1">{value}</h3>
    <p className="text-sm text-muted-foreground">{title}</p>
  </motion.div>
);

const InfoCard = ({ title, description, icon: Icon }: {
  title: string;
  description: string;
  icon: React.ElementType;
}) => (
  <div className="flex gap-4 p-4 rounded-lg bg-secondary/30 border border-border hover:border-primary/30 transition-colors">
    <div className="w-10 h-10 rounded-md bg-primary/10 flex items-center justify-center border border-primary/20 flex-shrink-0">
      <Icon className="w-5 h-5 text-primary" />
    </div>
    <div>
      <h4 className="text-sm font-semibold text-foreground mb-1">{title}</h4>
      <p className="text-xs text-muted-foreground leading-relaxed">{description}</p>
    </div>
  </div>
);

const Dashboard = ({ onPageChange }: DashboardProps) => {
  return (
    <div className="h-full grid grid-cols-3 grid-rows-2 gap-6">
      {/* Top-Left: 3D Model Viewer (spans 2 columns) */}
      <div className="col-span-2 industrial-panel overflow-hidden relative">
        <div className="absolute top-4 left-4 z-10">
          <h3 className="text-sm font-medium text-muted-foreground mb-1">MACHINE VIEW</h3>
          <p className="text-xs text-muted-foreground font-mono">Spectra-Scan</p>
        </div>

        <Canvas className="w-full h-full">
          <PerspectiveCamera makeDefault position={[5, 3, 5]} />
          <OrbitControls
            enablePan={false}
            minDistance={2}
            maxDistance={15}
            autoRotate
            autoRotateSpeed={0.8}
          />
          <ambientLight intensity={0.5} />
          <directionalLight position={[5, 5, 5]} intensity={1.2} />
          <pointLight position={[-3, 3, -3]} intensity={0.6} color="#00d4ff" />
          <spotLight position={[0, 10, 0]} intensity={0.5} angle={0.3} penumbra={1} />
          <Suspense fallback={<Loader />}>
            <GLBModel />
          </Suspense>
        </Canvas>
      </div>

      {/* Right Side: About Spectra-Scan (spanning both rows) */}
      <div className="row-span-2 industrial-panel p-6 overflow-y-auto">
        <div className="flex items-center gap-3 mb-4">
          <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center border border-primary/20 flex-shrink-0">
            <Cpu className="w-5 h-5 text-primary" />
          </div>
          <h3 className="text-base font-bold text-foreground uppercase tracking-wide">About Spectra-Scan</h3>
        </div>
        <p className="text-sm text-muted-foreground leading-relaxed mb-4">
          Spectra-Scan is an advanced automated inspection system developed by the <span className="text-primary font-semibold">CON-SOL-E club</span>.
          It utilizes cutting-edge computer vision and machine learning algorithms for real-time defect detection.
          The system features a precision gantry mechanism with high-resolution imaging capabilities, specifically
          designed for industrial quality control applications.
        </p>
        <div className="grid grid-cols-2 gap-3 mb-4">
          <div className="bg-secondary/40 rounded-lg p-3 border border-border">
            <div className="text-xs text-muted-foreground mb-1 uppercase tracking-wide">Resolution</div>
            <div className="text-base font-bold text-foreground">4K Ultra HD</div>
          </div>
          <div className="bg-secondary/40 rounded-lg p-3 border border-border">
            <div className="text-xs text-muted-foreground mb-1 uppercase tracking-wide">Processing Speed</div>
            <div className="text-base font-bold text-foreground">60 FPS</div>
          </div>
        </div>

        {/* MECUP Competition Badge */}
        <div className="mt-6 pt-4 border-t border-border">
          <div className="flex items-center gap-3 bg-secondary/30 rounded-lg p-3 border border-border">
            <img
              src="/assets/MECUP_logo.png"
              alt="MECUP Competition"
              className="h-12 w-12 object-contain flex-shrink-0"
            />
            <div>
              <div className="text-xs text-muted-foreground uppercase tracking-wide">Competition</div>
              <div className="text-sm font-bold text-foreground">MECUP</div>
            </div>
          </div>
        </div>
      </div>

      {/* Bottom-Left: Key Features (spans 2 columns) */}
      <div className="col-span-2 row-span-0.5 industrial-panel p-6 overflow-y-auto">
        <div className="flex items-center gap-3 mb-6">
          <div className="w-12 h-12 rounded-lg bg-primary/10 flex items-center justify-center border border-primary/20 flex-shrink-0">
            <Zap className="w-6 h-6 text-primary" />
          </div>
          <h3 className="text-base font-bold text-foreground uppercase tracking-wide">Key Features</h3>
        </div>
        <div className="space-y-5">
          <InfoCard
            title="Real-time Detection"
            description="Instant defect identification with AI-powered analysis and pattern recognition for enhanced quality control"
            icon={Shield}
          />
          <InfoCard
            title="Automated Workflow"
            description="Seamless integration with production line systems enabling continuous monitoring and automated reporting"
            icon={Award}
          />
          <InfoCard
            title="Precision Gantry System"
            description="High-accuracy positioning mechanism ensuring consistent and repeatable inspection results"
            icon={Target}
          />
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
