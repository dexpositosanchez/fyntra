package com.tomoko.fyntra.data.repository

import com.tomoko.fyntra.data.api.ApiService
import com.tomoko.fyntra.data.api.RetrofitModule
import com.tomoko.fyntra.data.local.AuthDataStore
import com.tomoko.fyntra.data.models.LoginRequest
import com.tomoko.fyntra.data.models.LoginResponse

class AuthRepository(
    private val authDataStore: AuthDataStore
) {
    private var apiService: ApiService? = null

    private fun getApiService(): ApiService {
        if (apiService == null) {
            val token = kotlinx.coroutines.runBlocking { authDataStore.getToken() }
            apiService = RetrofitModule.createApiServiceWithToken(authDataStore, token)
        }
        return apiService!!
    }

    suspend fun login(email: String, password: String): Result<LoginResponse> {
        return try {
            val request = LoginRequest(email, password)
            val apiService = RetrofitModule.createApiServiceWithToken(authDataStore, null)
            val response = apiService.login(request)
            
            if (response.isSuccessful && response.body() != null) {
                val loginResponse = response.body()!!
                authDataStore.saveToken(loginResponse.access_token)
                authDataStore.saveUser(
                    loginResponse.usuario.id.toString(),
                    loginResponse.usuario.email,
                    loginResponse.usuario.nombre,
                    loginResponse.usuario.rol
                )
                // Actualizar API service con el nuevo token
                this.apiService = RetrofitModule.createApiServiceWithToken(
                    authDataStore,
                    loginResponse.access_token
                )
                Result.success(loginResponse)
            } else {
                val bodyDetail = response.errorBody()?.string()?.let { body ->
                    try {
                        com.google.gson.Gson().fromJson(body, Map::class.java)["detail"]?.toString()
                    } catch (e: Exception) { null }
                }
                val errorMsg = bodyDetail ?: when {
                    response.code() == 401 -> "Credenciales incorrectas"
                    response.code() == 429 -> "Demasiados intentos. Acceso bloqueado temporalmente."
                    response.code() == 404 -> "Servidor no encontrado. Verifica que el backend esté corriendo en http://10.84.89.211:8000"
                    response.code() >= 500 -> "Error del servidor"
                    else -> response.message() ?: "Error de autenticación (código: ${response.code()})"
                }
                Result.failure(Exception(errorMsg))
            }
        } catch (e: java.net.UnknownHostException) {
            Result.failure(Exception("No se puede conectar al servidor. Verifica:\n1. Que el backend esté corriendo\n2. Que la IP 10.84.89.211 sea correcta\n3. Que el dispositivo esté en la misma red WiFi"))
        } catch (e: java.net.ConnectException) {
            Result.failure(Exception("No se puede conectar al servidor en 10.84.89.211:8000. Verifica que el backend esté corriendo y accesible."))
        } catch (e: Exception) {
            Result.failure(Exception("Error de conexión: ${e.message}"))
        }
    }

    suspend fun logout() {
        authDataStore.clear()
        apiService = null
    }

    suspend fun isLoggedIn(): Boolean {
        return authDataStore.getToken() != null
    }

    fun getApiServiceInstance(): ApiService {
        return getApiService()
    }
}

