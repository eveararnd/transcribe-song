import React, { createContext, useState, useContext, useCallback, ReactNode } from 'react';
import { cookieUtils } from '../utils/cookieUtils';

interface AuthContextType {
  isAuthenticated: boolean;
  username: string | null;
  password: string | null;
  isUsingCookie: boolean;
  login: (username: string, password: string, rememberMe?: boolean) => void;
  logout: () => void;
  getAuthHeader: () => string;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

interface AuthProviderProps {
  children: ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [username, setUsername] = useState<string | null>(null);
  const [password, setPassword] = useState<string | null>(null);
  const [isUsingCookie, setIsUsingCookie] = useState(false);

  const login = useCallback((username: string, password: string, rememberMe: boolean = true) => {
    setUsername(username);
    setPassword(password);
    setIsAuthenticated(true);
    setIsUsingCookie(rememberMe);
    // Store in cookie for persistence (2 weeks) if rememberMe is true
    if (rememberMe) {
      cookieUtils.setAuthCookie(username, password);
    }
    // Always keep in sessionStorage for current session
    sessionStorage.setItem('auth', JSON.stringify({ username, password }));
  }, []);

  const logout = useCallback(() => {
    setUsername(null);
    setPassword(null);
    setIsAuthenticated(false);
    setIsUsingCookie(false);
    // Remove from both cookie and sessionStorage
    cookieUtils.removeAuthCookie();
    sessionStorage.removeItem('auth');
  }, []);

  const getAuthHeader = useCallback(() => {
    if (username && password) {
      return 'Basic ' + btoa(`${username}:${password}`);
    }
    return '';
  }, [username, password]);

  // Check for existing auth on mount (first try cookie, then sessionStorage)
  React.useEffect(() => {
    // First try to get auth from cookie
    const cookieAuth = cookieUtils.getAuthCookie();
    if (cookieAuth) {
      setUsername(cookieAuth.username);
      setPassword(cookieAuth.password);
      setIsAuthenticated(true);
      setIsUsingCookie(true);
      // Also sync to sessionStorage
      sessionStorage.setItem('auth', JSON.stringify(cookieAuth));
      return;
    }
    
    // Fall back to sessionStorage for backward compatibility
    const authData = sessionStorage.getItem('auth');
    if (authData) {
      const { username, password } = JSON.parse(authData);
      setUsername(username);
      setPassword(password);
      setIsAuthenticated(true);
      setIsUsingCookie(false);
    }
  }, []);

  return (
    <AuthContext.Provider
      value={{
        isAuthenticated,
        username,
        password,
        isUsingCookie,
        login,
        logout,
        getAuthHeader,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};