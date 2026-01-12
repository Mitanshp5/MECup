import { useState } from "react";
import { motion } from "framer-motion";
import { Search, Filter, Download, Eye, Calendar, User, CheckCircle, AlertTriangle } from "lucide-react";

interface ScanRecord {
  id: string;
  date: string;
  time: string;
  operator: string;
  vehicleId: string;
  defectsFound: number;
  status: "pass" | "fail";
  duration: string;
}

const mockScans: ScanRecord[] = [
  { id: "SCN-001", date: "2024-01-12", time: "10:45:23", operator: "John Smith", vehicleId: "VH-2024-0892", defectsFound: 0, status: "pass", duration: "12m 34s" },
  { id: "SCN-002", date: "2024-01-12", time: "09:32:15", operator: "Jane Doe", vehicleId: "VH-2024-0891", defectsFound: 2, status: "fail", duration: "14m 22s" },
  { id: "SCN-003", date: "2024-01-12", time: "08:15:47", operator: "John Smith", vehicleId: "VH-2024-0890", defectsFound: 0, status: "pass", duration: "11m 58s" },
  { id: "SCN-004", date: "2024-01-11", time: "16:22:33", operator: "Mike Wilson", vehicleId: "VH-2024-0889", defectsFound: 1, status: "fail", duration: "13m 45s" },
  { id: "SCN-005", date: "2024-01-11", time: "14:10:22", operator: "Jane Doe", vehicleId: "VH-2024-0888", defectsFound: 0, status: "pass", duration: "12m 12s" },
  { id: "SCN-006", date: "2024-01-11", time: "11:45:18", operator: "John Smith", vehicleId: "VH-2024-0887", defectsFound: 3, status: "fail", duration: "15m 03s" },
];

const PastScans = () => {
  const [searchTerm, setSearchTerm] = useState("");
  const [selectedScan, setSelectedScan] = useState<ScanRecord | null>(null);

  const filteredScans = mockScans.filter(scan => 
    scan.id.toLowerCase().includes(searchTerm.toLowerCase()) ||
    scan.vehicleId.toLowerCase().includes(searchTerm.toLowerCase()) ||
    scan.operator.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="h-full grid grid-cols-12 gap-6">
      {/* Scan List */}
      <div className="col-span-8 industrial-panel flex flex-col">
        {/* Header */}
        <div className="p-4 border-b border-border">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-foreground">Scan History</h3>
            <button className="flex items-center gap-2 px-4 py-2 bg-secondary text-foreground rounded-md hover:bg-secondary/80 transition-colors">
              <Download className="w-4 h-4" />
              Export
            </button>
          </div>
          
          <div className="flex gap-3">
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
              <input
                type="text"
                placeholder="Search by ID, vehicle, or operator..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full pl-10 pr-4 py-2 bg-secondary border border-border rounded-md text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-primary"
              />
            </div>
            <button className="flex items-center gap-2 px-4 py-2 bg-secondary border border-border rounded-md text-foreground hover:bg-secondary/80 transition-colors">
              <Filter className="w-4 h-4" />
              Filter
            </button>
          </div>
        </div>

        {/* Table */}
        <div className="flex-1 overflow-y-auto">
          <table className="w-full">
            <thead className="sticky top-0 bg-card">
              <tr className="border-b border-border">
                <th className="text-left p-4 text-xs font-medium text-muted-foreground uppercase">Scan ID</th>
                <th className="text-left p-4 text-xs font-medium text-muted-foreground uppercase">Date/Time</th>
                <th className="text-left p-4 text-xs font-medium text-muted-foreground uppercase">Operator</th>
                <th className="text-left p-4 text-xs font-medium text-muted-foreground uppercase">Vehicle</th>
                <th className="text-left p-4 text-xs font-medium text-muted-foreground uppercase">Defects</th>
                <th className="text-left p-4 text-xs font-medium text-muted-foreground uppercase">Status</th>
                <th className="text-left p-4 text-xs font-medium text-muted-foreground uppercase">Actions</th>
              </tr>
            </thead>
            <tbody>
              {filteredScans.map((scan) => (
                <motion.tr
                  key={scan.id}
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  className={`border-b border-border/50 hover:bg-secondary/30 cursor-pointer transition-colors ${
                    selectedScan?.id === scan.id ? "bg-primary/5" : ""
                  }`}
                  onClick={() => setSelectedScan(scan)}
                >
                  <td className="p-4 font-mono text-sm text-foreground">{scan.id}</td>
                  <td className="p-4">
                    <div className="text-sm text-foreground">{scan.date}</div>
                    <div className="text-xs text-muted-foreground font-mono">{scan.time}</div>
                  </td>
                  <td className="p-4 text-sm text-foreground">{scan.operator}</td>
                  <td className="p-4 font-mono text-sm text-foreground">{scan.vehicleId}</td>
                  <td className="p-4">
                    <span className={`font-mono text-sm ${scan.defectsFound > 0 ? "text-warning" : "text-success"}`}>
                      {scan.defectsFound}
                    </span>
                  </td>
                  <td className="p-4">
                    <span className={`inline-flex items-center gap-1.5 px-2 py-1 rounded text-xs font-medium ${
                      scan.status === "pass" 
                        ? "bg-success/10 text-success" 
                        : "bg-destructive/10 text-destructive"
                    }`}>
                      {scan.status === "pass" ? (
                        <CheckCircle className="w-3 h-3" />
                      ) : (
                        <AlertTriangle className="w-3 h-3" />
                      )}
                      {scan.status.toUpperCase()}
                    </span>
                  </td>
                  <td className="p-4">
                    <button className="p-2 hover:bg-secondary rounded-md transition-colors">
                      <Eye className="w-4 h-4 text-muted-foreground" />
                    </button>
                  </td>
                </motion.tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Scan Details */}
      <div className="col-span-4 space-y-4">
        {selectedScan ? (
          <>
            <div className="industrial-panel p-4">
              <h3 className="text-sm font-medium text-muted-foreground mb-4">SCAN DETAILS</h3>
              <div className="space-y-3">
                <div className="flex justify-between text-sm">
                  <span className="text-muted-foreground">Scan ID</span>
                  <span className="font-mono text-foreground">{selectedScan.id}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-muted-foreground">Vehicle ID</span>
                  <span className="font-mono text-foreground">{selectedScan.vehicleId}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-muted-foreground">Duration</span>
                  <span className="font-mono text-foreground">{selectedScan.duration}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-muted-foreground">Status</span>
                  <span className={`font-medium ${selectedScan.status === "pass" ? "text-success" : "text-destructive"}`}>
                    {selectedScan.status.toUpperCase()}
                  </span>
                </div>
              </div>
            </div>

            <div className="industrial-panel p-4">
              <h3 className="text-sm font-medium text-muted-foreground mb-4">OPERATOR INFO</h3>
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-full bg-primary/20 flex items-center justify-center">
                  <User className="w-5 h-5 text-primary" />
                </div>
                <div>
                  <p className="font-medium text-foreground">{selectedScan.operator}</p>
                  <p className="text-xs text-muted-foreground">Quality Inspector</p>
                </div>
              </div>
            </div>

            <div className="industrial-panel p-4">
              <h3 className="text-sm font-medium text-muted-foreground mb-4">DEFECTS FOUND</h3>
              {selectedScan.defectsFound > 0 ? (
                <div className="space-y-2">
                  {Array.from({ length: selectedScan.defectsFound }).map((_, i) => (
                    <div key={i} className="p-3 bg-secondary/50 rounded-md border border-border">
                      <div className="flex items-center gap-2 mb-1">
                        <AlertTriangle className="w-4 h-4 text-warning" />
                        <span className="text-sm font-medium text-foreground">
                          {["Orange Peel", "Dust Nib", "Scratch"][i % 3]}
                        </span>
                      </div>
                      <p className="text-xs text-muted-foreground">Panel: {["Hood", "Door", "Fender"][i % 3]}</p>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-6">
                  <CheckCircle className="w-12 h-12 text-success mx-auto mb-2" />
                  <p className="text-sm text-success">No defects detected</p>
                </div>
              )}
            </div>
          </>
        ) : (
          <div className="industrial-panel p-6 text-center">
            <Calendar className="w-12 h-12 text-muted-foreground mx-auto mb-3" />
            <p className="text-muted-foreground">Select a scan to view details</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default PastScans;
