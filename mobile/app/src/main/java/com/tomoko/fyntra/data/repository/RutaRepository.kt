package com.tomoko.fyntra.data.repository

import com.google.gson.Gson
import com.tomoko.fyntra.data.local.database.dao.RutaDao
import com.tomoko.fyntra.data.local.database.entities.RutaCacheEntity
import com.tomoko.fyntra.data.models.Ruta
import com.tomoko.fyntra.data.sync.NetworkMonitor
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext

/** Resultado de getMisRutas: lista de rutas y si provienen de caché (sin conexión). */
data class MisRutasResult(val rutas: List<Ruta>, val fromCache: Boolean)

/** Resultado de getRutaById: ruta opcional y si proviene de caché. */
data class RutaResult(val ruta: Ruta?, val fromCache: Boolean)

/**
 * Repositorio de rutas con caché local para ver "mis rutas" sin conexión.
 * Si hay red: obtiene del API y guarda en caché. Si no hay red: devuelve desde caché.
 */
class RutaRepository(
    private val authRepository: AuthRepository,
    private val rutaDao: RutaDao,
    private val networkMonitor: NetworkMonitor,
    private val gson: Gson
) {
    /**
     * Obtiene la lista de "mis rutas". Con conexión: pide al API y actualiza caché. Sin conexión: devuelve caché.
     * [MisRutasResult.fromCache] indica si se usó solo caché (sin conexión).
     */
    suspend fun getMisRutas(): MisRutasResult = withContext(Dispatchers.IO) {
        if (networkMonitor.isCurrentlyOnline()) {
            try {
                val response = authRepository.getApiServiceInstance().getMisRutas()
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
                val response = authRepository.getApiServiceInstance().getRuta(rutaId)
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
