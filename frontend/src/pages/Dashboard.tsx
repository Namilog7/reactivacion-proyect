import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useAuth } from "../auth/AuthContext";
import { api } from "../api/client";
import type { DashboardOperador, DashboardSupervisor, Periodo } from "../api/types";
import { ErrorBanner, Modal } from "../components/ui";

export function Dashboard() {
  const { usuario } = useAuth();
  return usuario?.rol === "SUPERVISOR" ? <SupervisorDash /> : <OperadorDash />;
}

function OperadorDash() {
  const { data: periodos } = useQuery({
    queryKey: ["periodos"],
    queryFn: () => api.get<Periodo[]>("/periodos"),
  });
  const vigente = periodos?.find((p) => p.periodo_vigente)?.id ?? periodos?.[0]?.id;
  const [periodoId, setPeriodoId] = useState<string | undefined>(undefined);

  const { data, isLoading, error } = useQuery({
    queryKey: ["dashboard", "operador", periodoId ?? "vigente"],
    queryFn: () => api.get<DashboardOperador>("/dashboard/operador", { periodo_id: periodoId }),
  });

  const card = (cfg: { num: number; label: string; cls?: string }) => (
    <div key={cfg.label} className={`card ${cfg.cls ?? ""}`}>
      <div className="num">{cfg.num}</div>
      <div className="label">{cfg.label}</div>
    </div>
  );

  return (
    <div>
      <h2>Panel del operador</h2>
      <div className="filters">
        <div className="field">
          <label>Período</label>
          <select
            value={periodoId ?? vigente ?? ""}
            onChange={(e) => setPeriodoId(e.target.value || undefined)}
          >
            {periodos
              ?.slice()
              .sort((a, b) => (a.anio !== b.anio ? b.anio - a.anio : b.mes - a.mes))
              .map((p) => (
                <option key={p.id} value={p.id}>
                  {p.nombre} {p.periodo_vigente ? "(actual)" : ""}
                </option>
              ))}
          </select>
        </div>
      </div>
      <ErrorBanner message={error instanceof Error ? error.message : null} />
      {isLoading && <p>Cargando…</p>}
      {data && (
        <>
          <h3 className="text-muted">{data.periodo_nombre ?? "Sin período vigente"}</h3>
          <div className="cards">
            {card({ num: data.total_gestiones, label: "Gestiones" })}
            {card({ num: data.total_pagos, label: "Pagos registrados" })}
            {card({ num: data.alertas, label: "Alertas", cls: "card-alert" })}
            {card({ num: data.criticas, label: "Situaciones críticas", cls: "card-critica" })}
            {card({ num: data.problemas_nc, label: "Problemas de NC", cls: "card-alert" })}
            {card({ num: data.problemas_desbloqueo, label: "Problemas de desbloqueo", cls: "card-alert" })}
          </div>
        </>
      )}
    </div>
  );
}

function SupervisorDash() {
  const qc = useQueryClient();
  const [crearPeriodo, setCrearPeriodo] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [okMsg, setOkMsg] = useState<string | null>(null);

  const { data, isLoading, error } = useQuery({
    queryKey: ["dashboard", "supervisor"],
    queryFn: () => api.get<DashboardSupervisor>("/dashboard/supervisor"),
  });

  const setVigente = useMutation({
    mutationFn: (id: string) => api.patch<Periodo>(`/periodos/${id}`, { periodo_vigente: true }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["dashboard", "supervisor"] });
      qc.invalidateQueries({ queryKey: ["periodos"] });
      setOkMsg("Período vigente actualizado.");
      setTimeout(() => setOkMsg(null), 3000);
    },
    onError: (e: Error) => setErrorMsg(e.message),
  });

  const flash = (m: string) => {
    setOkMsg(m);
    setTimeout(() => setOkMsg(null), 3000);
  };

  return (
    <div>
      <h2>Panel del supervisor</h2>
      <ErrorBanner message={errorMsg ?? (error instanceof Error ? error.message : null)} />
      {okMsg && <div className="alert-box alert-success">{okMsg}</div>}
      {isLoading && <p>Cargando…</p>}
      {data && (
        <>
          <div className="cards">
            <div className="card">
              <div className="num">{data.total_operadores}</div>
              <div className="label">Operadores ({data.operadores_activos} activos)</div>
            </div>
            <div className="card">
              <div className="num">{data.total_periodos}</div>
              <div className="label">Períodos</div>
            </div>
            <div className="card">
              <div className="num">{data.total_gestiones}</div>
              <div className="label">Gestiones en total</div>
            </div>
          </div>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <h3>Períodos</h3>
            <button className="btn btn-primary" onClick={() => setCrearPeriodo(true)}>
              + Nuevo período
            </button>
          </div>
          <div className="table-wrap">
            <table className="data">
              <thead>
                <tr>
                  <th>Período</th>
                  <th>Vigente</th>
                  <th>Mes</th>
                  <th>Año</th>
                  <th>Gestiones</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {data.periodos.map((p) => (
                  <tr key={p.id}>
                    <td>{p.nombre}</td>
                    <td>{p.periodo_vigente ? "Sí" : "No"}</td>
                    <td>{p.mes}</td>
                    <td>{p.anio}</td>
                    <td>{p.total_gestiones}</td>
                    <td>
                      {!p.periodo_vigente && (
                        <button className="btn" onClick={() => setVigente.mutate(p.id)}>
                          Fijar como vigente
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}
      {crearPeriodo && (
        <FormPeriodo
          onClose={() => setCrearPeriodo(false)}
          onHecho={() => {
            setCrearPeriodo(false);
            flash("Período creado.");
            qc.invalidateQueries({ queryKey: ["dashboard", "supervisor"] });
            qc.invalidateQueries({ queryKey: ["periodos"] });
          }}
        />
      )}
    </div>
  );
}

function FormPeriodo({ onClose, onHecho }: { onClose: () => void; onHecho: () => void }) {
  const meses = [
    "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
    "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre",
  ];
  const hoy = new Date();
  const [mes, setMes] = useState(hoy.getMonth() + 1);
  const [anio, setAnio] = useState(hoy.getFullYear());
  const [vigente, setVigente] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const mut = useMutation({
    mutationFn: (body: unknown) => api.post<Periodo>("/periodos", body),
    onSuccess: onHecho,
    onError: (e: Error) => setError(e.message),
  });

  const submit = () => {
    setError(null);
    mut.mutate({
      nombre: `${meses[mes - 1]} ${anio}`,
      mes,
      anio,
      periodo_vigente: vigente,
    });
  };

  return (
    <Modal title="Nuevo período" onClose={onClose}>
      <ErrorBanner message={error} />
      <div className="field">
        <label>Mes</label>
        <select value={mes} onChange={(e) => setMes(Number(e.target.value))}>
          {meses.map((m, i) => (
            <option key={m} value={i + 1}>
              {m}
            </option>
          ))}
        </select>
      </div>
      <div className="field">
        <label>Año</label>
        <input type="number" value={anio} onChange={(e) => setAnio(Number(e.target.value))} />
      </div>
      <div className="checkbox-row">
        <input type="checkbox" checked={vigente} onChange={(e) => setVigente(e.target.checked)} id="p-vigente" />
        <label htmlFor="p-vigente">Fijar como período vigente (los demás dejarán de serlo)</label>
      </div>
      <div style={{ display: "flex", gap: 8, justifyContent: "flex-end" }}>
        <button className="btn" onClick={onClose}>Cancelar</button>
        <button className="btn btn-primary" onClick={submit}>Crear</button>
      </div>
    </Modal>
  );
}