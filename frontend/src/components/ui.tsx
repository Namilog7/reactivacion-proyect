import type { ReactNode } from "react";
import type { Alertas } from "../api/types";

export function Modal({
  title,
  onClose,
  children,
  wide = false,
}: {
  title: string;
  onClose: () => void;
  children: ReactNode;
  wide?: boolean;
}) {
  return (
    <div className="modal-backdrop" onMouseDown={(e) => { if (e.target === e.currentTarget) onClose(); }}>
      <div className="modal" style={wide ? { maxWidth: 860 } : undefined}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <h3>{title}</h3>
          <button className="btn" onClick={onClose} aria-label="Cerrar">✕</button>
        </div>
        {children}
      </div>
    </div>
  );
}

export function Pagination({
  page,
  pages,
  total,
  onPage,
}: {
  page: number;
  pages: number;
  total: number;
  onPage: (p: number) => void;
}) {
  return (
    <div className="pagination">
      <span className="page-info">
        {total} registro{total === 1 ? "" : "s"} · pág. {page} de {pages}
      </span>
      <button className="btn" disabled={page <= 1} onClick={() => onPage(page - 1)}>
        Anterior
      </button>
      <button className="btn" disabled={page >= pages} onClick={() => onPage(page + 1)}>
        Siguiente
      </button>
    </div>
  );
}

export function AlertIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" aria-hidden="true" fill="currentColor">
      <path d="M12 2 1 21h22L12 2zm1 14h-2v2h2v-2zm0-7h-2v5h2V9z" />
    </svg>
  );
}

export function ErrorBanner({ message }: { message: string | null }) {
  if (!message) return null;
  return <div className="alert-box alert-error">{message}</div>;
}

export function SuccessBanner({ message }: { message: string | null }) {
  if (!message) return null;
  return <div className="alert-box alert-success">{message}</div>;
}

export function fmtFecha(iso?: string | null): string {
  if (!iso) return "—";
  const d = new Date(iso);
  if (isNaN(d.getTime())) return iso;
  return d.toLocaleDateString("es-AR");
}

/** Renderiza el nivel de alerta de una gestión con texto accesible + icono. */
export function AlertBadge({ alertas }: { alertas: Alertas }) {
  if (alertas.nivel === "NINGUNA") return <span>—</span>;
  const critica = alertas.nivel === "CRITICA";
  const texto = alertas.mensajes.join(" ");
  return (
    <span
      className={critica ? "badge-critica" : "badge-alerta"}
      role="img"
      aria-label={texto}
      title={texto}
    >
      {critica ? "!!" : <AlertIcon />}
      {critica ? "CRÍTICA" : "Alerta"}
    </span>
  );
}

/**
 * Celda de una columna de estado con fondo rojo leve cuando la regla aplica.
 * Incluye tooltip y texto accesible para no depender solo del color.
 */
export function AlertCell({
  value,
  showTip,
  alertas,
}: {
  value: ReactNode;
  showTip: boolean;
  alertas: Alertas;
}) {
  if (!showTip) {
    return (
      <td>
        <span style={{ display: "inline-block", width: "100%" }}>{value}</span>
      </td>
    );
  }
  const textos = alertas.mensajes;
  return (
    <td className={"cell-alert"}>
      <span
        role="img"
        aria-label={textos.join(" ")}
        title={textos.join(" ")}
        style={{ display: "inline-block", width: "100%", cursor: "help" }}
      >
        {value}
      </span>
    </td>
  );
}