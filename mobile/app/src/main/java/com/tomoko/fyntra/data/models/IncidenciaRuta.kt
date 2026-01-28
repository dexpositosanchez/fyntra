package com.tomoko.fyntra.data.models

data class IncidenciaRutaCreate(
    val tipo: String, // "averia", "retraso", "cliente_ausente", "otros"
    val descripcion: String,
    val ruta_parada_id: Int? = null // Si es null, es incidencia de ruta; si tiene valor, es de parada
)

data class IncidenciaRutaResponse(
    val id: Int,
    val ruta_id: Int,
    val ruta_parada_id: Int? = null,
    val creador_usuario_id: Int,
    val tipo: String,
    val descripcion: String,
    val creado_en: String,
    val fotos: List<IncidenciaRutaFotoResponse> = emptyList()
)

data class IncidenciaRutaFotoResponse(
    val id: Int,
    val tipo_archivo: String? = null
)

data class EntregaConfirmacion(
    val pedido_id: Int,
    val ruta_id: Int,
    val firma_base64: String? = null,
    val foto_base64: String? = null,
    val observaciones: String? = null
)

