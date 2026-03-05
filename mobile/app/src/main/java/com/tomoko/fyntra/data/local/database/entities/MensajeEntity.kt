package com.tomoko.fyntra.data.local.database.entities

import androidx.room.Entity
import androidx.room.PrimaryKey

@Entity(tableName = "mensajes")
data class MensajeEntity(
    @PrimaryKey val id: Int,
    val incidencia_id: Int,
    val usuario_id: Int,
    val usuario_nombre: String,
    val usuario_rol: String,
    val contenido: String,
    val creado_en: String,
    val syncStatus: String = "synced" // pending, synced, error
)

