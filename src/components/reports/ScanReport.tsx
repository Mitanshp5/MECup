import React from "react";
import PrintableReport from "./PrintableReport";
import type { ScanDetails } from "./PrintableReport";

// Re-export the interface so PastScans.tsx can still import from here
export type { ScanDetails };

interface ScanReportProps {
    scan: ScanDetails;
    onBack: () => void;
}

const ScanReport: React.FC<ScanReportProps> = ({ scan, onBack }) => {
    return <PrintableReport scan={scan} onBack={onBack} />;
};

export default ScanReport;
