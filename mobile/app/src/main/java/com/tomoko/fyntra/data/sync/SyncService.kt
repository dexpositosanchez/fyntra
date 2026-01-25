package com.tomoko.fyntra.data.sync

import android.util.Log
import com.google.gson.Gson
import com.tomoko.fyntra.data.api.ApiService
import com.tomoko.fyntra.data.local.database.AppDatabase
import com.tomoko.fyntra.data.local.database.dao.PendingOperationDao
import com.tomoko.fyntra.data.local.database.entities.PendingOperationEntity
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.withContext
import retrofit2.HttpException

class SyncService(
    private val database: AppDatabase,
    private val apiService: ApiService,
    private val networkMonitor: NetworkMonitor,
    private val gson: Gson
) {
    private val pendingOperationDao: PendingOperationDao = database.pendingOperationDao()

    suspend fun syncPendingOperations(): SyncResult = withContext(Dispatchers.IO) {
        if (!networkMonitor.isCurrentlyOnline()) {
            return@withContext SyncResult.NoInternet
        }

        val pendingOps = pendingOperationDao.getPendingOperationsSync()
        if (pendingOps.isEmpty()) {
            return@withContext SyncResult.Success(0)
        }

        var successCount = 0
        var errorCount = 0

        for (operation in pendingOps) {
            try {
                // Marcar como sincronizando
                val syncingOp = operation.copy(status = "syncing")
                pendingOperationDao.updateOperation(syncingOp)

                when (operation.operationType) {
                    "CREATE" -> {
                        when {
                            operation.endpoint.startsWith("incidencias") -> {
                                val incidencia = gson.fromJson(operation.data, com.tomoko.fyntra.data.models.IncidenciaCreate::class.java)
                                val response = apiService.crearIncidencia(incidencia)
                                if (response.isSuccessful) {
                                    markAsSynced(operation.id)
                                    successCount++
                                } else {
                                    handleError(operation, response.message())
                                    errorCount++
                                }
                            }
                            // Agregar más tipos de operaciones según necesites
                            else -> {
                                Log.w("SyncService", "Unknown CREATE endpoint: ${operation.endpoint}")
                                markAsSynced(operation.id) // Eliminar operaciones desconocidas
                            }
                        }
                    }
                    "UPDATE" -> {
                        when {
                            operation.endpoint.startsWith("incidencias/") -> {
                                val incidenciaId = extractIdFromEndpoint(operation.endpoint)
                                val update = gson.fromJson(operation.data, com.tomoko.fyntra.data.models.IncidenciaUpdate::class.java)
                                val response = apiService.actualizarIncidencia(incidenciaId, update)
                                if (response.isSuccessful) {
                                    markAsSynced(operation.id)
                                    successCount++
                                } else {
                                    handleError(operation, response.message())
                                    errorCount++
                                }
                            }
                            else -> {
                                Log.w("SyncService", "Unknown UPDATE endpoint: ${operation.endpoint}")
                                markAsSynced(operation.id)
                            }
                        }
                    }
                    "DELETE" -> {
                        when {
                            operation.endpoint.startsWith("incidencias/") -> {
                                val incidenciaId = extractIdFromEndpoint(operation.endpoint)
                                val response = apiService.eliminarIncidencia(incidenciaId)
                                if (response.isSuccessful) {
                                    markAsSynced(operation.id)
                                    successCount++
                                } else {
                                    handleError(operation, response.message())
                                    errorCount++
                                }
                            }
                            else -> {
                                Log.w("SyncService", "Unknown DELETE endpoint: ${operation.endpoint}")
                                markAsSynced(operation.id)
                            }
                        }
                    }
                }
            } catch (e: Exception) {
                Log.e("SyncService", "Error syncing operation ${operation.id}", e)
                handleError(operation, e.message ?: "Unknown error")
                errorCount++
            }
        }

        // Limpiar operaciones sincronizadas
        pendingOperationDao.deleteSyncedOperations()

        SyncResult.Success(successCount, errorCount)
    }

    private suspend fun markAsSynced(operationId: Long) {
        val operation = pendingOperationDao.getOperationById(operationId)
        operation?.let {
            pendingOperationDao.updateOperation(it.copy(status = "synced"))
        }
    }

    private suspend fun handleError(operation: PendingOperationEntity, errorMessage: String?) {
        val retryCount = operation.retryCount + 1
        val newStatus = if (retryCount >= 3) "error" else "pending"
        
        pendingOperationDao.updateOperation(
            operation.copy(
                status = newStatus,
                errorMessage = errorMessage,
                retryCount = retryCount
            )
        )
    }

    private fun extractIdFromEndpoint(endpoint: String): Int {
        // Extraer ID de endpoints como "incidencias/123" o "incidencias/123/estado"
        val parts = endpoint.split("/")
        return parts.getOrNull(1)?.toIntOrNull() ?: 0
    }

    suspend fun addPendingOperation(
        type: String,
        endpoint: String,
        data: Any
    ) {
        val jsonData = gson.toJson(data)
        val operation = PendingOperationEntity(
            operationType = type,
            endpoint = endpoint,
            data = jsonData
        )
        pendingOperationDao.insertOperation(operation)
    }
}

sealed class SyncResult {
    object NoInternet : SyncResult()
    data class Success(val syncedCount: Int, val errorCount: Int = 0) : SyncResult()
}
