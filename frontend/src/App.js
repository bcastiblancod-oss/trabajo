import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Toaster } from 'sonner';
import { AuthProvider, useAuth } from './context/AuthContext';

// Pages
import LoginPage from './pages/LoginPage';
import DashboardPage from './pages/DashboardPage';
import HabitacionesPage from './pages/HabitacionesPage';
import ReservasPage from './pages/ReservasPage';
import CheckinPage from './pages/CheckinPage';
import CheckoutPage from './pages/CheckoutPage';
import PagosPage from './pages/PagosPage';
import FacturasPage from './pages/FacturasPage';
import ReportesPage from './pages/ReportesPage';
import UsuariosPage from './pages/UsuariosPage';

// Layout
import Layout from './components/Layout';

// Protected Route Component
const ProtectedRoute = ({ children, allowedRoles = [] }) => {
  const { isAuthenticated, loading, hasRole } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[#fcfaf8]">
        <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-primary"></div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  if (allowedRoles.length > 0 && !allowedRoles.some(role => hasRole(role))) {
    return <Navigate to="/dashboard" replace />;
  }

  return <Layout>{children}</Layout>;
};

// Public Route Component
const PublicRoute = ({ children }) => {
  const { isAuthenticated, loading } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[#fcfaf8]">
        <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-primary"></div>
      </div>
    );
  }

  if (isAuthenticated) {
    return <Navigate to="/dashboard" replace />;
  }

  return children;
};

function AppRoutes() {
  return (
    <Routes>
      {/* Public Routes */}
      <Route
        path="/login"
        element={
          <PublicRoute>
            <LoginPage />
          </PublicRoute>
        }
      />

      {/* Protected Routes - All authenticated users */}
      <Route
        path="/dashboard"
        element={
          <ProtectedRoute>
            <DashboardPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/habitaciones"
        element={
          <ProtectedRoute>
            <HabitacionesPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/reservas"
        element={
          <ProtectedRoute>
            <ReservasPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/facturas"
        element={
          <ProtectedRoute>
            <FacturasPage />
          </ProtectedRoute>
        }
      />

      {/* Protected Routes - Receptionist & Admin only */}
      <Route
        path="/checkin"
        element={
          <ProtectedRoute allowedRoles={['administrador', 'recepcionista']}>
            <CheckinPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/checkout"
        element={
          <ProtectedRoute allowedRoles={['administrador', 'recepcionista']}>
            <CheckoutPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/pagos"
        element={
          <ProtectedRoute allowedRoles={['administrador', 'recepcionista']}>
            <PagosPage />
          </ProtectedRoute>
        }
      />

      {/* Protected Routes - Admin only */}
      <Route
        path="/reportes"
        element={
          <ProtectedRoute allowedRoles={['administrador']}>
            <ReportesPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/usuarios"
        element={
          <ProtectedRoute allowedRoles={['administrador']}>
            <UsuariosPage />
          </ProtectedRoute>
        }
      />

      {/* Default redirect */}
      <Route path="/" element={<Navigate to="/dashboard" replace />} />
      <Route path="*" element={<Navigate to="/dashboard" replace />} />
    </Routes>
  );
}

function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <AppRoutes />
        <Toaster 
          position="top-right" 
          richColors 
          toastOptions={{
            style: {
              fontFamily: 'Manrope, sans-serif',
            },
          }}
        />
      </AuthProvider>
    </BrowserRouter>
  );
}

export default App;
