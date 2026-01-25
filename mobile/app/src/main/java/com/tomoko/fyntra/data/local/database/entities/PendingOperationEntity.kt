package com.tomoko.fyntra.data.local.database.entities

import androidx.room.Entity
import androidx.room.PrimaryKey

@Entity(tableName = "pending_operations")
data class PendingOperationEntity(
    @PrimaryKey(autoGenerate = true) val id: Long = 0,
    val operationType: String, // CREATE, UPDATE, DELETE
    val endpoint: String,
    val data: String, // JSON de los datos
    val timestamp: Long = System.currentTimeMillis(),
    val status: String = "pending", // pending, syncing, synced, error
    val errorMessage: String? = null,
    val retryCount: Int = 0
)
