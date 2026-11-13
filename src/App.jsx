import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { useEffect, useState } from 'react';
import { useAuth } from './context/AuthContext';
import Navbar from './components/Navbar';
import AuthModal from './components/AuthModal';
import DetectPage from './pages/DetectPage';
import FeedPage from './pages/FeedPage';
import DatasetPage from './pages/DatasetPage';
import DashboardPage from './pages/DashboardPage';
import HistoryPage from './pages/HistoryPage';

function ProtectedRoute({ children, onSignIn }) {
  const { user, loading } = useAuth();
  useEffect(() => { if (!loading && !user) onSignIn(); }, [loading, user, onSignIn]);
  if (loading) return <div className="page-container"><div className="loading-state">Loading your account…</div></div>;
  if (!user) return <Navigate to="/" replace />;
  return children;
}

function App() {
  const [authOpen, setAuthOpen] = useState(false);
  return (
    <Router>
      <div className="app">
        <Navbar onSignIn={() => setAuthOpen(true)} />
        <main className="main-content">
          <Routes>
            <Route path="/" element={<DetectPage onSignIn={() => setAuthOpen(true)} />} />
            <Route path="/feed" element={<ProtectedRoute onSignIn={() => setAuthOpen(true)}><FeedPage /></ProtectedRoute>} />
            <Route path="/dataset" element={<ProtectedRoute onSignIn={() => setAuthOpen(true)}><DatasetPage /></ProtectedRoute>} />
            <Route path="/dashboard" element={<ProtectedRoute onSignIn={() => setAuthOpen(true)}><DashboardPage /></ProtectedRoute>} />
            <Route path="/history" element={<ProtectedRoute onSignIn={() => setAuthOpen(true)}><HistoryPage /></ProtectedRoute>} />
          </Routes>
        </main>
      </div>
      <AuthModal isOpen={authOpen} onClose={() => setAuthOpen(false)} />
    </Router>
  );
}

export default App;
