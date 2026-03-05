package com.tomoko.fyntra.data.local.database.dao

import androidx.room.Dao
import androidx.room.Insert
import androidx.room.OnConflictStrategy
import androidx.room.Query
import com.tomoko.fyntra.data.local.database.entities.DocumentoEntity
import kotlinx.coroutines.flow.Flow

@Dao
interface DocumentoDao {
    @Query("SELECT * FROM documentos WHERE incidencia_id = :incidenciaId ORDER BY creado_en DESC")
    fun getDocumentosByIncidencia(incidenciaId: Int): Flow<List<DocumentoEntity>>

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertDocumento(documento: DocumentoEntity)

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertDocumentos(documentos: List<DocumentoEntity>)

    @Query("DELETE FROM documentos WHERE incidencia_id = :incidenciaId")
    suspend fun deleteDocumentosIncidencia(incidenciaId: Int)

    @Query("DELETE FROM documentos WHERE id = :id")
    suspend fun deleteById(id: Int)
}

