package com.tomoko.fyntra.data.local.database.entities

import androidx.room.Entity
import androidx.room.PrimaryKey

@Entity(tableName = "actuaciones")
data class ActuacionEntity(
    @PrimaryKey val id: Int,
    val incidencia_id: Int,
    val proveedor_id: Int,
    val descripcion: String,
    val fecha: String,
    val coste: Double?,
    val creado_en: String,
    val proveedor_nombre: String? = null,
    val syncStatus: String = "synced" // pending, synced, error
)

