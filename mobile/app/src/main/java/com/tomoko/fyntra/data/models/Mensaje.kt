package com.tomoko.fyntra.data.models

data class Mensaje(
    val id: Int,
    val incidencia_id: Int,
    val usuario_id: Int,
    val usuario_nombre: String,
    val usuario_rol: String,
    val contenido: String,
    val creado_en: String
)

data class MensajeCreate(
    val contenido: String
)

