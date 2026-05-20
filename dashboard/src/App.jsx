import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { useState, useEffect } from 'react';
import { getToken, getStoredUser } from './services/api';
import LoginPage from './pages/LoginPage';
import DashboardLayout from './components/DashboardLayout';
import OverviewPage from './pages/OverviewPage';
import PlayerDetailPage from './pages/PlayerDetailPage';

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
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route
          path="/"
          element={
            <ProtectedRoute>
              <DashboardLayout />
            </ProtectedRoute>
          }
        >
          <Route index element={<OverviewPage />} />
          <Route path="players/:playerId" element={<PlayerDetailPage />} />
        </Route>
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}
