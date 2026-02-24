import { lazy, Suspense } from "react";
import { Routes, Route, Navigate } from "react-router-dom";
import { Layout } from "./components/Layout";
import { Login } from "./pages/Login";
import { useAuth } from "./hooks/useAuth";

// Lazy-loaded pages — Vite creates separate chunks automatically
const Dashboard = lazy(() => import("./pages/Dashboard").then(m => ({ default: m.Dashboard })));
const PortfolioPage = lazy(() => import("./pages/Portfolio").then(m => ({ default: m.PortfolioPage })));
const MarketAnalysis = lazy(() => import("./pages/MarketAnalysis").then(m => ({ default: m.MarketAnalysis })));
const Trading = lazy(() => import("./pages/Trading").then(m => ({ default: m.Trading })));
const DataManagement = lazy(() => import("./pages/DataManagement").then(m => ({ default: m.DataManagement })));
const Screening = lazy(() => import("./pages/Screening").then(m => ({ default: m.Screening })));
const RiskManagement = lazy(() => import("./pages/RiskManagement").then(m => ({ default: m.RiskManagement })));
const Backtesting = lazy(() => import("./pages/Backtesting").then(m => ({ default: m.Backtesting })));
const RegimeDashboard = lazy(() => import("./pages/RegimeDashboard").then(m => ({ default: m.RegimeDashboard })));
const PaperTrading = lazy(() => import("./pages/PaperTrading").then(m => ({ default: m.PaperTrading })));
const Settings = lazy(() => import("./pages/Settings").then(m => ({ default: m.Settings })));
const MLModels = lazy(() => import("./pages/MLModels").then(m => ({ default: m.MLModels })));
const Scheduler = lazy(() => import("./pages/Scheduler").then(m => ({ default: m.Scheduler })));
const Workflows = lazy(() => import("./pages/Workflows").then(m => ({ default: m.Workflows })));

function PageLoader() {
  return (
    <div className="flex h-64 items-center justify-center">
      <div className="text-[var(--color-text-muted)]">Loading...</div>
    </div>
  );
}

export default function App() {
  const { isAuthenticated, isLoading, login, logout, username } = useAuth();

  if (isLoading) {
    return (
      <div className="flex h-screen items-center justify-center bg-[var(--color-bg)]">
        <div className="text-[var(--color-text-muted)]">Loading...</div>
      </div>
    );
  }

  return (
    <Routes>
      <Route
        path="/login"
        element={
          isAuthenticated ? (
            <Navigate to="/" replace />
          ) : (
            <Login onLogin={login} />
          )
        }
      />
      <Route
        element={
          isAuthenticated ? (
            <Layout onLogout={logout} username={username} />
          ) : (
            <Navigate to="/login" replace />
          )
        }
      >
        <Route path="/" element={<Suspense fallback={<PageLoader />}><Dashboard /></Suspense>} />
        <Route path="/portfolio" element={<Suspense fallback={<PageLoader />}><PortfolioPage /></Suspense>} />
        <Route path="/market" element={<Suspense fallback={<PageLoader />}><MarketAnalysis /></Suspense>} />
        <Route path="/trading" element={<Suspense fallback={<PageLoader />}><Trading /></Suspense>} />
        <Route path="/data" element={<Suspense fallback={<PageLoader />}><DataManagement /></Suspense>} />
        <Route path="/screening" element={<Suspense fallback={<PageLoader />}><Screening /></Suspense>} />
        <Route path="/risk" element={<Suspense fallback={<PageLoader />}><RiskManagement /></Suspense>} />
        <Route path="/regime" element={<Suspense fallback={<PageLoader />}><RegimeDashboard /></Suspense>} />
        <Route path="/backtest" element={<Suspense fallback={<PageLoader />}><Backtesting /></Suspense>} />
        <Route path="/paper-trading" element={<Suspense fallback={<PageLoader />}><PaperTrading /></Suspense>} />
        <Route path="/ml" element={<Suspense fallback={<PageLoader />}><MLModels /></Suspense>} />
        <Route path="/scheduler" element={<Suspense fallback={<PageLoader />}><Scheduler /></Suspense>} />
        <Route path="/workflows" element={<Suspense fallback={<PageLoader />}><Workflows /></Suspense>} />
        <Route path="/settings" element={<Suspense fallback={<PageLoader />}><Settings /></Suspense>} />
      </Route>
    </Routes>
  );
}
