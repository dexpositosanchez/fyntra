package com.tomoko.fyntra.data.sync

import android.util.Log
import com.google.gson.Gson
import com.tomoko.fyntra.data.api.ApiService
import com.tomoko.fyntra.data.local.database.AppDatabase
import com.tomoko.fyntra.data.local.database.dao.ActuacionDao
import com.tomoko.fyntra.data.local.database.dao.DocumentoDao
import com.tomoko.fyntra.data.local.database.dao.IncidenciaDao
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
    private val incidenciaDao: IncidenciaDao = database.incidenciaDao()
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
    private data class PendingIncidenciaRutaPayload(
        val rutaId: Int,
        val create: com.tomoko.fyntra.data.models.IncidenciaRutaCreate,
        val cancelarRuta: Boolean,
        val fotoPath: String? = null
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
        val incidenciaIdRemap = mutableMapOf<Int, Int>() // localTempId -> serverId

        for (operation in pendingOps) {
            try {
                // Marcar como sincronizando
                val syncingOp = operation.copy(status = "syncing")
                pendingOperationDao.updateOperation(syncingOp)

                when (operation.operationType) {
                    "CREATE" -> {
                        when {
                            operation.endpoint.startsWith("incidencias") -> {
                                // Compatibilidad: formato nuevo incluye localId para poder migrar documentos/fotos.
                                val payload = runCatching {
                                    gson.fromJson(operation.data, PendingCreateIncidenciaPayload::class.java)
                                }.getOrNull()

                                val incidenciaCreate = payload?.incidencia ?: runCatching {
                                    gson.fromJson(operation.data, com.tomoko.fyntra.data.models.IncidenciaCreate::class.java)
                                }.getOrNull()

                                if (incidenciaCreate == null) {
                                    handleError(operation, "Payload de incidencia inválido")
                                    errorCount++
                                } else {
                                    val response = apiService.crearIncidencia(incidenciaCreate)
                                    if (response.isSuccessful && response.body() != null) {
                                        val created = response.body()!!
                                        payload?.let {
                                            val localId = it.localId
                                            val serverId = created.id
                                            incidenciaIdRemap[localId] = serverId
                                            migrateIncidenciaId(localId, serverId)
                                            remapPendingOperations(localId, serverId)
                                        }
                                        markAsSynced(operation.id)
                                        successCount++
                                    } else {
                                        handleError(operation, response.message())
                                        errorCount++
                                    }
                                }
                            }
                            operation.endpoint.startsWith("mensajes/incidencia/") -> {
                                val rawId = operation.endpoint.split("/").lastOrNull()?.toIntOrNull() ?: 0
                                val incidenciaId = incidenciaIdRemap[rawId] ?: rawId
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
                                val incidenciaId = incidenciaIdRemap[payload.incidencia_id] ?: payload.incidencia_id
                                val create = com.tomoko.fyntra.data.models.ActuacionCreate(
                                    incidencia_id = incidenciaId,
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
                                val rawId = extractIdFromEndpoint(operation.endpoint)
                                val incidenciaId = incidenciaIdRemap[rawId] ?: rawId
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
                                        val body = file.asRequestBody("image/jpeg".toMediaType())
                                        MultipartBody.Part.createFormData("foto", file.name, body)
                                    } else null
                                }
                                val firmaPart = payload.firmaPath?.let { path ->
                                    val file = File(path)
                                    if (file.exists()) {
                                        val body = file.asRequestBody("image/jpeg".toMediaType())
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
                            operation.endpoint.startsWith("rutas/") && operation.endpoint.endsWith("/incidencia") -> {
                                val payload = gson.fromJson(operation.data, PendingIncidenciaRutaPayload::class.java)
                                val mediaTypeText = "text/plain".toMediaType()
                                val tipoPart = payload.create.tipo.toRequestBody(mediaTypeText)
                                val descripcionPart = payload.create.descripcion.toRequestBody(mediaTypeText)
                                val cancelarRutaPart = payload.cancelarRuta.toString().toRequestBody(mediaTypeText)
                                val rutaParadaIdPart = payload.create.ruta_parada_id?.toString()?.toRequestBody(mediaTypeText)

                                val fotoParts = payload.fotoPath?.let { path ->
                                    val file = File(path)
                                    if (file.exists()) {
                                        val requestFile = file.asRequestBody("image/jpeg".toMediaType())
                                        listOf(MultipartBody.Part.createFormData("fotos", file.name, requestFile))
                                    } else emptyList()
                                } ?: emptyList()

                                val response = apiService.reportarIncidenciaRuta(
                                    rutaId = payload.rutaId,
                                    tipo = tipoPart,
                                    descripcion = descripcionPart,
                                    rutaParadaId = rutaParadaIdPart,
                                    cancelarRuta = cancelarRutaPart,
                                    fotos = fotoParts
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
                                Log.w("SyncService", "Unknown POST endpoint: ${operation.endpoint}")
                                markAsSynced(operation.id)
                            }
                        }
                    }
                    "DELETE" -> {
                        when {
                            operation.endpoint.startsWith("incidencias/") -> {
                                val rawId = extractIdFromEndpoint(operation.endpoint)
                                val incidenciaId = incidenciaIdRemap[rawId] ?: rawId
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
                        // Ya no se usa para documentos; mantenemos el tipo por compatibilidad
                        Log.w("SyncService", "Ignoring UPLOAD operation: ${operation.endpoint}")
                        markAsSynced(operation.id)
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

    private suspend fun migrateIncidenciaId(oldLocalId: Int, newServerId: Int) {
        if (oldLocalId == newServerId) return

        val local = incidenciaDao.getIncidenciaById(oldLocalId)
        if (local != null) {
            // Insertar con el ID real preservando owner_user_id, inmueble_referencia/direccion, historial_json, etc.
            incidenciaDao.insertIncidencia(
                local.copy(
                    id = newServerId,
                    syncStatus = "synced",
                    lastSyncTimestamp = System.currentTimeMillis()
                )
            )
            // Borrar la fila temporal
            incidenciaDao.deleteIncidencia(local)
        }

        // Reasignar dependencias (documentos/fotos, chat, actuaciones) al nuevo ID
        documentoDao.remapIncidenciaId(oldLocalId, newServerId)
        mensajeDao.remapIncidenciaId(oldLocalId, newServerId)
        actuacionDao.remapIncidenciaId(oldLocalId, newServerId)
    }

    private suspend fun remapPendingOperations(oldLocalId: Int, newServerId: Int) {
        val ops = pendingOperationDao.getPendingOperationsSync()
        if (ops.isEmpty()) return

        for (op in ops) {
            when {
                op.endpoint == "actuaciones" -> {
                    val parsed = runCatching { gson.fromJson(op.data, PendingActuacionPayload::class.java) }.getOrNull()
                    if (parsed != null && parsed.incidencia_id == oldLocalId) {
                        val updatedPayload = parsed.copy(incidencia_id = newServerId)
                        pendingOperationDao.updateOperation(op.copy(data = gson.toJson(updatedPayload)))
                    }
                }
                op.endpoint.startsWith("mensajes/incidencia/") -> {
                    val rawId = op.endpoint.split("/").lastOrNull()?.toIntOrNull()
                    if (rawId != null && rawId == oldLocalId) {
                        val newEndpoint = "mensajes/incidencia/$newServerId"
                        pendingOperationDao.updateOperation(op.copy(endpoint = newEndpoint))
                    }
                }
                op.endpoint.startsWith("incidencias/") -> {
                    val rawId = extractIdFromEndpoint(op.endpoint)
                    if (rawId == oldLocalId) {
                        val suffix = op.endpoint.removePrefix("incidencias/$oldLocalId")
                        val newEndpoint = "incidencias/$newServerId$suffix"
                        pendingOperationDao.updateOperation(op.copy(endpoint = newEndpoint))
                    }
                }
            }
        }
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
