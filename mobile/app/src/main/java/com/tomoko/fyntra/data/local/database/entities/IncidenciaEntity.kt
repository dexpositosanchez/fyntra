package com.tomoko.fyntra.data.local.database.entities

import androidx.room.Entity
import androidx.room.PrimaryKey

@Entity(tableName = "incidencias")
data class IncidenciaEntity(
    @PrimaryKey val id: Int,
    val titulo: String,
    val descripcion: String?,
    val prioridad: String,
    val estado: String,
    val inmueble_id: Int,
    val creador_usuario_id: Int,
    val proveedor_id: Int?,
    val fecha_alta: String,
    val fecha_cierre: String?,
    val version: Int,
    val syncStatus: String = "synced", // synced, pending, syncing, error
    val lastSyncTimestamp: Long = System.currentTimeMillis(),
    val inmueble_referencia: String? = null,
    val inmueble_direccion: String? = null
)
