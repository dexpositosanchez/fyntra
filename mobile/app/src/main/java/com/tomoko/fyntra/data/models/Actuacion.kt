package com.tomoko.fyntra.data.models

data class Actuacion(
    val id: Int,
    val incidencia_id: Int,
    val proveedor_id: Int,
    val descripcion: String,
    val fecha: String,
    val coste: Double? = null,
    val creado_en: String,
    val proveedor: com.tomoko.fyntra.data.models.ProveedorSimple? = null
)

data class ActuacionCreate(
    val incidencia_id: Int,
    val descripcion: String,
    val fecha: String,
    val coste: Double? = null
)

