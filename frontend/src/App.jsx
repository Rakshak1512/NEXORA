import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import { ThemeProvider } from './context/ThemeContext';
import { WebSocketProvider } from './context/WebSocketContext';

// Layout
import DashboardLayout from './components/layout/DashboardLayout';

// Public Pages
import LandingPage from './pages/LandingPage';
import Login from './pages/Login';
import Register from './pages/Register';
import ForgotPassword from './pages/ForgotPassword';
import NotFound from './pages/NotFound';

// Protected Views
import OverviewDashboard from './pages/OverviewDashboard';
import CollectorsView from './pages/CollectorsView';
import InfrastructureView from './pages/InfrastructureView';
import NetworkMonitoringView from './pages/NetworkMonitoringView';
import SecurityMonitoringView from './pages/SecurityMonitoringView';
import EgressProofCenter from './pages/EgressProofCenter';
import AIOpsIntelligenceView from './pages/AIOpsIntelligenceView';
import IncidentsView from './pages/IncidentsView';
import AIRecommendationsView from './pages/AIRecommendationsView';
import ApprovalCenterView from './pages/ApprovalCenterView';
import GlobalOperationsView from './pages/GlobalOperationsView';
import AnalyticsView from './pages/AnalyticsView';
import AuditLogsView from './pages/AuditLogsView';
import ScenarioControlView from './pages/ScenarioControlView';
import SettingsView from './pages/SettingsView';

const ProtectedRoute = ({ children }) => {
  const { user, loading } = useAuth();
  if (loading) {
    return (
      <div className="min-h-screen bg-[#070C14] flex items-center justify-center text-cyan-400 font-mono text-sm">
        Authenticating session...
      </div>
    );
  }
  // If not logged in, we still allow demo browsing or redirect to login
  // In enterprise demo mode, allow access if token exists or redirect
  const token = localStorage.getItem('cicada_token');
  if (!user && !token) {
    return <Navigate to="/login" replace />;
  }
  return children;
};

function App() {
  return (
    <ThemeProvider>
      <AuthProvider>
        <WebSocketProvider>
          <BrowserRouter>
            <Routes>
              {/* Public Routes */}
              <Route path="/" element={<LandingPage />} />
              <Route path="/login" element={<Login />} />
              <Route path="/register" element={<Register />} />
              <Route path="/forgot-password" element={<ForgotPassword />} />

              {/* Protected Operational Dashboard */}
              <Route element={<ProtectedRoute><DashboardLayout /></ProtectedRoute>}>
                <Route path="/dashboard" element={<OverviewDashboard />} />
                <Route path="/collectors" element={<CollectorsView />} />
                <Route path="/infrastructure" element={<InfrastructureView />} />
                <Route path="/network" element={<NetworkMonitoringView />} />
                <Route path="/security" element={<SecurityMonitoringView />} />
                <Route path="/egress-proof" element={<EgressProofCenter />} />
                <Route path="/aiops" element={<AIOpsIntelligenceView />} />
                <Route path="/incidents" element={<IncidentsView />} />
                <Route path="/recommendations" element={<AIRecommendationsView />} />
                <Route path="/approvals" element={<ApprovalCenterView />} />
                <Route path="/global" element={<GlobalOperationsView />} />
                <Route path="/analytics" element={<AnalyticsView />} />
                <Route path="/audit-logs" element={<AuditLogsView />} />
                <Route path="/scenarios" element={<ScenarioControlView />} />
                <Route path="/settings" element={<SettingsView />} />
              </Route>

              {/* 404 Catch-All */}
              <Route path="*" element={<NotFound />} />
            </Routes>
          </BrowserRouter>
        </WebSocketProvider>
      </AuthProvider>
    </ThemeProvider>
  );
}

export default App;

