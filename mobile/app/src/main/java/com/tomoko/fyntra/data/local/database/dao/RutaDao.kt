package com.tomoko.fyntra.data.local.database.dao

import androidx.room.Dao
import androidx.room.Delete
import androidx.room.Insert
import androidx.room.OnConflictStrategy
import androidx.room.Query
import com.tomoko.fyntra.data.local.database.entities.RutaCacheEntity

@Dao
interface RutaDao {
    @Query("SELECT * FROM ruta_cache ORDER BY id ASC")
    suspend fun getAll(): List<RutaCacheEntity>

    @Query("SELECT * FROM ruta_cache WHERE id = :rutaId LIMIT 1")
    suspend fun getById(rutaId: Int): RutaCacheEntity?

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertAll(entities: List<RutaCacheEntity>)

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insert(entity: RutaCacheEntity)

    @Query("DELETE FROM ruta_cache")
    suspend fun deleteAll()
}
