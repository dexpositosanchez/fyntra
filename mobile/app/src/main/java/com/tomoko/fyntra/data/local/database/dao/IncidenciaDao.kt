package com.tomoko.fyntra.data.local.database.dao

import androidx.room.*
import com.tomoko.fyntra.data.local.database.entities.IncidenciaEntity
import kotlinx.coroutines.flow.Flow

@Dao
interface IncidenciaDao {
    @Query("SELECT * FROM incidencias ORDER BY fecha_alta DESC")
    fun getAllIncidencias(): Flow<List<IncidenciaEntity>>

    @Query("SELECT * FROM incidencias WHERE id = :id")
    fun observeIncidenciaById(id: Int): Flow<IncidenciaEntity?>

    @Query("SELECT * FROM incidencias WHERE id = :id")
    suspend fun getIncidenciaById(id: Int): IncidenciaEntity?

    @Query("SELECT * FROM incidencias WHERE syncStatus = :status")
    suspend fun getIncidenciasBySyncStatus(status: String): List<IncidenciaEntity>

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertIncidencia(incidencia: IncidenciaEntity)

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertIncidencias(incidencias: List<IncidenciaEntity>)

    @Update
    suspend fun updateIncidencia(incidencia: IncidenciaEntity)

    @Delete
    suspend fun deleteIncidencia(incidencia: IncidenciaEntity)

    @Query("DELETE FROM incidencias")
    suspend fun deleteAllIncidencias()

    @Query("DELETE FROM incidencias WHERE syncStatus = 'synced'")
    suspend fun deleteSyncedIncidencias()

    @Query("SELECT * FROM incidencias WHERE syncStatus IN ('pending', 'error')")
    suspend fun getPendingIncidencias(): List<IncidenciaEntity>
}
