package com.tomoko.fyntra.data.models

data class Documento(
    val id: Int,
    val incidencia_id: Int,
    val usuario_id: Int,
    val nombre: String,
    val nombre_archivo: String,
    val tipo_archivo: String? = null,
    val tamano: Int? = null,
    val creado_en: String,
    val subido_por: String? = null
)

