package com.tomoko.fyntra.data.local.database.entities

import androidx.room.Entity
import androidx.room.PrimaryKey

/**
 * Caché local de una ruta (mis rutas) para ver sin conexión.
 * Se guarda el JSON completo de la ruta tal como lo devuelve la API.
 */
@Entity(tableName = "ruta_cache")
data class RutaCacheEntity(
    @PrimaryKey val id: Int,
    val rutaJson: String,
    val updatedAt: Long = System.currentTimeMillis(),
    val owner_user_id: Int = 0
)
