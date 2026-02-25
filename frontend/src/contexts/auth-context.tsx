"use client";

import {
  createContext,
  useContext,
  useEffect,
  useState,
  useCallback,
  type ReactNode,
} from "react";
import type { UserProfile } from "@/types";
import {
  login as authLogin,
  register as authRegister,
  logout as authLogout,
  getMe,
  ensureCsrfToken,
  type LoginCredentials,
  type RegisterData,
} from "@/lib/auth";

interface AuthContextType {
  user: UserProfile | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (credentials: LoginCredentials) => Promise<void>;
  register: (data: RegisterData) => Promise<void>;
  logout: () => Promise<void>;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<UserProfile | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const refreshUser = useCallback(async () => {
    try {
      const userData = await getMe();
      setUser(userData);
    } catch {
      setUser(null);
    }
  }, []);

  // On mount: ensure CSRF token, then try to load user
  useEffect(() => {
    let cancelled = false;
    async function init() {
      try {
        await ensureCsrfToken();
        const userData = await getMe();
        if (!cancelled) setUser(userData);
      } catch {
        if (!cancelled) setUser(null);
      } finally {
        if (!cancelled) setIsLoading(false);
      }
    }
    init();
    return () => {
      cancelled = true;
    };
  }, []);

  const login = useCallback(
    async (credentials: LoginCredentials) => {
      await authLogin(credentials);
      await refreshUser();
    },
    [refreshUser],
  );

  const register = useCallback(
    async (data: RegisterData) => {
      await authRegister(data);
      await refreshUser();
    },
    [refreshUser],
  );

  const logout = useCallback(async () => {
    await authLogout();
    setUser(null);
  }, []);

  return (
    <AuthContext.Provider
      value={{
        user,
        isLoading,
        isAuthenticated: !!user,
        login,
        register,
        logout,
        refreshUser,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
