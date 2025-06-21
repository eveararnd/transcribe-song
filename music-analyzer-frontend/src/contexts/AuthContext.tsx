import React, { createContext, useState, useContext, useCallback, ReactNode } from 'react';

interface AuthContextType {
  isAuthenticated: boolean;
  username: string | null;
  password: string | null;
  login: (username: string, password: string) => void;
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

  const login = useCallback((username: string, password: string) => {
    setUsername(username);
    setPassword(password);
    setIsAuthenticated(true);
    // Store in sessionStorage for persistence during session
    sessionStorage.setItem('auth', JSON.stringify({ username, password }));
  }, []);

  const logout = useCallback(() => {
    setUsername(null);
    setPassword(null);
    setIsAuthenticated(false);
    sessionStorage.removeItem('auth');
  }, []);

  const getAuthHeader = useCallback(() => {
    if (username && password) {
      return 'Basic ' + btoa(`${username}:${password}`);
    }
    return '';
  }, [username, password]);

  // Check for existing auth on mount
  React.useEffect(() => {
    const authData = sessionStorage.getItem('auth');
    if (authData) {
      const { username, password } = JSON.parse(authData);
      login(username, password);
    }
  }, [login]);

  return (
    <AuthContext.Provider
      value={{
        isAuthenticated,
        username,
        password,
        login,
        logout,
        getAuthHeader,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};