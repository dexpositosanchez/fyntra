package com.tomoko.fyntra.data.repository

import com.tomoko.fyntra.data.api.ApiService
import com.tomoko.fyntra.data.local.database.AppDatabase
import com.tomoko.fyntra.data.local.database.dao.IncidenciaDao
import com.tomoko.fyntra.data.local.database.entities.IncidenciaEntity
import com.tomoko.fyntra.data.models.Incidencia
import com.tomoko.fyntra.data.models.IncidenciaCreate
import com.tomoko.fyntra.data.models.IncidenciaUpdate
import com.tomoko.fyntra.data.sync.NetworkMonitor
import com.tomoko.fyntra.data.sync.SyncService
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.map

class IncidenciaRepository(
    private val apiService: ApiService,
    private val database: AppDatabase,
    private val networkMonitor: NetworkMonitor,
    private val syncService: SyncService
) {
    private val incidenciaDao: IncidenciaDao = database.incidenciaDao()

    // Obtener todas las incidencias (desde caché local, actualizando si hay internet)
    fun getIncidencias(estado: String? = null): Flow<List<Incidencia>> {
        // Retornar datos desde caché local
        // La actualización se hará automáticamente cuando haya conexión
        return incidenciaDao.getAllIncidencias().map { entities ->
            entities.map { it.toIncidencia() }
        }
    }
    
    // Refrescar incidencias desde el servidor (llamar manualmente cuando sea necesario)
    suspend fun refreshIncidenciasFromServer(estado: String? = null, userRol: String? = null) {
        refreshIncidencias(estado, userRol)
    }

    // Obtener una incidencia por ID
    suspend fun getIncidenciaById(id: Int): Incidencia? {
        // Primero intentar actualizar desde el servidor si hay internet
        if (networkMonitor.isCurrentlyOnline()) {
            try {
                val response = apiService.getIncidencia(id)
                if (response.isSuccessful && response.body() != null) {
                    val incidencia = response.body()!!
                    incidenciaDao.insertIncidencia(incidencia.toEntity())
                    return incidencia
                }
            } catch (e: Exception) {
                // Si falla, usar caché local
            }
        }
        
        // Usar caché local
        return incidenciaDao.getIncidenciaById(id)?.toIncidencia()
    }

    // Crear incidencia
    suspend fun createIncidencia(incidencia: IncidenciaCreate): Result<Incidencia> {
        return if (networkMonitor.isCurrentlyOnline()) {
            // Si hay internet, enviar directamente
            try {
                val response = apiService.crearIncidencia(incidencia)
                if (response.isSuccessful && response.body() != null) {
                    val created = response.body()!!
                    incidenciaDao.insertIncidencia(created.toEntity())
                    Result.success(created)
                } else {
                    Result.failure(Exception(response.message() ?: "Error al crear incidencia"))
                }
            } catch (e: Exception) {
                Result.failure(e)
            }
        } else {
            // Si no hay internet, guardar localmente y agregar a cola de sincronización
            val tempId = System.currentTimeMillis().toInt() // ID temporal
            val localIncidencia = Incidencia(
                id = tempId,
                titulo = incidencia.titulo,
                descripcion = incidencia.descripcion,
                prioridad = incidencia.prioridad,
                estado = "abierta",
                inmueble_id = incidencia.inmueble_id,
                creador_usuario_id = 0, // Se actualizará cuando se sincronice
                fecha_alta = java.time.LocalDateTime.now().toString(),
                version = 1
            )
            
            incidenciaDao.insertIncidencia(localIncidencia.toEntity().copy(syncStatus = "pending"))
            syncService.addPendingOperation("CREATE", "incidencias", incidencia)
            
            Result.success(localIncidencia)
        }
    }

    // Actualizar incidencia
    suspend fun updateIncidencia(id: Int, update: IncidenciaUpdate): Result<Incidencia> {
        val existing = incidenciaDao.getIncidenciaById(id)
        
        return if (networkMonitor.isCurrentlyOnline()) {
            // Si hay internet, enviar directamente
            try {
                val response = apiService.actualizarIncidencia(id, update)
                if (response.isSuccessful && response.body() != null) {
                    val updated = response.body()!!
                    incidenciaDao.insertIncidencia(updated.toEntity())
                    Result.success(updated)
                } else {
                    Result.failure(Exception(response.message() ?: "Error al actualizar incidencia"))
                }
            } catch (e: Exception) {
                Result.failure(e)
            }
        } else {
            // Si no hay internet, actualizar localmente y agregar a cola
            existing?.let {
                val updatedEntity = it.copy(
                    syncStatus = "pending",
                    lastSyncTimestamp = System.currentTimeMillis()
                )
                incidenciaDao.updateIncidencia(updatedEntity)
                syncService.addPendingOperation("UPDATE", "incidencias/$id", update)
                
                // Retornar la versión local actualizada
                Result.success(updatedEntity.toIncidencia())
            } ?: Result.failure(Exception("Incidencia no encontrada"))
        }
    }

    // Eliminar incidencia
    suspend fun deleteIncidencia(id: Int): Result<Unit> {
        return if (networkMonitor.isCurrentlyOnline()) {
            // Si hay internet, eliminar directamente
            try {
                val response = apiService.eliminarIncidencia(id)
                if (response.isSuccessful) {
                    incidenciaDao.getIncidenciaById(id)?.let {
                        incidenciaDao.deleteIncidencia(it)
                    }
                    Result.success(Unit)
                } else {
                    Result.failure(Exception(response.message() ?: "Error al eliminar incidencia"))
                }
            } catch (e: Exception) {
                Result.failure(e)
            }
        } else {
            // Si no hay internet, marcar para eliminación y agregar a cola
            incidenciaDao.getIncidenciaById(id)?.let {
                val deletedEntity = it.copy(syncStatus = "pending")
                incidenciaDao.updateIncidencia(deletedEntity)
                syncService.addPendingOperation("DELETE", "incidencias/$id", mapOf("id" to id))
                Result.success(Unit)
            } ?: Result.failure(Exception("Incidencia no encontrada"))
        }
    }

    // Refrescar incidencias desde el servidor
    private suspend fun refreshIncidencias(estado: String? = null, userRol: String? = null) {
        if (!networkMonitor.isCurrentlyOnline()) {
            // Si no hay internet, no intentar refrescar
            return
        }
        
        try {
            val response = if (userRol == "proveedor") {
                // Proveedores usan endpoint diferente
                apiService.getMisIncidenciasProveedor(estado)
            } else {
                // Admin, super_admin y propietarios usan el endpoint normal
                apiService.getIncidencias(estado)
            }
            
            if (response.isSuccessful) {
                val incidencias = response.body()
                if (incidencias != null && incidencias.isNotEmpty()) {
                    // Limpiar e insertar nuevas incidencias
                    incidenciaDao.deleteAllIncidencias()
                    incidenciaDao.insertIncidencias(
                        incidencias.map { it.toEntity() }
                    )
                } else if (incidencias != null && incidencias.isEmpty()) {
                    // Si la respuesta es exitosa pero vacía, limpiar la base de datos
                    incidenciaDao.deleteAllIncidencias()
                }
            } else {
                // Si la respuesta no es exitosa, lanzar excepción
                throw Exception("Error al obtener incidencias: ${response.code()} ${response.message()}")
            }
        } catch (e: Exception) {
            // Error al refrescar, usar caché local
            // El error se manejará en el ViewModel
            throw e
        }
    }

    // Sincronizar operaciones pendientes
    suspend fun syncPendingOperations() {
        syncService.syncPendingOperations()
    }
}

// Extensiones para convertir entre Entity y Model
private fun IncidenciaEntity.toIncidencia(): Incidencia {
    return Incidencia(
        id = id,
        titulo = titulo,
        descripcion = descripcion,
        prioridad = prioridad,
        estado = estado,
        inmueble_id = inmueble_id,
        creador_usuario_id = creador_usuario_id,
        proveedor_id = proveedor_id,
        fecha_alta = fecha_alta,
        fecha_cierre = fecha_cierre,
        version = version,
        inmueble = if (inmueble_referencia != null && inmueble_direccion != null) {
            com.tomoko.fyntra.data.models.InmuebleSimple(
                id = inmueble_id,
                referencia = inmueble_referencia ?: "",
                direccion = inmueble_direccion ?: ""
            )
        } else null,
        proveedor = if (proveedor_id != null && proveedor_nombre != null) {
            com.tomoko.fyntra.data.models.ProveedorSimple(
                id = proveedor_id,
                nombre = proveedor_nombre ?: "",
                email = proveedor_email,
                telefono = proveedor_telefono,
                especialidad = proveedor_especialidad
            )
        } else null,
        historial = null, // El historial se carga por separado si es necesario
        actuaciones_count = 0, // Se puede calcular desde la base de datos si es necesario
        documentos_count = 0,
        mensajes_count = 0
    )
}

private fun Incidencia.toEntity(): IncidenciaEntity {
    return IncidenciaEntity(
        id = id,
        titulo = titulo,
        descripcion = descripcion,
        prioridad = prioridad,
        estado = estado,
        inmueble_id = inmueble_id,
        creador_usuario_id = creador_usuario_id,
        proveedor_id = proveedor_id,
        fecha_alta = fecha_alta,
        fecha_cierre = fecha_cierre,
        version = version,
        syncStatus = "synced",
        lastSyncTimestamp = System.currentTimeMillis(),
        inmueble_referencia = inmueble?.referencia,
        inmueble_direccion = inmueble?.direccion,
        proveedor_nombre = proveedor?.nombre,
        proveedor_email = proveedor?.email,
        proveedor_telefono = proveedor?.telefono,
        proveedor_especialidad = proveedor?.especialidad
    )
}
