package com.tomoko.fyntra.data.repository

import com.google.gson.Gson
import com.tomoko.fyntra.data.api.ApiService
import com.tomoko.fyntra.data.local.SettingsDataStore
import com.tomoko.fyntra.data.local.database.dao.RutaDao
import com.tomoko.fyntra.data.local.database.entities.RutaCacheEntity
import com.tomoko.fyntra.data.models.EntregaConfirmacion
import com.tomoko.fyntra.data.models.Parada
import com.tomoko.fyntra.data.models.Ruta
import com.tomoko.fyntra.data.sync.NetworkMonitor
import com.tomoko.fyntra.data.sync.SyncService
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.withContext
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.MultipartBody
import okhttp3.RequestBody.Companion.asRequestBody
import okhttp3.RequestBody.Companion.toRequestBody
import java.io.File
import java.time.LocalDateTime

/** Resultado de getMisRutas: lista de rutas y si provienen de caché (sin conexión). */
data class MisRutasResult(val rutas: List<Ruta>, val fromCache: Boolean)

/** Resultado de getRutaById: ruta opcional y si proviene de caché. */
data class RutaResult(val ruta: Ruta?, val fromCache: Boolean)

/**
 * Repositorio de rutas con caché local para ver "mis rutas" sin conexión.
 * Si hay red: obtiene del API y guarda en caché. Si no hay red: devuelve desde caché.
 */
class RutaRepository(
    private val apiService: ApiService,
    private val rutaDao: RutaDao,
    private val networkMonitor: NetworkMonitor,
    private val gson: Gson,
    private val syncService: SyncService,
    private val settingsDataStore: SettingsDataStore
) {
    private data class PendingCompletarParadaPayload(
        val rutaId: Int,
        val paradaId: Int,
        val accion: String,
        val fotoPath: String? = null,
        val firmaPath: String? = null
    )

    private suspend fun canSendNow(): Boolean {
        if (!networkMonitor.isCurrentlyOnline()) return false
        val syncOnlyWifi = settingsDataStore.syncOnlyWifi.first()
        return if (!syncOnlyWifi) true else networkMonitor.isWifiConnected()
    }

    /**
     * Obtiene la lista de "mis rutas". Con conexión: pide al API y actualiza caché. Sin conexión: devuelve caché.
     * [MisRutasResult.fromCache] indica si se usó solo caché (sin conexión).
     */
    suspend fun getMisRutas(): MisRutasResult = withContext(Dispatchers.IO) {
        if (networkMonitor.isCurrentlyOnline()) {
            try {
                val response = apiService.getMisRutas()
                if (response.isSuccessful) {
                    val list = response.body() ?: emptyList()
                    saveMisRutasToCache(list)
                    return@withContext MisRutasResult(list, fromCache = false)
                }
            } catch (_: Exception) { }
        }
        MisRutasResult(loadMisRutasFromCache(), fromCache = true)
    }

    /**
     * Obtiene una ruta por ID. Con conexión: pide al API y actualiza esa ruta en caché. Sin conexión: devuelve desde caché.
     * [RutaResult.fromCache] indica si se usó solo caché.
     */
    suspend fun getRutaById(rutaId: Int): RutaResult = withContext(Dispatchers.IO) {
        if (networkMonitor.isCurrentlyOnline()) {
            try {
                val response = apiService.getRuta(rutaId)
                if (response.isSuccessful) {
                    val ruta = response.body()
                    if (ruta != null) {
                        rutaDao.insert(RutaCacheEntity(ruta.id, gson.toJson(ruta)))
                        return@withContext RutaResult(ruta, fromCache = false)
                    }
                }
            } catch (_: Exception) { }
        }
        RutaResult(loadRutaFromCache(rutaId), fromCache = true)
    }

    suspend fun iniciarRutaOfflineFirst(rutaId: Int): Result<Ruta> = withContext(Dispatchers.IO) {
        if (canSendNow()) {
            try {
                val response = apiService.iniciarRuta(rutaId)
                if (response.isSuccessful && response.body() != null) {
                    val ruta = response.body()!!
                    rutaDao.insert(RutaCacheEntity(ruta.id, gson.toJson(ruta)))
                    return@withContext Result.success(ruta)
                }
                return@withContext Result.failure(Exception(response.message() ?: "Error al iniciar ruta"))
            } catch (e: Exception) {
                return@withContext Result.failure(e)
            }
        } else {
            val cached = loadRutaFromCache(rutaId)
            val updated = cached?.copy(
                estado = "en_progreso",
                fecha_inicio = LocalDateTime.now().toString()
            )
            if (updated != null) {
                rutaDao.insert(RutaCacheEntity(updated.id, gson.toJson(updated)))
            }
            syncService.addPendingOperation("UPDATE", "rutas/$rutaId/iniciar", mapOf("rutaId" to rutaId))
            Result.success(updated ?: Ruta(rutaId, null, 0, 0, null, LocalDateTime.now().toString(), null, "en_progreso", null, null, cached?.paradas))
        }
    }

    suspend fun finalizarRutaOfflineFirst(rutaId: Int): Result<Ruta> = withContext(Dispatchers.IO) {
        if (canSendNow()) {
            try {
                val response = apiService.finalizarRuta(rutaId)
                if (response.isSuccessful && response.body() != null) {
                    val ruta = response.body()!!
                    rutaDao.insert(RutaCacheEntity(ruta.id, gson.toJson(ruta)))
                    return@withContext Result.success(ruta)
                }
                return@withContext Result.failure(Exception(response.message() ?: "Error al finalizar ruta"))
            } catch (e: Exception) {
                return@withContext Result.failure(e)
            }
        } else {
            val cached = loadRutaFromCache(rutaId)
            val updated = cached?.copy(
                estado = "finalizada",
                fecha_fin = LocalDateTime.now().toString()
            )
            if (updated != null) {
                rutaDao.insert(RutaCacheEntity(updated.id, gson.toJson(updated)))
            }
            syncService.addPendingOperation("UPDATE", "rutas/$rutaId/finalizar", mapOf("rutaId" to rutaId))
            Result.success(updated ?: Ruta(rutaId, null, 0, 0, null, cached?.fecha_inicio, LocalDateTime.now().toString(), "finalizada", null, null, cached?.paradas))
        }
    }

    suspend fun completarParadaOfflineFirst(
        rutaId: Int,
        paradaId: Int,
        accion: String,
        fotoPath: String? = null,
        firmaPath: String? = null
    ): Result<Parada> = withContext(Dispatchers.IO) {
        if (canSendNow()) {
            try {
                val accionBody = accion.toRequestBody("text/plain".toMediaType())
                val fotoPart = fotoPath?.let { path ->
                    val file = File(path)
                    if (file.exists()) {
                        val body = file.asRequestBody("application/octet-stream".toMediaType())
                        MultipartBody.Part.createFormData("foto", file.name, body)
                    } else null
                }
                val firmaPart = firmaPath?.let { path ->
                    val file = File(path)
                    if (file.exists()) {
                        val body = file.asRequestBody("application/octet-stream".toMediaType())
                        MultipartBody.Part.createFormData("firma", file.name, body)
                    } else null
                }
                val response = apiService.completarParada(
                    rutaId = rutaId,
                    paradaId = paradaId,
                    accion = accionBody,
                    foto = fotoPart,
                    firma = firmaPart
                )
                if (response.isSuccessful && response.body() != null) {
                    val parada = response.body()!!
                    // refrescar ruta en caché (best-effort)
                    val rutaResponse = apiService.getRuta(rutaId)
                    if (rutaResponse.isSuccessful && rutaResponse.body() != null) {
                        val ruta = rutaResponse.body()!!
                        rutaDao.insert(RutaCacheEntity(ruta.id, gson.toJson(ruta)))
                    }
                    return@withContext Result.success(parada)
                }
                return@withContext Result.failure(Exception(response.message() ?: "Error al completar parada"))
            } catch (e: Exception) {
                return@withContext Result.failure(e)
            }
        }

        val cached = loadRutaFromCache(rutaId)
        val updatedParada = cached?.paradas
            ?.firstOrNull { it.id == paradaId }
            ?.copy(
                estado = "completada",
                fecha_hora_completada = LocalDateTime.now().toString()
            )

        if (cached != null && updatedParada != null) {
            val updatedParadas = cached.paradas?.map { if (it.id == paradaId) updatedParada else it }
            val updatedRuta = cached.copy(paradas = updatedParadas)
            rutaDao.insert(RutaCacheEntity(updatedRuta.id, gson.toJson(updatedRuta)))
        }

        syncService.addPendingOperation(
            "UPDATE",
            "rutas/$rutaId/paradas/$paradaId/completar",
            PendingCompletarParadaPayload(rutaId = rutaId, paradaId = paradaId, accion = accion, fotoPath = fotoPath, firmaPath = firmaPath)
        )

        Result.success(updatedParada ?: Parada(paradaId, rutaId, 0, 0, "", null, null, LocalDateTime.now().toString(), "completada", null, null, null))
    }

    suspend fun confirmarEntregaOfflineFirst(confirmacion: EntregaConfirmacion): Result<Unit> = withContext(Dispatchers.IO) {
        if (canSendNow()) {
            try {
                val response = apiService.confirmarEntrega(confirmacion.ruta_id, confirmacion)
                if (response.isSuccessful) return@withContext Result.success(Unit)
                return@withContext Result.failure(Exception(response.message() ?: "Error al confirmar entrega"))
            } catch (e: Exception) {
                return@withContext Result.failure(e)
            }
        } else {
            // Actualizar caché (best-effort): marcar pedido como entregado
            val cached = loadRutaFromCache(confirmacion.ruta_id)
            if (cached?.paradas != null) {
                val updatedParadas = cached.paradas.map { parada ->
                    if (parada.pedido_id == confirmacion.pedido_id) {
                        parada.copy(
                            pedido = parada.pedido?.copy(estado = "entregado"),
                            fecha_hora_completada = parada.fecha_hora_completada ?: LocalDateTime.now().toString()
                        )
                    } else parada
                }
                val updatedRuta = cached.copy(paradas = updatedParadas)
                rutaDao.insert(RutaCacheEntity(updatedRuta.id, gson.toJson(updatedRuta)))
            }
            syncService.addPendingOperation("POST", "rutas/${confirmacion.ruta_id}/confirmar-entrega", confirmacion)
            Result.success(Unit)
        }
    }

    private suspend fun saveMisRutasToCache(rutas: List<Ruta>) {
        rutaDao.deleteAll()
        if (rutas.isEmpty()) return
        val now = System.currentTimeMillis()
        val entities = rutas.map { RutaCacheEntity(it.id, gson.toJson(it), now) }
        rutaDao.insertAll(entities)
    }

    private suspend fun loadMisRutasFromCache(): List<Ruta> {
        val entities = rutaDao.getAll()
        if (entities.isEmpty()) return emptyList()
        return entities.mapNotNull { entity ->
            try {
                gson.fromJson(entity.rutaJson, Ruta::class.java)
            } catch (_: Exception) {
                null
            }
        }
    }

    private suspend fun loadRutaFromCache(rutaId: Int): Ruta? {
        val entity = rutaDao.getById(rutaId) ?: return null
        return try {
            gson.fromJson(entity.rutaJson, Ruta::class.java)
        } catch (_: Exception) {
            null
        }
    }
}
