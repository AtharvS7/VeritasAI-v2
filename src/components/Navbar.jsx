import { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

export default function Navbar({ onSignIn }) {
  const [mobileOpen, setMobileOpen] = useState(false);
  const location = useLocation();
  const { user, signOut } = useAuth();

  const links = [
    { to: '/', label: 'Detect' },
    { to: '/feed', label: 'Trending Claims' },
    { to: '/dataset', label: 'Engines' },
    { to: '/dashboard', label: 'Dashboard' },
    ...(user ? [{ to: '/history', label: 'Your History' }] : []),
  ];

  return (
    <nav className="navbar">
      <div className="navbar-inner">
        <Link to="/" className="navbar-logo" style={{ color: '#fafafa' }}>
          Veritas<span style={{ color: '#f87171' }}>AI</span>
        </Link>

        <div className="navbar-live">
          <span className="live-dot"></span>
          <span className="live-text">LIVE</span>
        </div>

        <div className={`navbar-links ${mobileOpen ? 'open' : ''}`}>
          {links.map(link => (
            <Link
              key={link.to}
              to={link.to}
              className={`nav-link ${location.pathname === link.to ? 'active' : ''}`}
              onClick={() => setMobileOpen(false)}
            >
              {link.label}
            </Link>
          ))}
        </div>

        <div className="navbar-account">
          {user ? <><span className="navbar-user">{user.fullName}</span><button className="nav-auth-btn" onClick={signOut}>Sign out</button></> : <button className="nav-auth-btn" onClick={onSignIn}>Sign in / Sign up</button>}
        </div>

        <button
          className="hamburger"
          onClick={() => setMobileOpen(!mobileOpen)}
          aria-label="Toggle menu"
        >
          <span></span>
          <span></span>
          <span></span>
        </button>
      </div>
    </nav>
  );
}
