export type Rol = "SUPERVISOR" | "OPERADOR";

export interface Usuario {
  id: string;
  username: string;
  nombre: string;
  rol: Rol;
  tipo: "REAL" | "DEMO";
  activo: boolean;
  created_at: string;
}

export interface Periodo {
  id: string;
  nombre: string;
  mes: number;
  anio: number;
  periodo_vigente: boolean;
}

export interface TipoOperacion {
  id: string;
  codigo: string;
  nombre: string;
}

export type NivelAlerta = "NINGUNA" | "ALERTA" | "CRITICA";

export interface Alertas {
  nivel: NivelAlerta;
  nc_alerta: boolean;
  desbloqueo_alerta: boolean;
  mensajes: string[];
}

export interface OperadorRef {
  id: string;
  nombre: string;
}

export interface Gestion {
  id: string;
  cliente_numero: string;
  cliente_nombre?: string | null;
  operador: OperadorRef;
  periodo_id: string;
  periodo_nombre: string;
  tipo_operacion: TipoOperacion;
  fecha_ofrecida_pago?: string | null;
  pago: boolean;
  desbloqueado: boolean;
  tiene_nc: boolean;
  observaciones: string;
  origen: "MANUAL" | "CONCILIACION";
  conciliacion_origen_id?: string | null;
  alertas: Alertas;
  created_at: string;
  updated_at: string;
}

export interface Paginated<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
}

export interface HistorialItem {
  id: string;
  usuario_nombre?: string | null;
  conciliacion_id?: string | null;
  num_conciliacion?: number | null;
  campo: string;
  valor_anterior?: unknown | null;
  valor_nuevo: unknown;
  origen: string;
  created_at: string;
}

export interface MotivoCarga {
  codigo: string;
  nombre: string;
  descripcion?: string | null;
}

export interface CargaOperadorResumen {
  id: string;
  username: string;
  nombre: string;
  activo: boolean;
  gestiones: number;
  pagos: number;
  alertas: number;
  criticas: number;
}

export interface CargaResumen {
  periodo?: { id: string; nombre: string } | null;
  items: CargaOperadorResumen[];
}

export interface CargaResultado {
  operador: OperadorRef;
  periodo: { id: string; nombre: string };
  motivo: { codigo: string; nombre: string };
  archivo_nombre: string;
  total_filas: number;
  duplicados_archivo: number;
  invalidas_archivo: number;
  procesadas: number;
  actualizadas: number;
  sin_cambios: number;
  sin_gestion: number;
  modificaciones: number;
}

export interface DashboardSupervisor {
  total_operadores: number;
  operadores_activos: number;
  total_periodos: number;
  total_gestiones: number;
  periodos: (Periodo & { total_gestiones: number })[];
}

export interface DashboardOperador {
  periodo_id?: string | null;
  periodo_nombre?: string | null;
  total_gestiones: number;
  total_pagos: number;
  alertas: number;
  criticas: number;
  problemas_nc: number;
  problemas_desbloqueo: number;
}