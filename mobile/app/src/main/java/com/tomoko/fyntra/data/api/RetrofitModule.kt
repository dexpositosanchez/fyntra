package com.tomoko.fyntra.data.api

import com.google.gson.Gson
import com.google.gson.GsonBuilder
import com.tomoko.fyntra.data.local.AuthDataStore
import okhttp3.Interceptor
import okhttp3.OkHttpClient
import okhttp3.logging.HttpLoggingInterceptor
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory
import java.util.concurrent.TimeUnit

object RetrofitModule {
    // La URL base se obtiene de ApiConfig
    // Para cambiar la IP, edita ApiConfig.kt
    private val BASE_URL = ApiConfig.BASE_URL
    
    private val gson: Gson = GsonBuilder()
        .setLenient()
        .create()

    private fun createAuthInterceptor(authDataStore: AuthDataStore): Interceptor {
        return Interceptor { chain ->
            val request = chain.request().newBuilder()
            // El token se añadirá dinámicamente desde el ViewModel
            request.addHeader("Content-Type", "application/json")
            chain.proceed(request.build())
        }
    }
    
    fun createApiServiceWithToken(authDataStore: AuthDataStore, token: String?): ApiService {
        val client = OkHttpClient.Builder()
            .addInterceptor { chain ->
                val request = chain.request().newBuilder()
                
                // Siempre obtener el token más reciente del AuthDataStore
                val authToken = kotlinx.coroutines.runBlocking {
                    authDataStore.getToken()
                }
                
                if (authToken != null && authToken.isNotBlank()) {
                    request.addHeader("Authorization", "Bearer $authToken")
                }
                request.addHeader("Content-Type", "application/json")
                chain.proceed(request.build())
            }
            .addInterceptor(HttpLoggingInterceptor().apply {
                level = HttpLoggingInterceptor.Level.BODY
            })
            .connectTimeout(30, TimeUnit.SECONDS)
            .readTimeout(30, TimeUnit.SECONDS)
            .writeTimeout(30, TimeUnit.SECONDS)
            .build()

        val retrofit = Retrofit.Builder()
            .baseUrl(BASE_URL)
            .client(client)
            .addConverterFactory(GsonConverterFactory.create(gson))
            .build()

        return retrofit.create(ApiService::class.java)
    }

    private fun createOkHttpClient(authDataStore: AuthDataStore): OkHttpClient {
        val loggingInterceptor = HttpLoggingInterceptor().apply {
            level = HttpLoggingInterceptor.Level.BODY
        }

        return OkHttpClient.Builder()
            .addInterceptor(createAuthInterceptor(authDataStore))
            .addInterceptor(loggingInterceptor)
            .connectTimeout(30, TimeUnit.SECONDS)
            .readTimeout(30, TimeUnit.SECONDS)
            .writeTimeout(30, TimeUnit.SECONDS)
            .build()
    }

    fun createApiService(authDataStore: AuthDataStore): ApiService {
        val retrofit = Retrofit.Builder()
            .baseUrl(BASE_URL)
            .client(createOkHttpClient(authDataStore))
            .addConverterFactory(GsonConverterFactory.create(gson))
            .build()

        return retrofit.create(ApiService::class.java)
    }
}

