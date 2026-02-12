import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { HashRouter, Routes, Route, Navigate } from "react-router-dom";
import { ThemeProvider } from "@/components/theme-provider";
import NotFound from "./pages/NotFound";
import AppLayout from "@/components/layout/AppLayout";
import Dashboard from "@/pages/Dashboard";
import AutomaticMode from "@/pages/AutomaticMode";
import ManualMode from "@/pages/ManualMode";
import SettingsPage from "@/pages/SettingsPage";
import PastScans from "@/pages/PastScans";
import UserManagement from "@/pages/UserManagement";
import HeartbeatPage from "@/pages/HeartbeatPage";
import MobileHealthPage from "@/pages/MobileHealthPage";
import MobileDashboard from "@/pages/MobileDashboard";
import MobileReportPage from "@/pages/MobileReportPage";
import MobileLoginPage from "@/pages/MobileLoginPage";
import MobileProtectedRoute from "@/components/MobileProtectedRoute";
import MobileRedirect from "@/components/MobileRedirect";

import { AuthProvider } from "@/context/AuthContext";
import ProtectedRoute from "@/components/ProtectedRoute";

const queryClient = new QueryClient();

const App = () => (
  <ThemeProvider defaultTheme="dark" storageKey="mecup-theme">
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <TooltipProvider>
          <Toaster />
          <Sonner />
          <HashRouter>
            <Routes>
              <Route element={<AppLayout />}>
                <Route path="/" element={
                  <MobileRedirect>
                    <Dashboard />
                  </MobileRedirect>
                } />

                <Route path="/automatic" element={
                  <ProtectedRoute allowedRoles={['admin', 'operator']}>
                    <AutomaticMode />
                  </ProtectedRoute>
                } />

                <Route path="/manual" element={
                  <ProtectedRoute allowedRoles={['admin', 'operator']}>
                    <ManualMode />
                  </ProtectedRoute>
                } />

                <Route path="/settings" element={
                  <ProtectedRoute allowedRoles={['admin']}>
                    <SettingsPage />
                  </ProtectedRoute>
                } />

                <Route path="/scans" element={
                  <ProtectedRoute allowedRoles={['admin', 'operator', 'viewer']}>
                    <PastScans />
                  </ProtectedRoute>
                } />

                <Route path="/users" element={
                  <ProtectedRoute allowedRoles={['admin']}>
                    <UserManagement />
                  </ProtectedRoute>
                } />

                <Route path="/heartbeat" element={
                  <ProtectedRoute allowedRoles={['admin', 'operator', 'viewer']}>
                    <HeartbeatPage />
                  </ProtectedRoute>
                } />

                {/* Fallback for old routes or typos */}
                <Route path="/dashboard" element={<Navigate to="/" replace />} />
              </Route>

              {/* Standalone Mobile Pages - Not in sidebar */}
              <Route path="/mobile/login" element={<MobileLoginPage />} />

              <Route path="/mobile" element={
                <MobileProtectedRoute>
                  <MobileDashboard />
                </MobileProtectedRoute>
              } />
              <Route path="/mobile/health" element={
                <MobileProtectedRoute>
                  <MobileHealthPage />
                </MobileProtectedRoute>
              } />
              <Route path="/mobile/report" element={
                <MobileProtectedRoute>
                  <MobileReportPage />
                </MobileProtectedRoute>
              } />

              <Route path="*" element={<NotFound />} />
            </Routes>
          </HashRouter>
        </TooltipProvider>
      </AuthProvider>
    </QueryClientProvider>
  </ThemeProvider>
);

export default App;

