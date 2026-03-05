package com.tomoko.fyntra.data.sync

import android.util.Log
import com.google.gson.Gson
import com.tomoko.fyntra.data.api.ApiService
import com.tomoko.fyntra.data.local.database.AppDatabase
import com.tomoko.fyntra.data.local.database.dao.ActuacionDao
import com.tomoko.fyntra.data.local.database.dao.DocumentoDao
import com.tomoko.fyntra.data.local.database.dao.MensajeDao
import com.tomoko.fyntra.data.local.database.dao.PendingOperationDao
import com.tomoko.fyntra.data.local.database.entities.PendingOperationEntity
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.withContext
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.MultipartBody
import okhttp3.RequestBody.Companion.asRequestBody
import okhttp3.RequestBody.Companion.toRequestBody
import retrofit2.HttpException
import java.io.File

class SyncService(
    private val database: AppDatabase,
    private val apiService: ApiService,
    private val networkMonitor: NetworkMonitor,
    private val gson: Gson
) {
    private val pendingOperationDao: PendingOperationDao = database.pendingOperationDao()
    private val mensajeDao: MensajeDao = database.mensajeDao()
    private val actuacionDao: ActuacionDao = database.actuacionDao()
    private val documentoDao: DocumentoDao = database.documentoDao()

    private data class PendingMensajePayload(val localId: Int, val contenido: String)
    private data class PendingActuacionPayload(val localId: Int, val incidencia_id: Int, val descripcion: String, val fecha: String, val coste: Double?)
    private data class PendingDocumentoPayload(val localId: Int, val incidencia_id: Int, val nombre: String, val filePath: String)
    private data class PendingCompletarParadaPayload(
        val rutaId: Int,
        val paradaId: Int,
        val accion: String,
        val fotoPath: String? = null,
        val firmaPath: String? = null
    )

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
                            operation.endpoint.startsWith("mensajes/incidencia/") -> {
                                val incidenciaId = operation.endpoint.split("/").lastOrNull()?.toIntOrNull() ?: 0
                                val payload = gson.fromJson(operation.data, PendingMensajePayload::class.java)
                                val response = apiService.enviarMensaje(
                                    incidenciaId,
                                    com.tomoko.fyntra.data.models.MensajeCreate(payload.contenido)
                                )
                                if (response.isSuccessful && response.body() != null) {
                                    val created = response.body()!!
                                    mensajeDao.deleteById(payload.localId)
                                    mensajeDao.insertMensaje(
                                        com.tomoko.fyntra.data.local.database.entities.MensajeEntity(
                                            id = created.id,
                                            incidencia_id = created.incidencia_id,
                                            usuario_id = created.usuario_id,
                                            usuario_nombre = created.usuario_nombre,
                                            usuario_rol = created.usuario_rol,
                                            contenido = created.contenido,
                                            creado_en = created.creado_en,
                                            syncStatus = "synced"
                                        )
                                    )
                                    markAsSynced(operation.id)
                                    successCount++
                                } else {
                                    handleError(operation, response.message())
                                    errorCount++
                                }
                            }
                            operation.endpoint == "actuaciones" -> {
                                val payload = gson.fromJson(operation.data, PendingActuacionPayload::class.java)
                                val create = com.tomoko.fyntra.data.models.ActuacionCreate(
                                    incidencia_id = payload.incidencia_id,
                                    descripcion = payload.descripcion,
                                    fecha = payload.fecha,
                                    coste = payload.coste
                                )
                                val response = apiService.crearActuacion(create)
                                if (response.isSuccessful && response.body() != null) {
                                    val created = response.body()!!
                                    actuacionDao.deleteById(payload.localId)
                                    actuacionDao.insertActuacion(
                                        com.tomoko.fyntra.data.local.database.entities.ActuacionEntity(
                                            id = created.id,
                                            incidencia_id = created.incidencia_id,
                                            proveedor_id = created.proveedor_id,
                                            descripcion = created.descripcion,
                                            fecha = created.fecha,
                                            coste = created.coste,
                                            creado_en = created.creado_en,
                                            proveedor_nombre = created.proveedor?.nombre,
                                            syncStatus = "synced"
                                        )
                                    )
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
                            operation.endpoint.startsWith("rutas/") && operation.endpoint.endsWith("/iniciar") -> {
                                val rutaId = operation.endpoint.split("/").getOrNull(1)?.toIntOrNull() ?: 0
                                val response = apiService.iniciarRuta(rutaId)
                                if (response.isSuccessful) {
                                    markAsSynced(operation.id)
                                    successCount++
                                } else {
                                    handleError(operation, response.message())
                                    errorCount++
                                }
                            }
                            operation.endpoint.startsWith("rutas/") && operation.endpoint.endsWith("/finalizar") -> {
                                val rutaId = operation.endpoint.split("/").getOrNull(1)?.toIntOrNull() ?: 0
                                val response = apiService.finalizarRuta(rutaId)
                                if (response.isSuccessful) {
                                    markAsSynced(operation.id)
                                    successCount++
                                } else {
                                    handleError(operation, response.message())
                                    errorCount++
                                }
                            }
                            operation.endpoint.startsWith("rutas/") && operation.endpoint.contains("/paradas/") && operation.endpoint.endsWith("/completar") -> {
                                val payload = gson.fromJson(operation.data, PendingCompletarParadaPayload::class.java)
                                val accionBody = payload.accion.toRequestBody("text/plain".toMediaType())
                                val fotoPart = payload.fotoPath?.let { path ->
                                    val file = File(path)
                                    if (file.exists()) {
                                        val body = file.asRequestBody("application/octet-stream".toMediaType())
                                        MultipartBody.Part.createFormData("foto", file.name, body)
                                    } else null
                                }
                                val firmaPart = payload.firmaPath?.let { path ->
                                    val file = File(path)
                                    if (file.exists()) {
                                        val body = file.asRequestBody("application/octet-stream".toMediaType())
                                        MultipartBody.Part.createFormData("firma", file.name, body)
                                    } else null
                                }
                                val response = apiService.completarParada(
                                    rutaId = payload.rutaId,
                                    paradaId = payload.paradaId,
                                    accion = accionBody,
                                    foto = fotoPart,
                                    firma = firmaPart
                                )
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
                    "POST" -> {
                        when {
                            operation.endpoint.startsWith("rutas/") && operation.endpoint.endsWith("/confirmar-entrega") -> {
                                val parts = operation.endpoint.split("/")
                                val rutaId = parts.getOrNull(1)?.toIntOrNull() ?: 0
                                val confirmacion = gson.fromJson(operation.data, com.tomoko.fyntra.data.models.EntregaConfirmacion::class.java)
                                val response = apiService.confirmarEntrega(rutaId, confirmacion)
                                if (response.isSuccessful) {
                                    markAsSynced(operation.id)
                                    successCount++
                                } else {
                                    handleError(operation, response.message())
                                    errorCount++
                                }
                            }
                            else -> {
                                Log.w("SyncService", "Unknown POST endpoint: ${operation.endpoint}")
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
                    "UPLOAD" -> {
                        when {
                            operation.endpoint == "documentos" -> {
                                val payload = gson.fromJson(operation.data, PendingDocumentoPayload::class.java)
                                val file = File(payload.filePath)
                                if (!file.exists()) {
                                    handleError(operation, "Archivo no encontrado para subir")
                                    errorCount++
                                } else {
                                    val incidenciaIdPart = payload.incidencia_id
                                        .toString()
                                        .toRequestBody("text/plain".toMediaType())
                                    val nombrePart = payload.nombre.toRequestBody("text/plain".toMediaType())
                                    val requestFile = file.asRequestBody("application/octet-stream".toMediaType())
                                    val filePart = MultipartBody.Part.createFormData("archivo", file.name, requestFile)
                                    val response = apiService.uploadDocumento(incidenciaIdPart, nombrePart, filePart)
                                    if (response.isSuccessful && response.body() != null) {
                                        val created = response.body()!!
                                        documentoDao.deleteById(payload.localId)
                                        documentoDao.insertDocumento(
                                            com.tomoko.fyntra.data.local.database.entities.DocumentoEntity(
                                                id = created.id,
                                                incidencia_id = created.incidencia_id,
                                                usuario_id = created.usuario_id,
                                                nombre = created.nombre,
                                                nombre_archivo = created.nombre_archivo,
                                                tipo_archivo = created.tipo_archivo,
                                                tamano = created.tamano,
                                                creado_en = created.creado_en,
                                                subido_por = created.subido_por,
                                                local_path = null,
                                                syncStatus = "synced"
                                            )
                                        )
                                        markAsSynced(operation.id)
                                        successCount++
                                    } else {
                                        handleError(operation, response.message())
                                        errorCount++
                                    }
                                }
                            }
                            else -> {
                                Log.w("SyncService", "Unknown UPLOAD endpoint: ${operation.endpoint}")
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
