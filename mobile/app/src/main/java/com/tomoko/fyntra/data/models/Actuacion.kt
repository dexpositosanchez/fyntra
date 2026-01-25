package com.tomoko.fyntra.data.models

data class Actuacion(
    val id: Int,
    val incidencia_id: Int,
    val proveedor_id: Int,
    val descripcion: String,
    val fecha: String,
    val coste: Double? = null,
    val creado_en: String,
    val proveedor: ProveedorSimple? = null
)

data class ProveedorSimple(
    val id: Int,
    val nombre: String
)

data class ActuacionCreate(
    val descripcion: String,
    val fecha: String,
    val coste: Double? = null
)

