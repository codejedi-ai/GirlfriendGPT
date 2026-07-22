import { createContext, useContext, useEffect, useState, type ReactNode } from "react";
import { api } from "@/lib/api";

export interface DjangoUser {
  id: number;
  email: string;
}

interface AuthState {
  user: DjangoUser | null;
  loading: boolean;
}

interface AuthContextType extends AuthState {
  signUp: (email: string, password: string) => Promise<{ error: string | null }>;
  signIn: (email: string, password: string) => Promise<{ error: string | null }>;
  signOut: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<AuthState>({ user: null, loading: true });

  useEffect(() => {
    if (!localStorage.getItem('access_token')) {
      setState({ user: null, loading: false });
      return;
    }
    api.me().then((user) => setState({ user: user ?? null, loading: false }));
  }, []);

  const signUp = async (email: string, password: string) => {
    const { ok, data } = await api.register(email, password);
    if (!ok) {
      const err = data.email?.[0] || data.password?.[0] || data.detail || 'Registration failed.';
      return { error: err };
    }
    localStorage.setItem('access_token', data.access);
    localStorage.setItem('refresh_token', data.refresh);
    setState({ user: data.user, loading: false });
    return { error: null };
  };

  const signIn = async (email: string, password: string) => {
    const { ok, data } = await api.login(email, password);
    if (!ok) return { error: data.detail || 'Invalid email or password.' };
    localStorage.setItem('access_token', data.access);
    localStorage.setItem('refresh_token', data.refresh);
    setState({ user: data.user, loading: false });
    return { error: null };
  };

  const signOut = async () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    setState({ user: null, loading: false });
  };

  return (
    <AuthContext.Provider value={{ ...state, signUp, signIn, signOut }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
