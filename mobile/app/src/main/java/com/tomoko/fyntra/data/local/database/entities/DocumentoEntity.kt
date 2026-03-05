package com.tomoko.fyntra.data.local.database.entities

import androidx.room.Entity
import androidx.room.PrimaryKey

@Entity(tableName = "documentos")
data class DocumentoEntity(
    @PrimaryKey val id: Int,
    val incidencia_id: Int,
    val usuario_id: Int,
    val nombre: String,
    val nombre_archivo: String,
    val tipo_archivo: String? = null,
    val tamano: Int? = null,
    val creado_en: String,
    val subido_por: String? = null,
    val local_path: String? = null,
    val syncStatus: String = "synced" // pending, synced, error
)

