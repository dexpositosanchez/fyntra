package com.tomoko.fyntra.data.repository

import com.tomoko.fyntra.data.api.ApiService
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
import com.tomoko.fyntra.data.models.Mensaje
import com.tomoko.fyntra.data.models.MensajeCreate
import com.tomoko.fyntra.data.models.Incidencia
import com.tomoko.fyntra.data.models.IncidenciaCreate
import com.tomoko.fyntra.data.models.IncidenciaUpdate
import com.tomoko.fyntra.data.sync.NetworkMonitor
import com.tomoko.fyntra.data.sync.SyncService
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.first
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
    private val settingsDataStore: SettingsDataStore
) {
    private val incidenciaDao: IncidenciaDao = database.incidenciaDao()
    private val mensajeDao: MensajeDao = database.mensajeDao()
    private val actuacionDao: ActuacionDao = database.actuacionDao()
    private val documentoDao: DocumentoDao = database.documentoDao()

    private data class PendingMensajePayload(val localId: Int, val contenido: String)
    private data class PendingActuacionPayload(val localId: Int, val incidencia_id: Int, val descripcion: String, val fecha: String, val coste: Double?)
    private data class PendingDocumentoPayload(val localId: Int, val incidencia_id: Int, val nombre: String, val filePath: String)

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

    // Obtener todas las incidencias (desde caché local, actualizando si hay internet)
    fun getIncidencias(estado: String? = null): Flow<List<Incidencia>> {
        // Retornar datos desde caché local
        // La actualización se hará automáticamente cuando haya conexión
        return incidenciaDao.getAllIncidencias().map { entities ->
            entities.map { it.toIncidencia() }
        }
    }

    fun observeIncidenciaById(id: Int): Flow<Incidencia?> {
        return incidenciaDao.observeIncidenciaById(id).map { it?.toIncidencia() }
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
            documentoDao.deleteDocumentosIncidencia(incidenciaId)
            documentoDao.insertDocumentos(documentos.map { it.toEntity(syncStatus = "synced", localPath = null) })
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
                if (response.isSuccessful && response.body() != null) {
                    val created = response.body()!!
                    documentoDao.insertDocumento(created.toEntity(syncStatus = "synced", localPath = null))
                    Result.success(created)
                } else {
                    Result.failure(Exception(response.message() ?: "Error al subir documento"))
                }
            } catch (e: Exception) {
                Result.failure(e)
            }
        } else {
            val localId = -kotlin.math.abs(System.currentTimeMillis().toInt())
            val local = Documento(
                id = localId,
                incidencia_id = incidenciaId,
                usuario_id = 0,
                nombre = safeNombre,
                nombre_archivo = fileName,
                tipo_archivo = null,
                tamano = null,
                creado_en = nowString(),
                subido_por = "Pendiente de sincronizar"
            )
            documentoDao.insertDocumento(local.toEntity(syncStatus = "pending", localPath = filePath))
            syncService.addPendingOperation(
                type = "UPLOAD",
                endpoint = "documentos",
                data = PendingDocumentoPayload(localId = localId, incidencia_id = incidenciaId, nombre = safeNombre, filePath = filePath)
            )
            Result.success(local)
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
            return local.toIncidencia()
        }

        // Primero intentar actualizar desde el servidor si hay internet
        if (networkMonitor.isCurrentlyOnline()) {
            try {
                val response = apiService.getIncidencia(id)
                if (response.isSuccessful && response.body() != null) {
                    val incidencia = response.body()!!
                    // Solo upsert si no hay una versión local pendiente/error
                    val currentLocal = incidenciaDao.getIncidenciaById(id)
                    if (currentLocal == null || currentLocal.syncStatus == "synced") {
                        incidenciaDao.insertIncidencia(incidencia.toEntity().copy(syncStatus = "synced"))
                    }
                    return incidencia
                }
            } catch (e: Exception) {
                // Si falla, usar caché local
            }
        }
        
        // Usar caché local
        return (local ?: incidenciaDao.getIncidenciaById(id))?.toIncidencia()
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
    suspend fun createIncidencia(incidencia: IncidenciaCreate): Result<Incidencia> {
        return if (canSendNow()) {
            // Si se puede enviar ahora (respeta "solo WiFi"), enviar directamente
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
        
        return if (canSendNow()) {
            // Si se puede enviar ahora (respeta "solo WiFi"), enviar directamente
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
            // Si no se puede enviar ahora (respeta "solo WiFi"), actualizar localmente y agregar a cola
            existing?.let {
                val updatedEntity = applyLocalUpdate(it, update).copy(
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
                        incidenciaDao.insertIncidencias(incidencias.map { it.toEntity().copy(syncStatus = "synced") })
                    } else {
                        // Merge seguro: si existe local pending/error con el mismo ID, NO la sobreescribimos.
                        val safeToInsert = incidencias.filter { inc ->
                            val localExisting = incidenciaDao.getIncidenciaById(inc.id)
                            localExisting == null || localExisting.syncStatus == "synced"
                        }
                        if (safeToInsert.isNotEmpty()) {
                            incidenciaDao.insertIncidencias(safeToInsert.map { it.toEntity().copy(syncStatus = "synced") })
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
        creado_en = null, // No se almacena en la entidad local
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
        subido_por = subido_por
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
