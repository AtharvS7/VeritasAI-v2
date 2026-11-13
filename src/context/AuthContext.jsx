import { createContext, useContext, useEffect, useMemo, useState } from 'react';
import { authRequest } from '../lib/api';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const existingToken = localStorage.getItem('veritasai_token');
    if (!existingToken) { setLoading(false); return; }
    authRequest('me').then(setUser).catch(() => localStorage.removeItem('veritasai_token')).finally(() => setLoading(false));
  }, []);

  const signIn = async (email, password) => {
    const data = await authRequest('login', { email, password });
    localStorage.setItem('veritasai_token', data.token);
    setUser(data.user);
    return data.user;
  };
  const signUp = async (fullName, email, password) => {
    const data = await authRequest('signup', { fullName, email, password });
    localStorage.setItem('veritasai_token', data.token);
    setUser(data.user);
    return data.user;
  };
  const signOut = () => {
    localStorage.removeItem('veritasai_token');
    setUser(null);
  };
  const value = useMemo(() => ({ user, loading, signIn, signUp, signOut }), [user, loading]);
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export const useAuth = () => useContext(AuthContext);
