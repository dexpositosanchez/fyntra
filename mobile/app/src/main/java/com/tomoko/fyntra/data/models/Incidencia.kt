package com.tomoko.fyntra.data.models

data class Incidencia(
    val id: Int,
    val titulo: String,
    val descripcion: String? = null,
    val prioridad: String,
    val estado: String,
    val inmueble_id: Int,
    val creador_usuario_id: Int,
    val proveedor_id: Int? = null,
    val fecha_alta: String,
    val fecha_cierre: String? = null,
    val version: Int,
    val inmueble: InmuebleSimple? = null,
    val proveedor: ProveedorSimple? = null,
    val historial: List<HistorialIncidencia>? = null,
    val actuaciones_count: Int = 0,
    val documentos_count: Int = 0,
    val mensajes_count: Int = 0
)

data class ProveedorSimple(
    val id: Int,
    val nombre: String,
    val email: String? = null,
    val telefono: String? = null,
    val especialidad: String? = null
)

data class InmuebleSimple(
    val id: Int,
    val referencia: String,
    val direccion: String
)

data class HistorialIncidencia(
    val id: Int,
    val estado_anterior: String? = null,
    val estado_nuevo: String,
    val comentario: String? = null,
    val fecha: String,
    val usuario_nombre: String? = null
)

data class IncidenciaCreate(
    val titulo: String,
    val descripcion: String,
    val prioridad: String,
    val inmueble_id: Int
)

data class IncidenciaUpdate(
    val titulo: String? = null,
    val descripcion: String? = null,
    val prioridad: String? = null,
    val estado: String? = null,
    val proveedor_id: Int? = null,
    val comentario_cambio: String? = null,
    val version: Int
)

