package com.tomoko.fyntra.data.models

data class IncidenciaRutaCreate(
    val ruta_id: Int,
    val tipo: String, // "averia", "retraso", "cliente_ausente"
    val descripcion: String,
    val pedido_id: Int? = null
)

data class EntregaConfirmacion(
    val pedido_id: Int,
    val ruta_id: Int,
    val firma_base64: String? = null,
    val foto_base64: String? = null,
    val observaciones: String? = null
)

