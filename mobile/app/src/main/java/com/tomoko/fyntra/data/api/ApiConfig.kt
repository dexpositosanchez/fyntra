package com.tomoko.fyntra.data.api

/**
 * Configuración de la API
 * 
 * Para cambiar la IP del servidor, modifica la constante BASE_URL_IP
 * 
 * OPCIONES:
 * - Para EMULADOR Android: usar "10.0.2.2"
 * - Para DISPOSITIVO FÍSICO en misma WiFi: usar la IP local de tu Mac (ej: "192.168.1.128")
 * - Para HOTSPOT del móvil: usar la IP que te asigne el hotspot (ej: "192.168.43.1" o "172.20.10.1")
 * - Para ngrok: usar la URL de ngrok (ej: "xxxx.ngrok.io")
 */
object ApiConfig {
    // ============================================
    // ⚙️ CAMBIA ESTA IP SEGÚN TU ENTORNO ⚙️
    // ============================================
    private const val BASE_URL_IP = "10.85.227.211"
    private const val BASE_URL_PORT = "8000"
    private const val BASE_URL_PATH = "/api/"
    
    // Protocolo (http o https)
    // Usa "https" solo si usas ngrok o tienes SSL configurado
    private const val BASE_URL_PROTOCOL = "http"
    
    // Construir la URL completa
    val BASE_URL: String
        get() = "$BASE_URL_PROTOCOL://$BASE_URL_IP:$BASE_URL_PORT$BASE_URL_PATH"
    
    /**
     * Método helper para cambiar la IP fácilmente
     * Úsalo si prefieres cambiar la IP programáticamente
     */
    fun getBaseUrl(ip: String? = null, port: String? = null, useHttps: Boolean = false): String {
        val protocol = if (useHttps) "https" else "http"
        val finalIp = ip ?: BASE_URL_IP
        val finalPort = port ?: BASE_URL_PORT
        return "$protocol://$finalIp:$finalPort$BASE_URL_PATH"
    }
}
