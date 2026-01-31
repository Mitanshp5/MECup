import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { Search, Filter, Download, Eye, Calendar, User, CheckCircle, AlertTriangle, X, Image as ImageIcon } from "lucide-react";

interface ScanRecord {
  id: string;
  date: string;
  time: string;
  image_count: number;
  defect_count: number;
  status: "pass" | "fail";
}

interface ScanDetails {
  id: string;
  date: string;
  time: string;
  image_count: number;
  images: string[];
  total_defects: number;
  defect_types: { [key: string]: number };
  defects: {
    image: string;
    overlay: string;
    overlay_url: string;
    defect_count?: number;
    defect_details?: { type: string; pixel_count: number; area_ratio: number }[];
  }[];
  status: "pass" | "fail";
}

const PastScans = () => {
  const [scans, setScans] = useState<ScanRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState("");
  const [selectedScan, setSelectedScan] = useState<ScanDetails | null>(null);
  const [selectedImage, setSelectedImage] = useState<string | null>(null);

  const [showFullDetails, setShowFullDetails] = useState(false);

  // Fetch scans on mount
  useEffect(() => {
    const fetchScans = async () => {
      try {
        const res = await fetch("http://localhost:5001/scans/list");
        const data = await res.json();
        setScans(data.scans || []);
      } catch (e) {
        console.error("Failed to fetch scans:", e);
      } finally {
        setLoading(false);
      }
    };
    fetchScans();
  }, []);

  // Fetch scan details when selected
  const handleSelectScan = async (scanId: string) => {
    try {
      const res = await fetch(`http://localhost:5001/scans/${scanId}`);
      const data = await res.json();
      setSelectedScan(data);
      setShowFullDetails(false); // Reset to list view when selecting new scan
    } catch (e) {
      console.error("Failed to fetch scan details:", e);
    }
  };

  const filteredScans = scans.filter(scan =>
    scan.id.toLowerCase().includes(searchTerm.toLowerCase()) ||
    scan.date.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="h-full grid grid-cols-12 gap-6">
      {/* Main Content Area (List or Details) */}
      <div className="col-span-8 industrial-panel flex flex-col h-full overflow-hidden">
        {!showFullDetails ? (
          <>
            {/* Header */}
            <div className="p-4 border-b border-border flex-shrink-0">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-foreground">Scan History</h3>
              </div>

              <div className="flex gap-3">
                <div className="flex-1 relative">
                  <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                  <input
                    type="text"
                    placeholder="Search by ID or date..."
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
              {loading ? (
                <div className="p-8 text-center text-muted-foreground">Loading scans...</div>
              ) : filteredScans.length === 0 ? (
                <div className="p-8 text-center text-muted-foreground">No scans found</div>
              ) : (
                <table className="w-full">
                  <thead className="sticky top-0 bg-card z-10">
                    <tr className="border-b border-border">
                      <th className="text-left p-4 text-xs font-medium text-muted-foreground uppercase">Scan ID</th>
                      <th className="text-left p-4 text-xs font-medium text-muted-foreground uppercase">Date/Time</th>
                      <th className="text-left p-4 text-xs font-medium text-muted-foreground uppercase">Images</th>
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
                        className={`border-b border-border/50 hover:bg-secondary/30 cursor-pointer transition-colors ${selectedScan?.id === scan.id ? "bg-primary/5" : ""
                          }`}
                        onClick={() => handleSelectScan(scan.id)}
                      >
                        <td className="p-4 font-mono text-sm text-foreground">{scan.id}</td>
                        <td className="p-4">
                          <div className="text-sm text-foreground">{scan.date}</div>
                          <div className="text-xs text-muted-foreground font-mono">{scan.time}</div>
                        </td>
                        <td className="p-4 font-mono text-sm text-foreground">{scan.image_count}</td>
                        <td className="p-4">
                          <span className={`font-mono text-sm ${scan.defect_count > 0 ? "text-warning" : "text-success"}`}>
                            {scan.defect_count}
                          </span>
                        </td>
                        <td className="p-4">
                          <span className={`inline-flex items-center gap-1.5 px-2 py-1 rounded text-xs font-medium ${scan.status === "pass"
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
                          <button
                            className="p-2 hover:bg-secondary rounded-md transition-colors"
                            onClick={(e) => {
                              e.stopPropagation();
                              handleSelectScan(scan.id);
                            }}
                          >
                            <Eye className="w-4 h-4 text-muted-foreground" />
                          </button>
                        </td>
                      </motion.tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>
          </>
        ) : (
          // Detailed View (Replaces List)
          <div className="flex flex-col h-full">
            <div className="p-4 border-b border-border flex items-center gap-4 flex-shrink-0">
              <button
                onClick={() => setShowFullDetails(false)}
                className="p-2 hover:bg-secondary rounded-full transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
              <h3 className="text-lg font-semibold text-foreground">Scan Details: {selectedScan?.id}</h3>
            </div>

            <div className="flex-1 overflow-y-auto p-4 space-y-6">
              {/* Defects Section */}
              <div>
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-sm font-medium text-muted-foreground">DEFECTS FOUND</h3>
                  <span className={`px-2 py-1 rounded text-xs font-medium ${selectedScan!.total_defects > 0 ? "bg-destructive/10 text-destructive" : "bg-success/10 text-success"}`}>
                    {selectedScan!.total_defects}
                  </span>
                </div>

                {selectedScan!.total_defects > 0 ? (
                  <div className="grid grid-cols-6 gap-3">
                    {selectedScan!.defects.map((defect, i) => (
                      <button
                        key={i}
                        onClick={() => setSelectedImage(`http://localhost:5001${defect.overlay_url}`)}
                        className="aspect-square bg-secondary rounded border border-border hover:border-primary/50 overflow-hidden relative group"
                      >
                        <img
                          src={`http://localhost:5001${defect.overlay_url}`}
                          alt={defect.image}
                          className="w-full h-full object-cover"
                        />
                        <div className="absolute top-1 right-1">
                          <span className="flex items-center justify-center w-5 h-5 bg-black/60 rounded-full backdrop-blur-sm">
                            <AlertTriangle className="w-3 h-3 text-warning" />
                          </span>
                        </div>
                        <div className="absolute inset-x-0 bottom-0 p-1 bg-black/60 backdrop-blur-sm text-[10px] text-white truncate opacity-0 group-hover:opacity-100 transition-opacity">
                          {defect.defect_count || 1} defect(s)
                        </div>
                      </button>
                    ))}
                  </div>
                ) : (
                  <div className="text-center py-6 border border-dashed border-border rounded-lg">
                    <CheckCircle className="w-12 h-12 text-success mx-auto mb-2" />
                    <p className="text-sm text-success">No defects detected</p>
                  </div>
                )}
              </div>

              {/* Images Section */}
              {selectedScan!.images.length > 0 && (
                <div>
                  <h3 className="text-sm font-medium text-muted-foreground mb-3">CAPTURED IMAGES</h3>
                  <div className="grid grid-cols-6 gap-3">
                    {selectedScan!.images.map((img, i) => (
                      <button
                        key={i}
                        onClick={() => setSelectedImage(`http://localhost:5001/scans/${selectedScan!.id}/image/${img}`)}
                        className="aspect-square bg-secondary rounded border border-border hover:border-primary/50 overflow-hidden"
                      >
                        <img
                          src={`http://localhost:5001/scans/${selectedScan!.id}/image/${img}`}
                          alt={img}
                          className="w-full h-full object-cover"
                        />
                      </button>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Right Sidebar - Summary Only */}
      <div className="col-span-4 h-full flex flex-col overflow-hidden">
        {selectedScan ? (
          <div className="space-y-4">
            <div className="industrial-panel p-4">
              <h3 className="text-sm font-medium text-muted-foreground mb-4">SCAN DETAILS</h3>
              <div className="space-y-3">
                <div className="flex justify-between text-sm">
                  <span className="text-muted-foreground">Scan ID</span>
                  <span className="font-mono text-foreground text-xs">{selectedScan.id}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-muted-foreground">Date</span>
                  <span className="font-mono text-foreground">{selectedScan.date}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-muted-foreground">Time</span>
                  <span className="font-mono text-foreground">{selectedScan.time}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-muted-foreground">Total Images</span>
                  <span className="font-mono text-foreground">{selectedScan.image_count}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-muted-foreground">Status</span>
                  <span className={`font-medium ${selectedScan.status === "pass" ? "text-success" : "text-destructive"}`}>
                    {selectedScan.status.toUpperCase()}
                  </span>
                </div>
              </div>
            </div>

            {!showFullDetails && (
              <button
                onClick={() => setShowFullDetails(true)}
                className="w-full py-3 bg-primary text-primary-foreground rounded-md font-medium hover:bg-primary/90 transition-all shadow-lg flex items-center justify-center gap-2"
              >
                <Eye className="w-4 h-4" />
                View Full Details
              </button>
            )}

            {/* Defect Types Breakdown (Small summary) */}
            {Object.keys(selectedScan.defect_types).length > 0 && (
              <div className="industrial-panel p-4">
                <h3 className="text-sm font-medium text-muted-foreground mb-3">DEFECT SUMMARY</h3>
                <div className="flex flex-wrap gap-2">
                  {Object.entries(selectedScan.defect_types).map(([type, count]) => (
                    <span key={type} className="px-2 py-1 bg-warning/10 text-warning text-xs rounded border border-warning/20">
                      {type}: {count}
                    </span>
                  ))}
                </div>
              </div>
            )}

          </div>
        ) : (
          <div className="industrial-panel p-6 text-center">
            <Calendar className="w-12 h-12 text-muted-foreground mx-auto mb-3" />
            <p className="text-muted-foreground">Select a scan to view details</p>
          </div>
        )}
      </div>

      {/* Image Modal */}
      {selectedImage && (
        <div
          className="fixed inset-0 bg-black/80 z-50 flex items-center justify-center p-8"
          onClick={() => setSelectedImage(null)}
        >
          <div className="relative max-w-4xl max-h-full">
            <button
              onClick={() => setSelectedImage(null)}
              className="absolute -top-10 right-0 p-2 text-white hover:text-primary transition-colors"
            >
              <X className="w-6 h-6" />
            </button>
            <img
              src={selectedImage}
              className="max-w-full max-h-[80vh] object-contain rounded-lg"
              alt="Scan Image"
            />
          </div>
        </div>
      )}
    </div>
  );
};

export default PastScans;
