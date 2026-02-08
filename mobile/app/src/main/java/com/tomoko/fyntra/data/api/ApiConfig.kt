package com.tomoko.fyntra.data.api

/**
 * Configuración de la API
 * 
 * Configurado para producción en Render (Fly.io)
 * 
 * OPCIONES:
 * - PRODUCCIÓN: https://fyntra-backend-6yvt.onrender.com (actual)
 * - Para EMULADOR Android local: usar "10.0.2.2"
 * - Para DISPOSITIVO FÍSICO en misma WiFi: usar la IP local (ej: "192.168.1.128")
 * - Para HOTSPOT del móvil: usar la IP que te asigne el hotspot
 */
object ApiConfig {
    // ============================================
    // ⚙️ CONFIGURACIÓN DE PRODUCCIÓN ⚙️
    // ============================================
    private const val BASE_URL_HOST = "fyntra-backend-6yvt.onrender.com"
    private const val BASE_URL_PORT = "443"
    private const val BASE_URL_PATH = "/api/"
    
    // Protocolo (http o https)
    // Producción usa HTTPS
    private const val BASE_URL_PROTOCOL = "https"
    
    // Construir la URL completa
    // Omitir puerto 443 en HTTPS (es el puerto por defecto)
    val BASE_URL: String
        get() {
            val portPart = if (BASE_URL_PROTOCOL == "https" && BASE_URL_PORT == "443") {
                ""
            } else {
                ":$BASE_URL_PORT"
            }
            return "$BASE_URL_PROTOCOL://$BASE_URL_HOST$portPart$BASE_URL_PATH"
        }
    
    /**
     * Método helper para cambiar la URL fácilmente
     * Úsalo si prefieres cambiar la URL programáticamente
     * 
     * @param host Host o IP del servidor (ej: "fyntra-backend-6yvt.onrender.com" o "192.168.1.128")
     * @param port Puerto del servidor (por defecto 443 para HTTPS, 8000 para HTTP local)
     * @param useHttps Si usar HTTPS (true) o HTTP (false)
     */
    fun getBaseUrl(host: String? = null, port: String? = null, useHttps: Boolean = true): String {
        val protocol = if (useHttps) "https" else "http"
        val finalHost = host ?: BASE_URL_HOST
        val finalPort = port ?: BASE_URL_PORT
        
        // Omitir puerto si es el puerto por defecto (443 para HTTPS, 80 para HTTP)
        val portPart = when {
            useHttps && (finalPort == "443" || finalPort.isEmpty()) -> ""
            !useHttps && (finalPort == "80" || finalPort.isEmpty()) -> ""
            else -> ":$finalPort"
        }
        
        return "$protocol://$finalHost$portPart$BASE_URL_PATH"
    }
}
