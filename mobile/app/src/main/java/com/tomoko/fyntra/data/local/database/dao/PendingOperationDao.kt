package com.tomoko.fyntra.data.local.database.dao

import androidx.room.*
import com.tomoko.fyntra.data.local.database.entities.PendingOperationEntity
import kotlinx.coroutines.flow.Flow

@Dao
interface PendingOperationDao {
    @Query("SELECT * FROM pending_operations WHERE status = 'pending' ORDER BY timestamp ASC")
    fun getPendingOperations(): Flow<List<PendingOperationEntity>>

    @Query("SELECT * FROM pending_operations WHERE status = 'pending' ORDER BY timestamp ASC")
    suspend fun getPendingOperationsSync(): List<PendingOperationEntity>

    @Query("SELECT * FROM pending_operations WHERE id = :id")
    suspend fun getOperationById(id: Long): PendingOperationEntity?

    @Insert
    suspend fun insertOperation(operation: PendingOperationEntity): Long

    @Update
    suspend fun updateOperation(operation: PendingOperationEntity)

    @Delete
    suspend fun deleteOperation(operation: PendingOperationEntity)

    @Query("DELETE FROM pending_operations WHERE status = 'synced'")
    suspend fun deleteSyncedOperations()

    @Query("DELETE FROM pending_operations WHERE id = :id")
    suspend fun deleteOperationById(id: Long)
}
