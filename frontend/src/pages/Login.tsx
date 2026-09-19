import { useEffect, useState, type FormEvent } from "react";
import { useAuth } from "../auth/AuthContext";
import { SESION_EXPIRADA } from "../api/client";
import type { Rol } from "../api/types";
import { ErrorBanner } from "../components/ui";

export function Login() {
  const { login, ingresarDemo } = useAuth();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [demoRol, setDemoRol] = useState<Rol | null>(null);

  useEffect(() => {
    const handler = () => setError("Tu sesión expiró. Volvé a ingresar.");
    window.addEventListener(SESION_EXPIRADA, handler);
    return () => window.removeEventListener(SESION_EXPIRADA, handler);
  }, []);

  const onSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      await login(username, password);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error al iniciar sesión.");
    } finally {
      setLoading(false);
    }
  };

  const entrarDemo = async (rol: Rol) => {
    setError(null);
    setDemoRol(rol);
    try {
      await ingresarDemo(rol);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error al entrar al modo demo.");
    } finally {
      setDemoRol(null);
    }
  };

  return (
    <div className="login-wrap">
      <form className="login-box" onSubmit={onSubmit}>
        <h2>Gestión de Cobranzas</h2>
        <p className="text-muted">Iniciá sesión para continuar.</p>
        <ErrorBanner message={error} />
        <div className="field">
          <label htmlFor="username">Usuario</label>
          <input
            id="username"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            autoComplete="username"
            autoFocus
          />
        </div>
        <div className="field">
          <label htmlFor="password">Contraseña</label>
          <input
            id="password"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            autoComplete="current-password"
          />
        </div>
        <button className="btn btn-primary" type="submit" disabled={loading} style={{ width: "100%" }}>
          {loading ? "Ingresando…" : "Ingresar"}
        </button>

        <div className="divider">o probá el modo demo</div>
        <div className="demo-login">
          <button
            className="btn"
            type="button"
            disabled={demoRol !== null}
            style={{ width: "100%" }}
            onClick={() => entrarDemo("OPERADOR")}
          >
            {demoRol === "OPERADOR" ? "Ingresando…" : "Demo · Operador"}
          </button>
          <button
            className="btn"
            type="button"
            disabled={demoRol !== null}
            style={{ width: "100%" }}
            onClick={() => entrarDemo("SUPERVISOR")}
          >
            {demoRol === "SUPERVISOR" ? "Ingresando…" : "Demo · Supervisor"}
          </button>
          <p className="text-muted demo-note">Datos de ejemplo, de solo lectura.</p>
        </div>
      </form>
    </div>
  );
}