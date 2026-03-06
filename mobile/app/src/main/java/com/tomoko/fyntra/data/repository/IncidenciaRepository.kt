package com.tomoko.fyntra.data.repository

import com.google.gson.Gson
import com.google.gson.reflect.TypeToken
import com.tomoko.fyntra.data.api.ApiService
import com.tomoko.fyntra.data.local.AuthDataStore
import com.tomoko.fyntra.data.local.SettingsDataStore
import com.tomoko.fyntra.data.local.database.AppDatabase
import com.tomoko.fyntra.data.local.database.dao.ActuacionDao
import com.tomoko.fyntra.data.local.database.dao.DocumentoDao
import com.tomoko.fyntra.data.local.database.dao.IncidenciaDao
import com.tomoko.fyntra.data.local.database.dao.MensajeDao
import com.tomoko.fyntra.data.local.database.entities.ActuacionEntity
import com.tomoko.fyntra.data.local.database.entities.DocumentoEntity
import com.tomoko.fyntra.data.local.database.entities.IncidenciaEntity
import com.tomoko.fyntra.data.local.database.entities.MensajeEntity
import com.tomoko.fyntra.data.models.Actuacion
import com.tomoko.fyntra.data.models.ActuacionCreate
import com.tomoko.fyntra.data.models.Documento
import com.tomoko.fyntra.data.models.HistorialIncidencia
import com.tomoko.fyntra.data.models.InmuebleSimple
import com.tomoko.fyntra.data.models.Mensaje
import com.tomoko.fyntra.data.models.MensajeCreate
import com.tomoko.fyntra.data.models.Incidencia
import com.tomoko.fyntra.data.models.IncidenciaCreate
import com.tomoko.fyntra.data.models.IncidenciaUpdate
import com.tomoko.fyntra.data.sync.NetworkMonitor
import com.tomoko.fyntra.data.sync.SyncService
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.flow.flatMapLatest
import kotlinx.coroutines.flow.map
import java.time.LocalDateTime
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.MultipartBody
import okhttp3.RequestBody.Companion.asRequestBody
import okhttp3.RequestBody.Companion.toRequestBody
import java.io.File

class IncidenciaRepository(
    private val apiService: ApiService,
    private val database: AppDatabase,
    private val networkMonitor: NetworkMonitor,
    private val syncService: SyncService,
    private val settingsDataStore: SettingsDataStore,
    private val authDataStore: AuthDataStore,
    private val gson: Gson
) {
    private val incidenciaDao: IncidenciaDao = database.incidenciaDao()
    private val mensajeDao: MensajeDao = database.mensajeDao()
    private val actuacionDao: ActuacionDao = database.actuacionDao()
    private val documentoDao: DocumentoDao = database.documentoDao()

    private data class PendingMensajePayload(val localId: Int, val contenido: String)
    private data class PendingActuacionPayload(val localId: Int, val incidencia_id: Int, val descripcion: String, val fecha: String, val coste: Double?)
    private data class PendingDocumentoPayload(val localId: Int, val incidencia_id: Int, val nombre: String, val filePath: String)

    private suspend fun currentOwnerId(): Int = authDataStore.userId.first()?.toIntOrNull() ?: 0

    private fun applyLocalUpdate(entity: IncidenciaEntity, update: IncidenciaUpdate): IncidenciaEntity {
        return entity.copy(
            titulo = update.titulo ?: entity.titulo,
            descripcion = update.descripcion ?: entity.descripcion,
            prioridad = update.prioridad ?: entity.prioridad,
            estado = update.estado ?: entity.estado,
            proveedor_id = update.proveedor_id ?: entity.proveedor_id
            // Nota: version se mantiene para evitar conflictos con optimistic locking;
            // la versión "oficial" vendrá del backend tras sincronizar y refrescar.
        )
    }

    // Obtener todas las incidencias del usuario actual (desde caché local)
    fun getIncidencias(estado: String? = null): Flow<List<Incidencia>> {
        return authDataStore.userId.flatMapLatest { idStr ->
            val ownerId = idStr?.toIntOrNull() ?: 0
            incidenciaDao.getIncidenciasByOwner(ownerId).map { entities ->
                entities.map { it.toIncidencia(gson) }
            }
        }
    }

    fun observeIncidenciaById(id: Int): Flow<Incidencia?> {
        return incidenciaDao.observeIncidenciaById(id).map { it?.toIncidencia(gson) }
    }

    private fun nowString(): String = LocalDateTime.now().toString()

    fun getMensajes(incidenciaId: Int): Flow<List<Mensaje>> {
        return mensajeDao.getMensajesByIncidencia(incidenciaId).map { entities ->
            entities.map { it.toMensaje() }
        }
    }

    suspend fun refreshMensajesFromServer(incidenciaId: Int) {
        if (!canSendNow()) return
        val response = apiService.getMensajesIncidencia(incidenciaId)
        if (response.isSuccessful) {
            val mensajes = response.body() ?: emptyList()
            mensajeDao.deleteMensajesIncidencia(incidenciaId)
            mensajeDao.insertMensajes(mensajes.map { it.toEntity(syncStatus = "synced") })
        } else {
            throw Exception("Error al obtener mensajes: ${response.code()} ${response.message()}")
        }
    }

    suspend fun enviarMensajeOfflineFirst(incidenciaId: Int, contenido: String): Result<Mensaje> {
        val trimmed = contenido.trim()
        if (trimmed.isBlank()) return Result.failure(Exception("Mensaje vacío"))

        return if (canSendNow()) {
            try {
                val response = apiService.enviarMensaje(incidenciaId, MensajeCreate(trimmed))
                if (response.isSuccessful && response.body() != null) {
                    val created = response.body()!!
                    mensajeDao.insertMensaje(created.toEntity(syncStatus = "synced"))
                    Result.success(created)
                } else {
                    Result.failure(Exception(response.message() ?: "Error al enviar mensaje"))
                }
            } catch (e: Exception) {
                Result.failure(e)
            }
        } else {
            val localId = -kotlin.math.abs(System.currentTimeMillis().toInt())
            val local = Mensaje(
                id = localId,
                incidencia_id = incidenciaId,
                usuario_id = 0,
                usuario_nombre = "Pendiente de sincronizar",
                usuario_rol = "",
                contenido = trimmed,
                creado_en = nowString()
            )
            mensajeDao.insertMensaje(local.toEntity(syncStatus = "pending"))
            syncService.addPendingOperation(
                type = "CREATE",
                endpoint = "mensajes/incidencia/$incidenciaId",
                data = PendingMensajePayload(localId = localId, contenido = trimmed)
            )
            Result.success(local)
        }
    }

    fun getActuaciones(incidenciaId: Int): Flow<List<Actuacion>> {
        return actuacionDao.getActuacionesByIncidencia(incidenciaId).map { entities ->
            entities.map { it.toActuacion() }
        }
    }

    suspend fun refreshActuacionesFromServer(incidenciaId: Int) {
        if (!canSendNow()) return
        val response = apiService.getActuacionesIncidencia(incidenciaId)
        if (response.isSuccessful) {
            val actuaciones = response.body() ?: emptyList()
            actuacionDao.deleteActuacionesIncidencia(incidenciaId)
            actuacionDao.insertActuaciones(actuaciones.map { it.toEntity(syncStatus = "synced") })
        } else {
            throw Exception("Error al obtener actuaciones: ${response.code()} ${response.message()}")
        }
    }

    suspend fun crearActuacionOfflineFirst(actuacion: ActuacionCreate): Result<Actuacion> {
        return if (canSendNow()) {
            try {
                val response = apiService.crearActuacion(actuacion)
                if (response.isSuccessful && response.body() != null) {
                    val created = response.body()!!
                    actuacionDao.insertActuacion(created.toEntity(syncStatus = "synced"))
                    Result.success(created)
                } else {
                    Result.failure(Exception(response.message() ?: "Error al crear actuación"))
                }
            } catch (e: Exception) {
                Result.failure(e)
            }
        } else {
            val localId = -kotlin.math.abs(System.currentTimeMillis().toInt())
            val local = Actuacion(
                id = localId,
                incidencia_id = actuacion.incidencia_id,
                proveedor_id = 0,
                descripcion = actuacion.descripcion,
                fecha = actuacion.fecha,
                coste = actuacion.coste,
                creado_en = nowString(),
                proveedor = null
            )
            actuacionDao.insertActuacion(local.toEntity(syncStatus = "pending"))
            syncService.addPendingOperation(
                type = "CREATE",
                endpoint = "actuaciones",
                data = PendingActuacionPayload(
                    localId = localId,
                    incidencia_id = actuacion.incidencia_id,
                    descripcion = actuacion.descripcion,
                    fecha = actuacion.fecha,
                    coste = actuacion.coste
                )
            )
            Result.success(local)
        }
    }

    fun getDocumentos(incidenciaId: Int): Flow<List<Documento>> {
        return documentoDao.getDocumentosByIncidencia(incidenciaId).map { entities ->
            entities.map { it.toDocumento() }
        }
    }

    suspend fun refreshDocumentosFromServer(incidenciaId: Int) {
        if (!canSendNow()) return
        val response = apiService.getDocumentosIncidencia(incidenciaId)
        if (response.isSuccessful) {
            val documentos = response.body() ?: emptyList()
            // Solo borramos los documentos ya sincronizados; los pendientes/error se mantienen.
            documentoDao.deleteSyncedDocumentosIncidencia(incidenciaId)
            if (documentos.isNotEmpty()) {
                documentoDao.insertDocumentos(documentos.map { it.toEntity(syncStatus = "synced", localPath = null) })
            }
        } else {
            throw Exception("Error al obtener documentos: ${response.code()} ${response.message()}")
        }
    }

    suspend fun uploadDocumentoOfflineFirst(
        incidenciaId: Int,
        nombre: String,
        filePath: String,
        mimeType: String = "application/octet-stream",
        fileName: String = filePath.substringAfterLast("/")
    ): Result<Documento> {
        val safeNombre = nombre.trim().ifBlank { "Documento" }
        return if (canSendNow()) {
            try {
                val file = File(filePath)
                if (!file.exists()) return Result.failure(Exception("Archivo no encontrado"))
                val incidenciaIdPart = incidenciaId.toString().toRequestBody("text/plain".toMediaType())
                val nombrePart = safeNombre.toRequestBody("text/plain".toMediaType())
                val requestFile = file.asRequestBody(mimeType.toMediaType())
                val filePart = MultipartBody.Part.createFormData("archivo", fileName, requestFile)
                val response = apiService.uploadDocumento(incidenciaIdPart, nombrePart, filePart)
                if (response.isSuccessful) {
                    val created = response.body()
                    if (created != null) {
                        documentoDao.insertDocumento(created.toEntity(syncStatus = "synced", localPath = null))
                        Result.success(created)
                    } else {
                        // Si el backend no devuelve cuerpo, refrescar documentos desde servidor
                        refreshDocumentosFromServer(incidenciaId)
                        Result.success(
                            Documento(
                                id = 0,
                                incidencia_id = incidenciaId,
                                usuario_id = 0,
                                nombre = safeNombre,
                                nombre_archivo = fileName,
                                tipo_archivo = mimeType,
                                tamano = null,
                                creado_en = nowString(),
                                subido_por = null,
                                local_path = null
                            )
                        )
                    }
                } else {
                    Result.failure(Exception(response.message() ?: "Error al subir documento"))
                }
            } catch (e: Exception) {
                Result.failure(e)
            }
        } else {
            val localId = -kotlin.math.abs(System.currentTimeMillis().toInt())
            val file = File(filePath)
            val size = if (file.exists()) file.length().toInt().coerceAtLeast(0) else 0
            val local = Documento(
                id = localId,
                incidencia_id = incidenciaId,
                usuario_id = 0,
                nombre = safeNombre,
                nombre_archivo = fileName,
                tipo_archivo = mimeType,
                tamano = if (size > 0) size else null,
                creado_en = nowString(),
                subido_por = null,
                local_path = filePath
            )
            documentoDao.insertDocumento(local.toEntity(syncStatus = "pending", localPath = filePath))
            Result.success(local)
        }
    }

    suspend fun syncPendingDocumentos() {
        val pendientes = documentoDao.getPendingDocumentos()
        if (pendientes.isEmpty()) return

        for (doc in pendientes) {
            val path = doc.local_path ?: continue
            val file = File(path)
            if (!file.exists()) continue

            try {
                val incidenciaIdPart = doc.incidencia_id.toString().toRequestBody("text/plain".toMediaType())
                val nombrePart = doc.nombre.toRequestBody("text/plain".toMediaType())
                val mime = doc.tipo_archivo ?: "application/octet-stream"
                val requestFile = file.asRequestBody(mime.toMediaType())
                val filePart = MultipartBody.Part.createFormData("archivo", doc.nombre_archivo, requestFile)
                val response = apiService.uploadDocumento(incidenciaIdPart, nombrePart, filePart)
                if (response.isSuccessful) {
                    // Subida correcta: eliminamos el documento pendiente y refrescamos documentos desde servidor
                    documentoDao.deleteById(doc.id)
                    refreshDocumentosFromServer(doc.incidencia_id)
                } else {
                    // dejar como pendiente para reintentar
                    continue
                }
            } catch (_: Exception) {
                // dejar como pendiente para reintentar
                continue
            }
        }
    }
    
    // Refrescar incidencias desde el servidor (llamar manualmente cuando sea necesario)
    suspend fun refreshIncidenciasFromServer(estado: String? = null, userRol: String? = null) {
        refreshIncidencias(estado, userRol)
    }

    // Obtener una incidencia por ID
    suspend fun getIncidenciaById(id: Int): Incidencia? {
        val local = incidenciaDao.getIncidenciaById(id)

        // Si hay cambios locales pendientes/error, esa es la fuente de verdad para la UI.
        // No debemos sobreescribirla con la versión del servidor.
        if (local != null && local.syncStatus != "synced") {
            return local.toIncidencia(gson)
        }

        val ownerId = currentOwnerId()
        // Primero intentar actualizar desde el servidor si hay internet
        if (networkMonitor.isCurrentlyOnline()) {
            try {
                val response = apiService.getIncidencia(id)
                if (response.isSuccessful && response.body() != null) {
                    val incidencia = response.body()!!
                    // Solo upsert si no hay una versión local pendiente/error
                    val currentLocal = incidenciaDao.getIncidenciaById(id)
                    if (currentLocal == null || currentLocal.syncStatus == "synced") {
                        incidenciaDao.insertIncidencia(incidencia.toEntity(gson, ownerId).copy(syncStatus = "synced"))
                    }
                    return incidencia
                }
            } catch (e: Exception) {
                // Si falla, usar caché local
            }
        }
        
        // Usar caché local
        return (local ?: incidenciaDao.getIncidenciaById(id))?.toIncidencia(gson)
    }

    /**
     * Determina si en este momento se puede enviar tráfico al backend respetando la opción "solo WiFi".
     *
     * - Si no hay conexión a internet, devuelve false.
     * - Si "solo WiFi" está desactivado, mientras haya internet devuelve true.
     * - Si "solo WiFi" está activado, solo devuelve true cuando la conexión actual es WiFi.
     */
    private suspend fun canSendNow(): Boolean {
        if (!networkMonitor.isCurrentlyOnline()) return false

        val syncOnlyWifi = settingsDataStore.syncOnlyWifi.first()
        return if (!syncOnlyWifi) {
            true
        } else {
            networkMonitor.isWifiConnected()
        }
    }

    // Crear incidencia
    suspend fun createIncidencia(incidencia: IncidenciaCreate, inmueble: InmuebleSimple? = null): Result<Incidencia> {
        val ownerId = currentOwnerId()
        return if (canSendNow()) {
            // Si se puede enviar ahora (respeta "solo WiFi"), enviar directamente
            try {
                val response = apiService.crearIncidencia(incidencia)
                if (response.isSuccessful && response.body() != null) {
                    val created = response.body()!!
                    val baseEntity = created.toEntity(gson, ownerId)
                    // Si el backend no devuelve el objeto "inmueble", conservamos la selección del formulario
                    // para que el listado/detalle offline muestre referencia y dirección.
                    val patchedEntity = if (
                        inmueble != null &&
                        (baseEntity.inmueble_referencia.isNullOrBlank() || baseEntity.inmueble_direccion.isNullOrBlank())
                    ) {
                        baseEntity.copy(
                            inmueble_referencia = inmueble.referencia,
                            inmueble_direccion = inmueble.direccion
                        )
                    } else {
                        baseEntity
                    }
                    incidenciaDao.insertIncidencia(patchedEntity)
                    // Muchos endpoints de "create" devuelven una incidencia incompleta (sin inmueble/creador/historial).
                    // Forzamos refresco del detalle para rellenar campos usados por la UI (p.ej. permisos de propietario).
                    try {
                        getIncidenciaById(created.id)
                    } catch (_: Exception) {
                        // Si falla, dejamos la versión devuelta por create.
                    }
                    Result.success(created)
                } else {
                    Result.failure(Exception(response.message() ?: "Error al crear incidencia"))
                }
            } catch (e: Exception) {
                Result.failure(e)
            }
        } else {
            // Si no hay internet, guardar localmente y agregar a cola de sincronización
            val tempId = -kotlin.math.abs(System.currentTimeMillis().toInt()) // ID temporal (negativo)
            val localIncidencia = Incidencia(
                id = tempId,
                titulo = incidencia.titulo,
                descripcion = incidencia.descripcion,
                prioridad = incidencia.prioridad,
                estado = "abierta",
                inmueble_id = incidencia.inmueble_id,
                creador_usuario_id = ownerId,
                fecha_alta = java.time.LocalDateTime.now().toString(),
                version = 1,
                inmueble = inmueble
            )
            
            incidenciaDao.insertIncidencia(localIncidencia.toEntity(gson, ownerId).copy(syncStatus = "pending"))
            // Guardamos también el ID local temporal para poder remapearlo al ID real al sincronizar
            syncService.addPendingOperation(
                "CREATE",
                "incidencias",
                com.tomoko.fyntra.data.sync.PendingCreateIncidenciaPayload(
                    localId = tempId,
                    incidencia = incidencia
                )
            )
            
            Result.success(localIncidencia)
        }
    }

    // Actualizar incidencia
    suspend fun updateIncidencia(id: Int, update: IncidenciaUpdate): Result<Incidencia> {
        val existing = incidenciaDao.getIncidenciaById(id)
        val ownerId = currentOwnerId()
        
        return if (canSendNow()) {
            // Si se puede enviar ahora (respeta "solo WiFi"), enviar directamente
            try {
                val response = apiService.actualizarIncidencia(id, update)
                if (response.isSuccessful && response.body() != null) {
                    val updated = response.body()!!
                    incidenciaDao.insertIncidencia(updated.toEntity(gson, ownerId))
                    Result.success(updated)
                } else {
                    Result.failure(Exception(response.message() ?: "Error al actualizar incidencia"))
                }
            } catch (e: Exception) {
                Result.failure(e)
            }
        } else {
            // Si no se puede enviar ahora (respeta "solo WiFi"), actualizar localmente y agregar a cola
            existing?.let {
                val updatedEntity = applyLocalUpdate(it, update).copy(
                    syncStatus = "pending",
                    lastSyncTimestamp = System.currentTimeMillis()
                )
                incidenciaDao.updateIncidencia(updatedEntity)
                syncService.addPendingOperation("UPDATE", "incidencias/$id", update)
                
                // Retornar la versión local actualizada
                Result.success(updatedEntity.toIncidencia(gson))
            } ?: Result.failure(Exception("Incidencia no encontrada"))
        }
    }

    // Eliminar incidencia
    suspend fun deleteIncidencia(id: Int): Result<Unit> {
        return if (canSendNow()) {
            // Si se puede enviar ahora (respeta "solo WiFi"), eliminar directamente
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

        // Si "solo WiFi" está activo y no hay WiFi, seguimos pudiendo REFRESCAR (lecturas) desde servidor,
        // pero NO debemos hacer un wipe completo de la tabla porque podríamos mezclar/duplicar con pendientes.
        // En ese caso hacemos "merge/upsert" de lo que venga del backend y mantenemos los pending locales.
        val syncOnlyWifi = settingsDataStore.syncOnlyWifi.first()
        val shouldMergeOnly = syncOnlyWifi && !networkMonitor.isWifiConnected()
        val ownerId = currentOwnerId()
        
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
                if (!shouldMergeOnly) {
                    // En este punto asumimos que las operaciones pendientes ya se han sincronizado.
                    // Limpiamos toda la tabla y la rellenamos con el estado oficial del servidor.
                    incidenciaDao.deleteAllIncidencias()
                }
                if (incidencias != null && incidencias.isNotEmpty()) {
                    // Upsert: REPLACE por PK mantiene coherencia.
                    // - Con mergeOnly: no borra pendientes locales (IDs temporales/negativos), pero inserta las del servidor.
                    // - Con wipe: deja una foto limpia del servidor.
                    if (!shouldMergeOnly) {
                        incidenciaDao.insertIncidencias(incidencias.map { it.toEntity(gson, ownerId).copy(syncStatus = "synced") })
                    } else {
                        // Merge seguro: si existe local pending/error con el mismo ID, NO la sobreescribimos.
                        val safeToInsert = incidencias.filter { inc ->
                            val localExisting = incidenciaDao.getIncidenciaById(inc.id)
                            localExisting == null || localExisting.syncStatus == "synced"
                        }
                        if (safeToInsert.isNotEmpty()) {
                            incidenciaDao.insertIncidencias(safeToInsert.map { it.toEntity(gson, ownerId).copy(syncStatus = "synced") })
                        }
                    }
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

    /**
     * Borra todos los datos locales (incidencias, mensajes, documentos, actuaciones, operaciones pendientes).
     * Debe llamarse al hacer login con otro usuario para que la caché sea solo del usuario actual.
     */
    suspend fun clearAllLocalData() {
        incidenciaDao.deleteAllIncidencias()
        mensajeDao.deleteAllMensajes()
        documentoDao.deleteAllDocumentos()
        actuacionDao.deleteAllActuaciones()
        database.pendingOperationDao().deleteAllOperations()
    }
}

// Extensiones para convertir entre Entity y Model
private fun IncidenciaEntity.toIncidencia(gson: Gson): Incidencia {
    val historialList = historial_json?.let { json ->
        try {
            gson.fromJson<List<HistorialIncidencia>>(json, object : TypeToken<List<HistorialIncidencia>>() {}.type)
        } catch (_: Exception) {
            null
        }
    } ?: null
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
        creado_en = null,
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
        historial = historialList,
        actuaciones_count = 0,
        documentos_count = 0,
        mensajes_count = 0
    )
}

private fun Incidencia.toEntity(gson: Gson, ownerUserId: Int = 0): IncidenciaEntity {
    val historialJson = historial?.let { gson.toJson(it) }
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
        proveedor_especialidad = proveedor?.especialidad,
        historial_json = historialJson,
        owner_user_id = ownerUserId
    )
}

private fun MensajeEntity.toMensaje(): Mensaje {
    return Mensaje(
        id = id,
        incidencia_id = incidencia_id,
        usuario_id = usuario_id,
        usuario_nombre = usuario_nombre,
        usuario_rol = usuario_rol,
        contenido = contenido,
        creado_en = creado_en
    )
}

private fun Mensaje.toEntity(syncStatus: String): MensajeEntity {
    return MensajeEntity(
        id = id,
        incidencia_id = incidencia_id,
        usuario_id = usuario_id,
        usuario_nombre = usuario_nombre,
        usuario_rol = usuario_rol,
        contenido = contenido,
        creado_en = creado_en,
        syncStatus = syncStatus
    )
}

private fun ActuacionEntity.toActuacion(): Actuacion {
    return Actuacion(
        id = id,
        incidencia_id = incidencia_id,
        proveedor_id = proveedor_id,
        descripcion = descripcion,
        fecha = fecha,
        coste = coste,
        creado_en = creado_en,
        proveedor = proveedor_nombre?.let { com.tomoko.fyntra.data.models.ProveedorSimple(id = proveedor_id, nombre = it) }
    )
}

private fun Actuacion.toEntity(syncStatus: String): ActuacionEntity {
    return ActuacionEntity(
        id = id,
        incidencia_id = incidencia_id,
        proveedor_id = proveedor_id,
        descripcion = descripcion,
        fecha = fecha,
        coste = coste,
        creado_en = creado_en,
        proveedor_nombre = proveedor?.nombre,
        syncStatus = syncStatus
    )
}

private fun DocumentoEntity.toDocumento(): Documento {
    return Documento(
        id = id,
        incidencia_id = incidencia_id,
        usuario_id = usuario_id,
        nombre = nombre,
        nombre_archivo = nombre_archivo,
        tipo_archivo = tipo_archivo,
        tamano = tamano,
        creado_en = creado_en,
        subido_por = subido_por,
        local_path = local_path
    )
}

private fun Documento.toEntity(syncStatus: String, localPath: String?): DocumentoEntity {
    return DocumentoEntity(
        id = id,
        incidencia_id = incidencia_id,
        usuario_id = usuario_id,
        nombre = nombre,
        nombre_archivo = nombre_archivo,
        tipo_archivo = tipo_archivo,
        tamano = tamano,
        creado_en = creado_en,
        subido_por = subido_por,
        local_path = localPath,
        syncStatus = syncStatus
    )
}
