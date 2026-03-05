package com.tomoko.fyntra.data.local.database.dao

import androidx.room.Dao
import androidx.room.Insert
import androidx.room.OnConflictStrategy
import androidx.room.Query
import com.tomoko.fyntra.data.local.database.entities.ActuacionEntity
import kotlinx.coroutines.flow.Flow

@Dao
interface ActuacionDao {
    @Query("SELECT * FROM actuaciones WHERE incidencia_id = :incidenciaId ORDER BY fecha DESC")
    fun getActuacionesByIncidencia(incidenciaId: Int): Flow<List<ActuacionEntity>>

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertActuacion(actuacion: ActuacionEntity)

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertActuaciones(actuaciones: List<ActuacionEntity>)

    @Query("DELETE FROM actuaciones WHERE incidencia_id = :incidenciaId")
    suspend fun deleteActuacionesIncidencia(incidenciaId: Int)

    @Query("DELETE FROM actuaciones WHERE id = :id")
    suspend fun deleteById(id: Int)
}

