import {
  createContext,
  useContext,
  useEffect,
  useState,
  type ReactNode,
} from "react";
import {
  api,
  clearToken,
  getToken,
  SESION_EXPIRADA,
  setToken,
} from "../api/client";
import type { Rol, Usuario } from "../api/types";

interface AuthState {
  usuario: Usuario | null;
  token: string | null;
  loaded: boolean;
  login: (username: string, password: string) => Promise<void>;
  ingresarDemo: (rol: Rol) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthState | null>(null);

interface LoginResponse {
  access_token: string;
  usuario: Usuario;
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [token, setTokenState] = useState<string | null>(getToken());
  const [usuario, setUsuario] = useState<Usuario | null>(null);
  const [loaded, setLoaded] = useState(false);

  useEffect(() => {
    if (!token) {
      setLoaded(true);
      return;
    }
    api
      .get<Usuario>("/auth/me")
      .then(setUsuario)
      .catch(() => {
        clearToken();
        setTokenState(null);
        setUsuario(null);
      })
      .finally(() => setLoaded(true));
  }, [token]);

  useEffect(() => {
    const handler = () => {
      setTokenState(null);
      setUsuario(null);
    };
    window.addEventListener(SESION_EXPIRADA, handler);
    return () => window.removeEventListener(SESION_EXPIRADA, handler);
  }, []);

  const aplicarSesion = (res: LoginResponse) => {
    setToken(res.access_token);
    setTokenState(res.access_token);
    setUsuario(res.usuario);
  };

  const login = async (username: string, password: string) => {
    aplicarSesion(await api.post<LoginResponse>("/auth/login", { username, password }));
  };

  const ingresarDemo = async (rol: Rol) => {
    aplicarSesion(await api.post<LoginResponse>("/auth/demo/login", { rol }));
  };

  const logout = () => {
    clearToken();
    setTokenState(null);
    setUsuario(null);
  };

  return (
    <AuthContext.Provider value={{ usuario, token, loaded, login, ingresarDemo, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthState {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth debe usarse dentro de AuthProvider");
  return ctx;
}