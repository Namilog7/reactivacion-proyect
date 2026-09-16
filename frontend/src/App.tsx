import { Navigate, NavLink, Route, Routes } from "react-router-dom";
import { useAuth } from "./auth/AuthContext";
import { Login } from "./pages/Login";
import { Dashboard } from "./pages/Dashboard";
import { Gestiones } from "./pages/Gestiones";
import { Operadores } from "./pages/Operadores";

function Layout() {
  const { usuario, logout } = useAuth();
  const esSupervisor = usuario?.rol === "SUPERVISOR";
  return (
    <div className="layout">
      <aside className="sidebar">
        <div className="brand">Gestión de Cobranzas</div>
        <NavLink to="/dashboard" end>
          Dashboard
        </NavLink>
        <NavLink to="/gestiones">Gestiones</NavLink>
        {esSupervisor && <NavLink to="/operadores">Operadores</NavLink>}
        <div className="user-box">
          <div>
            <strong>{usuario?.nombre}</strong>
          </div>
          <div className="text-muted" style={{ color: "#9ca3af" }}>
            {esSupervisor ? "Supervisor" : "Operador"}
          </div>
          <div style={{ marginTop: 8 }}>
            <button className="btn" style={{ width: "100%" }} onClick={logout}>
              Cerrar sesión
            </button>
          </div>
        </div>
      </aside>
      <main className="content">
        <Routes>
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/gestiones" element={<Gestiones />} />
          {esSupervisor && (
            <>
              <Route path="/operadores" element={<Operadores />} />
            </>
          )}
          <Route path="*" element={<Navigate to="/dashboard" replace />} />
        </Routes>
      </main>
    </div>
  );
}

export default function App() {
  const { usuario, token, loaded } = useAuth();
  if (!loaded) return <div className="content">Cargando…</div>;
  if (!token || !usuario) return <Login />;
  return <Layout />;
}