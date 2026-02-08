import { Canvas } from "@react-three/fiber";
import { OrbitControls, PerspectiveCamera, useGLTF, Html, Center } from "@react-three/drei";
import { motion } from "framer-motion";
import { Activity, TrendingUp, Shield, Zap, Award, Users, Target, Cpu, Loader2 } from "lucide-react";
import { Suspense } from "react";
import { useAuth } from "@/context/AuthContext";

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


const GLBModel = () => {
  const { scene } = useGLTF("/assets/DoorChecker.glb");

  return (
    <Center>
      <primitive
        object={scene}
        scale={1}
        position={[0, 0, 0]}
      />
    </Center>
  );
};

type ColorKey = "primary" | "success" | "muted";

const colorStyles = {
  primary: {
    bg: "bg-primary/10",
    text: "text-primary",
    border: "border-primary/20",
  },
  success: {
    bg: "bg-success/10",
    text: "text-success",
    border: "border-success/30",
  },
  muted: {
    bg: "bg-muted",
    text: "text-muted-foreground",
    border: "border-border",
  },
};

const MetricCard = ({ title, value, trend, icon: Icon, color = "primary" }: {
  title: string;
  value: string;
  trend?: string;
  icon: React.ElementType;
  color?: ColorKey;
}) => {
  const styles = colorStyles[color] || colorStyles.primary;

  return (
    <motion.div
      whileHover={{ scale: 1.02, y: -2 }}
      className="industrial-panel p-5 transition-all hover:border-primary/50"
    >
      <div className="flex items-start justify-between mb-3">
        <div className={`w-11 h-11 rounded-lg ${styles.bg} flex items-center justify-center border ${styles.border}`}>
          <Icon className={`w-6 h-6 ${styles.text}`} />
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
};

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

const Dashboard = () => {
  const { user } = useAuth();
  return (
    <div className="h-full grid grid-cols-3 grid-rows-2 gap-6">
      {/* Left Side: 3D Model Viewer (spans 2 rows) */}
      <div className="col-span-2 row-span-2 industrial-panel overflow-hidden relative">
        <div className="absolute top-4 left-4 z-10">
          <h3 className="text-sm font-medium text-muted-foreground mb-1">MACHINE VIEW</h3>
          <p className="text-xs text-muted-foreground font-mono">Spectra-Scan</p>
        </div>

        <Canvas className="w-full h-full">
          <PerspectiveCamera makeDefault position={[2.5, 2.0, 2.5]} />
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

      {/* Right Side: About Spectra-Scan (spans 2 rows now) */}
      <div className="industrial-panel p-6 flex flex-col justify-between overflow-hidden relative group row-span-2">
        <div className="absolute inset-0 bg-gradient-to-br from-primary/5 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500" />

        <div className="flex-1 flex flex-col">
          <div className="flex items-center gap-3 mb-6">
            <div className="w-12 h-12 rounded-lg bg-primary/10 flex items-center justify-center border border-primary/20 flex-shrink-0 shadow-[0_0_15px_rgba(var(--primary),0.15)]">
              <Cpu className="w-6 h-6 text-primary" />
            </div>
            <h3 className="text-lg font-bold text-foreground uppercase tracking-wide">About Spectra-Scan</h3>
          </div>

          <p className="text-base text-muted-foreground leading-relaxed mb-8">
            Spectra-Scan is an advanced automated inspection system developed by the <span className="text-primary font-semibold">Team CON-SOL-E</span>.
            The system features a precision gantry mechanism with high-resolution imaging capabilities, specifically
            designed for industrial quality control applications.
          </p>
        </div>

        {/* MECUP Competition Badge */}
        <div className="mt-6 pt-6 border-t border-border/50">
          <div className="flex items-center gap-4 bg-secondary/30 rounded-xl p-4 border border-border hover:border-primary/30 transition-colors">
            <img
              src="/assets/MECUP_logo.png"
              alt="MECUP Competition"
              className="h-16 w-16 object-contain flex-shrink-0"
            />
            <div>
              <div className="text-xs text-muted-foreground uppercase tracking-wide font-medium mb-1">Competition</div>
              <div className="text-3xl font-bold text-foreground tracking-tight">MECUP</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
