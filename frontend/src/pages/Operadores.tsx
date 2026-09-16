import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "../api/client";
import type {
  CargaOperadorResumen,
  CargaResultado,
  CargaResumen,
  MotivoCarga,
  Rol,
  Usuario,
} from "../api/types";
import { ErrorBanner, Modal, SuccessBanner } from "../components/ui";

export function Operadores() {
  const qc = useQueryClient();
  const { data: operadores, isLoading, error } = useQuery({
    queryKey: ["operadores"],
    queryFn: () => api.get<Usuario[]>("/usuarios"),
  });
  const { data: resumen } = useQuery({
    queryKey: ["cargas", "resumen"],
    queryFn: () => api.get<CargaResumen>("/cargas/resumen"),
  });
  const [crear, setCrear] = useState(false);
  const [editando, setEditando] = useState<Usuario | null>(null);
  const [cargandoOp, setCargandoOp] = useState<CargaOperadorResumen | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [okMsg, setOkMsg] = useState<string | null>(null);

  const flash = (m: string) => {
    setOkMsg(m);
    setTimeout(() => setOkMsg(null), 5000);
  };

  const desactivar = useMutation({
    mutationFn: (id: string) => api.del(`/usuarios/${id}`),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["operadores"] });
      qc.invalidateQueries({ queryKey: ["cargas", "resumen"] });
      flash("Operador desactivado (se conserva su historial).");
    },
    onError: (e: Error) => setErrorMsg(e.message),
  });

  const handleCarga = (r: CargaResultado) => {
    qc.invalidateQueries({ queryKey: ["cargas", "resumen"] });
    qc.invalidateQueries({ queryKey: ["gestiones"] });
    qc.invalidateQueries({ queryKey: ["dashboard"] });
    qc.invalidateQueries({ queryKey: ["operadores"] });
    flash(`Carga aplicada: ${r.actualizadas} gestiones actualizadas.`);
  };

  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <h2>Operadores</h2>
        <button className="btn btn-primary" onClick={() => setCrear(true)}>
          + Nuevo operador
        </button>
      </div>
      <ErrorBanner message={errorMsg ?? (error instanceof Error ? error.message : null)} />
      <SuccessBanner message={okMsg} />

      {resumen && resumen.items.length > 0 && (
        <>
          <h3 className="text-muted">
            Cargas por operador
            {resumen.periodo ? ` — ${resumen.periodo.nombre}` : " (sin período vigente)"}
          </h3>
          <div className="operadores-map">
            {resumen.items.map((op) => (
              <div key={op.id} className={`op-card${!op.activo ? " op-inactivo" : ""}`}>
                <div className="op-head">
                  <strong>{op.nombre}</strong>
                  <span className={`op-badge${op.activo ? "" : " op-badge-off"}`}>
                    {op.activo ? "Activo" : "Inactivo"}
                  </span>
                </div>
                <div className="op-user mono">{op.username}</div>
                <div className="op-stats">
                  <span>
                    <em>{op.gestiones}</em> gestiones
                  </span>
                  <span>
                    <em>{op.pagos}</em> pagos
                  </span>
                  <span className="op-alerta">
                    <em>{op.alertas}</em> alertas
                  </span>
                  <span className="op-critica">
                    <em>{op.criticas}</em> críticas
                  </span>
                </div>
                <button
                  className="btn btn-primary"
                  disabled={!op.activo}
                  onClick={() => setCargandoOp(op)}
                >
                  Subir archivo…
                </button>
              </div>
            ))}
          </div>
        </>
      )}

      {isLoading && <p>Cargando…</p>}
      {operadores && (
        <div className="table-wrap">
          <table className="data">
            <thead>
              <tr>
                <th>Usuario</th>
                <th>Nombre</th>
                <th>Rol</th>
                <th>Estado</th>
                <th>Alta</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {operadores.map((u) => (
                <tr key={u.id}>
                  <td className="mono">{u.username}</td>
                  <td>{u.nombre}</td>
                  <td>{u.rol}</td>
                  <td>{u.activo ? "Activo" : "Inactivo"}</td>
                  <td>{new Date(u.created_at).toLocaleDateString("es-AR")}</td>
                  <td style={{ display: "flex", gap: 6 }}>
                    <button className="btn" onClick={() => setEditando(u)}>
                      Editar
                    </button>
                    {u.activo && u.rol === "OPERADOR" && (
                      <button
                        className="btn btn-danger"
                        onClick={() => {
                          if (confirm(`¿Desactivar al operador ${u.nombre}?`))
                            desactivar.mutate(u.id);
                        }}
                      >
                        Desactivar
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      {crear && (
        <FormOperador
          onClose={() => setCrear(false)}
          onHecho={() => {
            setCrear(false);
            flash("Operador creado.");
            qc.invalidateQueries({ queryKey: ["operadores"] });
            qc.invalidateQueries({ queryKey: ["cargas", "resumen"] });
          }}
        />
      )}
      {editando && (
        <FormOperador
          usuario={editando}
          onClose={() => setEditando(null)}
          onHecho={() => {
            setEditando(null);
            flash("Operador actualizado.");
            qc.invalidateQueries({ queryKey: ["operadores"] });
            qc.invalidateQueries({ queryKey: ["cargas", "resumen"] });
          }}
        />
      )}
      {cargandoOp && (
        <CargaModal
          operador={cargandoOp}
          onClose={() => setCargandoOp(null)}
          onHecho={handleCarga}
        />
      )}
    </div>
  );
}

function CargaModal({
  operador,
  onClose,
  onHecho,
}: {
  operador: CargaOperadorResumen;
  onClose: () => void;
  onHecho: (r: CargaResultado) => void;
}) {
  const { data: motivos } = useQuery({
    queryKey: ["cargas", "motivos"],
    queryFn: () => api.get<MotivoCarga[]>("/cargas/motivos"),
  });
  const [motivo, setMotivo] = useState("");
  const [archivo, setArchivo] = useState<File | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [enviando, setEnviando] = useState(false);
  const [resultado, setResultado] = useState<CargaResultado | null>(null);

  const submit = async () => {
    setError(null);
    if (!motivo) return setError("Seleccioná el motivo de la carga.");
    if (!archivo) return setError("Seleccioná el archivo .xlsx.");
    const form = new FormData();
    form.append("file", archivo);
    form.append("operador_id", operador.id);
    form.append("motivo", motivo);
    setEnviando(true);
    try {
      const res = await api.upload<CargaResultado>("/cargas", form);
      setResultado(res);
      onHecho(res);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Error al subir el archivo.");
    } finally {
      setEnviando(false);
    }
  };

  const motivoSel = (motivos ?? []).find((m) => m.codigo === motivo);

  return (
    <Modal title={`Subir archivo — ${operador.nombre}`} onClose={onClose}>
      <ErrorBanner message={error} />
      {resultado ? (
        <div>
          <div className="alert-box alert-success">
            Carga aplicada: <strong>{resultado.actualizadas}</strong> gestiones actualizadas
            ({resultado.sin_gestion} sin gestión, {resultado.sin_cambios} sin cambios).
          </div>
          <ul className="resumen-carga">
            <li>
              Archivo: <span className="mono">{resultado.archivo_nombre}</span>
            </li>
            <li>Período: {resultado.periodo.nombre}</li>
            <li>Motivo: {resultado.motivo.nombre}</li>
            <li>
              Filas: {resultado.total_filas} · modificaciones aplicadas:{" "}
              {resultado.modificaciones}
              {resultado.duplicados_archivo > 0 &&
                ` · duplicadas en archivo: ${resultado.duplicados_archivo}`}
              {resultado.invalidas_archivo > 0 &&
                ` · filas vacías: ${resultado.invalidas_archivo}`}
            </li>
          </ul>
          <div style={{ display: "flex", gap: 8, justifyContent: "flex-end" }}>
            <button className="btn btn-primary" onClick={onClose}>
              Listo
            </button>
            <button
              className="btn"
              onClick={() => {
                setResultado(null);
                setArchivo(null);
                setMotivo("");
              }}
            >
              Cargar otro archivo
            </button>
          </div>
        </div>
      ) : (
        <>
          <div className="field">
            <label>Motivo de la carga</label>
            <select value={motivo} onChange={(e) => setMotivo(e.target.value)}>
              <option value="">Seleccionar…</option>
              {(motivos ?? []).map((m) => (
                <option key={m.codigo} value={m.codigo}>
                  {m.nombre}
                </option>
              ))}
            </select>
            {motivoSel && (
              <p className="text-muted" style={{ fontSize: 12, marginTop: 4 }}>
                {motivoSel.descripcion}
              </p>
            )}
          </div>
          <div className="field">
            <label>Archivo .xlsx (solo números de cliente)</label>
            <input
              type="file"
              accept=".xlsx"
              onChange={(e) => setArchivo(e.target.files?.[0] ?? null)}
            />
          </div>
          <div style={{ display: "flex", gap: 8, justifyContent: "flex-end" }}>
            <button className="btn" onClick={onClose}>
              Cancelar
            </button>
            <button className="btn btn-primary" disabled={enviando} onClick={submit}>
              {enviando ? "Subiendo…" : "Cargar archivo"}
            </button>
          </div>
        </>
      )}
    </Modal>
  );
}

function FormOperador({
  usuario,
  onClose,
  onHecho,
}: {
  usuario?: Usuario;
  onClose: () => void;
  onHecho: () => void;
}) {
  const [username, setUsername] = useState(usuario?.username ?? "");
  const [nombre, setNombre] = useState(usuario?.nombre ?? "");
  const [rol, setRol] = useState<Rol>(usuario?.rol ?? "OPERADOR");
  const [password, setPassword] = useState("");
  const [activo, setActivo] = useState(usuario?.activo ?? true);
  const [error, setError] = useState<string | null>(null);

  const mut = useMutation({
    mutationFn: (body: unknown) =>
      usuario
        ? api.patch<Usuario>(`/usuarios/${usuario.id}`, body)
        : api.post<Usuario>("/usuarios", body),
    onSuccess: onHecho,
    onError: (e: Error) => setError(e.message),
  });

  const submit = () => {
    setError(null);
    if (!username.trim()) return setError("Ingresá el nombre de usuario.");
    if (!nombre.trim()) return setError("Ingresá el nombre.");
    if (!usuario && password.length < 6)
      return setError("La contraseña debe tener al menos 6 caracteres.");
    const body: Record<string, unknown> = { username: username.trim(), nombre: nombre.trim() };
    if (usuario) {
      body.rol = rol;
      body.activo = activo;
      if (password) body.password = password;
    } else {
      body.password = password;
      body.rol = rol;
    }
    mut.mutate(body);
  };

  return (
    <Modal title={usuario ? `Editar ${usuario.nombre}` : "Nuevo operador"} onClose={onClose}>
      <ErrorBanner message={error} />
      <div className="field">
        <label>Usuario</label>
        <input value={username} onChange={(e) => setUsername(e.target.value)} autoFocus />
      </div>
      <div className="field">
        <label>Nombre</label>
        <input value={nombre} onChange={(e) => setNombre(e.target.value)} />
      </div>
      <div className="field">
        <label>Rol</label>
        <select value={rol} onChange={(e) => setRol(e.target.value as Rol)}>
          <option value="OPERADOR">OPERADOR</option>
          <option value="SUPERVISOR">SUPERVISOR</option>
        </select>
      </div>
      <div className="field">
        <label>{usuario ? "Nueva contraseña (opcional)" : "Contraseña *"}</label>
        <input
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          autoComplete="new-password"
        />
      </div>
      {usuario && (
        <div className="checkbox-row">
          <input type="checkbox" checked={activo} onChange={(e) => setActivo(e.target.checked)} id="f-activo" />
          <label htmlFor="f-activo">Activo</label>
        </div>
      )}
      <div style={{ display: "flex", gap: 8, justifyContent: "flex-end" }}>
        <button className="btn" onClick={onClose}>
          Cancelar
        </button>
        <button className="btn btn-primary" onClick={submit}>
          Guardar
        </button>
      </div>
    </Modal>
  );
}