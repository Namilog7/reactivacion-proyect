import {
  createContext,
  useContext,
  useEffect,
  useState,
  type ReactNode,
} from "react";
import { api, clearToken, getToken, setToken } from "../api/client";
import type { Usuario } from "../api/types";

interface AuthState {
  usuario: Usuario | null;
  token: string | null;
  loaded: boolean;
  login: (username: string, password: string) => Promise<void>;
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

  const login = async (username: string, password: string) => {
    const res = await api.post<LoginResponse>("/auth/login", { username, password });

      console.log("RESPUESTA LOGIN:", res);
  console.log("ACCESS TOKEN:", res.access_token);

  setToken(res.access_token);

  console.log("TOKEN GUARDADO:", localStorage.getItem("cobranzas_token"));
    setToken(res.access_token);
    setTokenState(res.access_token);
    setUsuario(res.usuario);
  };

  const logout = () => {
    clearToken();
    setTokenState(null);
    setUsuario(null);
  };

  return (
    <AuthContext.Provider value={{ usuario, token, loaded, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthState {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth debe usarse dentro de AuthProvider");
  return ctx;
}