import { useEffect, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useAuth } from "../auth/AuthContext";
import { api } from "../api/client";
import type { Gestion, HistorialItem, Paginated, Periodo, TipoOperacion, Usuario } from "../api/types";
import { AlertBadge, AlertCell, ErrorBanner, fmtFecha, Modal, Pagination, SuccessBanner } from "../components/ui";

const PAGE_SIZE = 20;
const SORTS = [
  { key: "updated_at", label: "Última modificación" },
  { key: "cliente_numero", label: "Número de cliente" },
  { key: "fecha_ofrecida_pago", label: "Fecha ofrecida" },
];

export function Gestiones() {
  const { usuario } = useAuth();
  const esSup = usuario?.rol === "SUPERVISOR";
  const soloLectura = usuario?.tipo === "DEMO";
  const qc = useQueryClient();

  const [page, setPage] = useState(1);
  const [periodoId, setPeriodoId] = useState("");
  const [operadorId, setOperadorId] = useState("");
  const [q, setQ] = useState("");
  const [qInput, setQInput] = useState("");
  const [tipoId, setTipoId] = useState("");
  const [pago, setPago] = useState("");
  const [desbloqueado, setDesbloqueado] = useState("");
  const [tieneNc, setTieneNc] = useState("");
  const [alerta, setAlerta] = useState("");
  const [sort, setSort] = useState("updated_at");
  const [order, setOrder] = useState<"asc" | "desc">("desc");
  const [crear, setCrear] = useState(false);
  const [historialDe, setHistorialDe] = useState<Gestion | null>(null);
  const [guardandoId, setGuardandoId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [okMsg, setOkMsg] = useState<string | null>(null);

  const { data: periodos } = useQuery({
    queryKey: ["periodos"],
    queryFn: () => api.get<Periodo[]>("/periodos"),
  });
  const { data: tipos } = useQuery({
    queryKey: ["tipos-operacion"],
    queryFn: () => api.get<TipoOperacion[]>("/tipos-operacion"),
  });
  const { data: operadores } = useQuery({
    queryKey: ["operadores"],
    queryFn: () => api.get<Usuario[]>("/usuarios"),
    enabled: esSup,
  });

  const params: Record<string, unknown> = {
    page,
    page_size: PAGE_SIZE,
    sort,
    order,
  };
  if (periodoId) params.periodo_id = periodoId;
  if (esSup && operadorId) params.operador_id = operadorId;
  if (q.trim()) params.q = q.trim();
  if (tipoId) params.tipo_operacion_id = tipoId;
  if (pago !== "") params.pago = pago === "true";
  if (desbloqueado !== "") params.desbloqueado = desbloqueado === "true";
  if (tieneNc !== "") params.tiene_nc = tieneNc === "true";
  if (alerta) params.alerta = alerta;

  const { data, isLoading, error: qerr } = useQuery({
    queryKey: ["gestiones", params],
    queryFn: () => api.get<Paginated<Gestion>>("/gestiones", params),
  });

  const reset = () => {
    setPage(1);
    setError(null);
    setOkMsg(null);
  };
  useEffect(reset, [periodoId, operadorId, q, tipoId, pago, desbloqueado, tieneNc, alerta, sort, order]);

  const patch = useMutation({
    mutationFn: ({ id, body }: { id: string; body: unknown }) =>
      api.patch<Gestion>(`/gestiones/${id}`, body),
    onMutate: ({ id }) => setGuardandoId(id),
    onSuccess: (g) => {
      qc.setQueryData(["gestiones", params], (old?: Paginated<Gestion>) =>
        old ? { ...old, items: old.items.map((i) => (i.id === g.id ? g : i)) } : old
      );
      setOkMsg("Cambios guardados.");
    },
    onError: (e: Error) => setError(e.message),
    onSettled: () => setGuardandoId(null),
  });

  const toggle = (g: Gestion, campo: string, valor: boolean) =>
    patch.mutate({ id: g.id, body: { [campo]: valor } });

  const flash = (msg: string) => {
    setOkMsg(msg);
    setTimeout(() => setOkMsg(null), 4000);
  };

  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <h2>Gestiones</h2>
        {!soloLectura && (
          <button className="btn btn-primary" onClick={() => setCrear(true)}>
            + Nueva gestión
          </button>
        )}
      </div>

      <div className="filters">
        <div className="field">
          <label>Período</label>
          <select value={periodoId} onChange={(e) => setPeriodoId(e.target.value)}>
            <option value="">Todos</option>
            {periodos
              ?.slice()
              .sort((a, b) => (a.anio !== b.anio ? b.anio - a.anio : b.mes - a.mes))
              .map((p) => (
                <option key={p.id} value={p.id}>
                  {p.nombre}
                </option>
              ))}
          </select>
        </div>
        {esSup && (
          <div className="field">
            <label>Operador</label>
            <select value={operadorId} onChange={(e) => setOperadorId(e.target.value)}>
              <option value="">Todos</option>
              {operadores?.map((o) => (
                <option key={o.id} value={o.id}>
                  {o.nombre} {!o.activo ? "(inactivo)" : ""}
                </option>
              ))}
            </select>
          </div>
        )}
        <div className="field">
          <label>Nro. cliente</label>
          <input
            value={qInput}
            placeholder="Buscar…"
            onChange={(e) => {
              setQInput(e.target.value);
              setQ(e.target.value);
            }}
          />
        </div>
        <div className="field">
          <label>Operación</label>
          <select value={tipoId} onChange={(e) => setTipoId(e.target.value)}>
            <option value="">Todas</option>
            {tipos?.map((t) => (
              <option key={t.id} value={t.id}>
                {t.nombre}
              </option>
            ))}
          </select>
        </div>
        <div className="field">
          <label>Pagó</label>
          <select value={pago} onChange={(e) => setPago(e.target.value)}>
            <option value="">Todos</option>
            <option value="true">Sí</option>
            <option value="false">No</option>
          </select>
        </div>
        <div className="field">
          <label>Desbloqueado</label>
          <select value={desbloqueado} onChange={(e) => setDesbloqueado(e.target.value)}>
            <option value="">Todos</option>
            <option value="true">Sí</option>
            <option value="false">No</option>
          </select>
        </div>
        <div className="field">
          <label>NC</label>
          <select value={tieneNc} onChange={(e) => setTieneNc(e.target.value)}>
            <option value="">Todos</option>
            <option value="true">Sí</option>
            <option value="false">No</option>
          </select>
        </div>
        <div className="field">
          <label>Alertas</label>
          <select value={alerta} onChange={(e) => setAlerta(e.target.value)}>
            <option value="">Todas</option>
            <option value="SI">Con alertas</option>
            <option value="CRITICA">Críticas</option>
          </select>
        </div>
        <div className="field">
          <label>Ordenar</label>
          <select
            value={sort}
            onChange={(e) => {
              if (e.target.value !== sort) setOrder("desc");
              setSort(e.target.value);
            }}
          >
            {SORTS.map((s) => (
              <option key={s.key} value={s.key}>
                {s.label}
              </option>
            ))}
          </select>
        </div>
        <div className="field">
          <label>Dirección</label>
          <button
            className="btn"
            onClick={() => setOrder(order === "asc" ? "desc" : "asc")}
            title="Invertir orden"
          >
            {order === "asc" ? "↑ Asc" : "↓ Desc"}
          </button>
        </div>
      </div>

      <ErrorBanner message={error ?? (qerr instanceof Error ? qerr.message : null)} />
      <SuccessBanner message={okMsg} />

      {isLoading && <p>Cargando…</p>}
      {data && (
        <>
          <div className="table-wrap">
            <table className="data">
              <thead>
                <tr>
                  <th>Cliente</th>
                  {esSup && <th>Operador</th>}
                  <th>Operación</th>
                  <th>Fecha ofrecida</th>
                  <th>Pagó</th>
                  <th>Desbloqueo</th>
                  <th>NC</th>
                  <th>Observaciones</th>
                  <th>Alerta</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {data.items.map((g) => (
                  <Fila
                    key={g.id}
                    g={g}
                    esSup={esSup}
                    soloLectura={soloLectura}
                    tipos={tipos ?? []}
                    guardando={guardandoId === g.id}
                    onToggle={(campo, valor) => toggle(g, campo, valor)}
                    onPatch={(body) => patch.mutate({ id: g.id, body })}
                    onHistorial={() => setHistorialDe(g)}
                    flash={flash}
                  />
                ))}
                {data.items.length === 0 && (
                  <tr>
                    <td colSpan={10} className="text-muted" style={{ padding: 24 }}>
                      No se encontraron gestiones con los filtros seleccionados.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
          <Pagination page={data.page} pages={data.pages} total={data.total} onPage={setPage} />
        </>
      )}

      {crear && (
        <NuevaGestion
          periodos={periodos ?? []}
          tipos={tipos ?? []}
          operadores={operadores ?? []}
          esSup={esSup}
          onClose={() => setCrear(false)}
          onCreada={(g) => {
            setCrear(false);
            flash(`Gestión creada para el cliente ${g.cliente_numero}.`);
            qc.invalidateQueries({ queryKey: ["gestiones"] });
          }}
        />
      )}
      {historialDe && (
        <HistorialModal gestion={historialDe} onClose={() => setHistorialDe(null)} />
      )}
    </div>
  );
}

function Fila({
  g,
  esSup,
  soloLectura,
  tipos,
  guardando,
  onToggle,
  onPatch,
  onHistorial,
  flash,
}: {
  g: Gestion;
  esSup: boolean;
  soloLectura: boolean;
  tipos: TipoOperacion[];
  guardando: boolean;
  onToggle: (campo: string, valor: boolean) => void;
  onPatch: (body: unknown) => void;
  onHistorial: () => void;
  flash: (msg: string) => void;
}) {
  const critic = g.alertas.nivel === "CRITICA";
  const [editObs, setEditObs] = useState(false);
  const [obs, setObs] = useState(g.observaciones);

  return (
    <tr className={critic ? "row-critica" : ""}>
      <td>
        <span className="mono">{g.cliente_numero}</span>
        <input
          aria-label={`Cliente ${g.cliente_numero} con alertas: ${g.alertas.mensajes.join(" ")}`}
          type="hidden"
        />
        {g.origen === "CONCILIACION" && (
          <span title="Gestión originada por conciliación" role="img" aria-label="Originada por conciliación">
            {" "}
            ⚙
          </span>
        )}
      </td>
      {esSup && <td>{g.operador.nombre}</td>}
      <td>
        <select
          aria-label="Tipo de operación"
          value={g.tipo_operacion.id}
          disabled={guardando || soloLectura}
          onChange={(e) => {
            onPatch({ tipo_operacion_id: e.target.value });
          }}
        >
          {tipos.map((t) => (
            <option key={t.id} value={t.id}>
              {t.nombre}
            </option>
          ))}
        </select>
      </td>
      <td>
        <input
          type="date"
          aria-label="Fecha ofrecida de pago"
          value={g.fecha_ofrecida_pago ?? ""}
          disabled={guardando || soloLectura}
          onChange={(e) => onPatch({ fecha_ofrecida_pago: e.target.value || null })}
        />
      </td>
      <AlertCell
        value={
          <input type="checkbox" checked={g.pago} disabled={guardando || soloLectura} onChange={(e) => onToggle("pago", e.target.checked)} aria-label="Pagó" />
        }
        showTip={g.pago && !g.tiene_nc}
        alertas={g.alertas}
      />
      <AlertCell
        value={
          <input type="checkbox" checked={g.desbloqueado} disabled={guardando || soloLectura} onChange={(e) => onToggle("desbloqueado", e.target.checked)} aria-label="Desbloqueado" />
        }
        showTip={g.pago && !g.desbloqueado}
        alertas={g.alertas}
      />
      <AlertCell
        value={
          <input type="checkbox" checked={g.tiene_nc} disabled={guardando || soloLectura} onChange={(e) => onToggle("tiene_nc", e.target.checked)} aria-label="Tiene nota de crédito" />
        }
        showTip={(g.pago && !g.tiene_nc) || (g.tipo_operacion.codigo === "DEUDA_BONIFICADA" && !g.tiene_nc)}
        alertas={g.alertas}
      />
      <td style={{ minWidth: 220 }}>
        {soloLectura ? (
          <span title={g.observaciones || "Sin observaciones"}>
            {g.observaciones || <span className="text-muted">Sin observaciones</span>}
          </span>
        ) : editObs ? (
          <span style={{ display: "flex", gap: 4 }}>
            <textarea
              rows={1}
              value={obs}
              onChange={(e) => setObs(e.target.value)}
              aria-label="Observaciones"
            />
            <button
              className="btn btn-primary"
              onClick={() => {
                onPatch({ observaciones: obs });
                setEditObs(false);
                flash("Observaciones guardadas.");
              }}
            >
              OK
            </button>
          </span>
        ) : (
          <span
            title={g.observaciones || "Sin observaciones"}
            style={{ cursor: "pointer", maxWidth: 200, overflow: "hidden", textOverflow: "ellipsis", display: "inline-block" }}
            onClick={() => {
              setObs(g.observaciones);
              setEditObs(true);
            }}
          >
            {g.observaciones || <span className="text-muted">Agregar…</span>}
          </span>
        )}
      </td>
      <td>
        <AlertBadge alertas={g.alertas} />
      </td>
      <td>
        <button className="btn" onClick={onHistorial} title="Historial de cambios">
          Historial
        </button>
      </td>
    </tr>
  );
}

function NuevaGestion({
  periodos,
  tipos,
  operadores,
  esSup,
  onClose,
  onCreada,
}: {
  periodos: Periodo[];
  tipos: TipoOperacion[];
  operadores: Usuario[];
  esSup: boolean;
  onClose: () => void;
  onCreada: (g: Gestion) => void;
}) {
  const [clienteNumero, setClienteNumero] = useState("");
  const [periodoId, setPeriodoId] = useState(
    periodos.find((p) => p.periodo_vigente)?.id ?? periodos[0]?.id ?? ""
  );
  const [tipoId, setTipoId] = useState(tipos[0]?.id ?? "");
  const [operadorId, setOperadorId] = useState("");
  const [fecha, setFecha] = useState("");
  const [pago, setPago] = useState(false);
  const [desbloq, setDesbloq] = useState(false);
  const [nc, setNc] = useState(false);
  const [obs, setObs] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  const crear = useMutation({
    mutationFn: (body: unknown) => api.post<Gestion>("/gestiones", body),
    onSuccess: onCreada,
    onError: (e: Error) => setError(e.message),
  });

  const submit = () => {
    setError(null);
    if (!clienteNumero.trim()) return setError("Ingresá el número de cliente.");
    if (!periodoId) return setError("Seleccioná el período.");
    if (!tipoId) return setError("Seleccioná el tipo de operación.");
    setSaving(true);
    crear.mutate({
      cliente_numero: clienteNumero.trim(),
      periodo_id: periodoId,
      tipo_operacion_id: tipoId,
      operador_id: esSup ? operadorId || undefined : undefined,
      fecha_ofrecida_pago: fecha || null,
      pago,
      desbloqueado: desbloq,
      tiene_nc: nc,
      observaciones: obs,
    });
  };

  return (
    <Modal title="Nueva gestión" onClose={onClose}>
      <ErrorBanner message={error} />
      <div className="field">
        <label>Número de cliente *</label>
        <input value={clienteNumero} onChange={(e) => setClienteNumero(e.target.value)} autoFocus />
      </div>
      <div className="field">
        <label>Período *</label>
        <select value={periodoId} onChange={(e) => setPeriodoId(e.target.value)}>
          {periodos
            .slice()
            .sort((a, b) => (a.anio !== b.anio ? b.anio - a.anio : b.mes - a.mes))
            .map((p) => (
              <option key={p.id} value={p.id}>
                {p.nombre}
              </option>
            ))}
        </select>
      </div>
      <div className="field">
        <label>Tipo de operación *</label>
        <select value={tipoId} onChange={(e) => setTipoId(e.target.value)}>
          {tipos.map((t) => (
            <option key={t.id} value={t.id}>
              {t.nombre}
            </option>
          ))}
        </select>
      </div>
      {esSup && (
        <div className="field">
          <label>Operador responsable *</label>
          <select value={operadorId} onChange={(e) => setOperadorId(e.target.value)}>
            <option value="">Seleccionar…</option>
            {operadores.map((o) => (
              <option key={o.id} value={o.id}>
                {o.nombre}
              </option>
            ))}
          </select>
        </div>
      )}
      <div className="field">
        <label>Fecha ofrecida de pago</label>
        <input type="date" value={fecha} onChange={(e) => setFecha(e.target.value)} />
      </div>
      <div className="checkbox-row">
        <input type="checkbox" checked={pago} onChange={(e) => setPago(e.target.checked)} id="n-pago" />
        <label htmlFor="n-pago">Pagó</label>
      </div>
      <div className="checkbox-row">
        <input type="checkbox" checked={desbloq} onChange={(e) => setDesbloq(e.target.checked)} id="n-desb" />
        <label htmlFor="n-desb">Desbloqueado</label>
      </div>
      <div className="checkbox-row">
        <input type="checkbox" checked={nc} onChange={(e) => setNc(e.target.checked)} id="n-nc" />
        <label htmlFor="n-nc">Tiene nota de crédito</label>
      </div>
      <div className="field">
        <label>Observaciones</label>
        <textarea rows={3} value={obs} onChange={(e) => setObs(e.target.value)} />
      </div>
      <div style={{ display: "flex", gap: 8, justifyContent: "flex-end" }}>
        <button className="btn" onClick={onClose}>
          Cancelar
        </button>
        <button className="btn btn-primary" onClick={submit} disabled={saving}>
          {saving ? "Guardando…" : "Crear gestión"}
        </button>
      </div>
    </Modal>
  );
}

function renderValor(campo: string, v: unknown): string {
  if (v === null || v === undefined) return "—";
  if (typeof v === "object") {
    const o = v as Record<string, unknown>;
    if ("value" in o) return String(o.value ?? "—");
    return JSON.stringify(o);
  }
  if (typeof v === "boolean") return v ? "Sí" : "No";
  if (campo === "fecha_ofrecida_pago" && typeof v === "string") return fmtFecha(v);
  return String(v);
}

function HistorialModal({ gestion, onClose }: { gestion: Gestion; onClose: () => void }) {
  const { data, isLoading } = useQuery({
    queryKey: ["gestiones", gestion.id, "historial"],
    queryFn: () => api.get<HistorialItem[]>(`/gestiones/${gestion.id}/historial`),
  });
  const items = data ?? [];

  const etiquetas: Record<string, string> = {
    creacion: "Creación",
    operador: "Operador",
    tipo_operacion: "Tipo de operación",
    fecha_ofrecida_pago: "Fecha ofrecida",
    pago: "Pagó",
    desbloqueado: "Desbloqueo",
    tiene_nc: "Nota de crédito",
    observaciones: "Observaciones",
  };

  return (
    <Modal title={`Historial · cliente ${gestion.cliente_numero}`} onClose={onClose} wide>
      {isLoading && <p>Cargando…</p>}
      {!isLoading && items.length === 0 && <p className="text-muted">Sin cambios registrados.</p>}
      {!isLoading && items.length > 0 && (
        <div className="table-wrap">
          <table className="data">
            <thead>
              <tr>
                <th>Fecha</th>
                <th>Quién</th>
                <th>Campo</th>
                <th>Anterior</th>
                <th>Nuevo</th>
                <th>Origen</th>
              </tr>
            </thead>
            <tbody>
              {items.map((it) => (
                <tr key={it.id}>
                  <td>{fmtFecha(it.created_at)}</td>
                  <td>
                    {it.usuario_nombre}
                    {it.num_conciliacion != null && (
                      <span className="text-muted"> · Conciliación #{it.num_conciliacion}</span>
                    )}
                  </td>
                  <td>{etiquetas[it.campo] ?? it.campo}</td>
                  <td>{renderValor(it.campo, it.valor_anterior)}</td>
                  <td>{renderValor(it.campo, it.valor_nuevo)}</td>
                  <td>{it.origen}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </Modal>
  );
}