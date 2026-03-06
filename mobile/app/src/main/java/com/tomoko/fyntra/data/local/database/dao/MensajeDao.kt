package com.tomoko.fyntra.data.local.database.dao

import androidx.room.Dao
import androidx.room.Insert
import androidx.room.OnConflictStrategy
import androidx.room.Query
import com.tomoko.fyntra.data.local.database.entities.MensajeEntity
import kotlinx.coroutines.flow.Flow

@Dao
interface MensajeDao {
    @Query("SELECT * FROM mensajes WHERE incidencia_id = :incidenciaId ORDER BY creado_en ASC")
    fun getMensajesByIncidencia(incidenciaId: Int): Flow<List<MensajeEntity>>

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertMensaje(mensaje: MensajeEntity)

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertMensajes(mensajes: List<MensajeEntity>)

    @Query("DELETE FROM mensajes WHERE incidencia_id = :incidenciaId")
    suspend fun deleteMensajesIncidencia(incidenciaId: Int)

    @Query("DELETE FROM mensajes WHERE id = :id")
    suspend fun deleteById(id: Int)

    @Query("DELETE FROM mensajes")
    suspend fun deleteAllMensajes()

    @Query("UPDATE mensajes SET incidencia_id = :newIncidenciaId WHERE incidencia_id = :oldIncidenciaId")
    suspend fun remapIncidenciaId(oldIncidenciaId: Int, newIncidenciaId: Int)
}

