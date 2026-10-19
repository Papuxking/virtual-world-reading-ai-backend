import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { getToken, getStoredUser } from './services/api';
import { WorkspaceProvider } from './context/WorkspaceContext';
import LoginPage from './pages/LoginPage';
import DashboardLayout from './components/DashboardLayout';
import OverviewPage from './pages/OverviewPage';
import PlayerDetailPage from './pages/PlayerDetailPage';
import AchievementsPage from './pages/AchievementsPage';
import AchievementDetailPage from './pages/AchievementDetailPage';
import MetricsPage from './pages/MetricsPage';

function ProtectedRoute({ children }) {
  const token = getToken();
  const user = getStoredUser();
  if (!token || !user?.is_admin) {
    return <Navigate to="/login" replace />;
  }
  return children;
}

export default function App() {
  return (
    <BrowserRouter basename="/dashboard">
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route
          path="/"
          element={
            <ProtectedRoute>
              <WorkspaceProvider>
                <DashboardLayout />
              </WorkspaceProvider>
            </ProtectedRoute>
          }
        >
          <Route index element={<OverviewPage />} />
          <Route path="players/:playerId" element={<PlayerDetailPage />} />
          <Route path="achievements" element={<AchievementsPage />} />
          <Route path="achievements/:achievementId" element={<AchievementDetailPage />} />
          <Route path="metrics" element={<MetricsPage />} />
        </Route>
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}
