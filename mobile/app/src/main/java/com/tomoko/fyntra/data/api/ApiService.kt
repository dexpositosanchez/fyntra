package com.tomoko.fyntra.data.api

import com.tomoko.fyntra.data.models.*
import okhttp3.MultipartBody
import okhttp3.RequestBody
import okhttp3.ResponseBody
import retrofit2.Response
import retrofit2.http.*

interface ApiService {
    // Auth
    @POST("auth/login")
    suspend fun login(@Body request: LoginRequest): Response<LoginResponse>

    // Rutas (para conductores)
    @GET("rutas/mis-rutas")
    suspend fun getMisRutas(): Response<List<Ruta>>

    @GET("rutas/{ruta_id}")
    suspend fun getRuta(@Path("ruta_id") rutaId: Int): Response<Ruta>

    @PUT("rutas/{ruta_id}/iniciar")
    suspend fun iniciarRuta(@Path("ruta_id") rutaId: Int): Response<Ruta>

    @PUT("rutas/{ruta_id}/finalizar")
    suspend fun finalizarRuta(@Path("ruta_id") rutaId: Int): Response<Ruta>

    @POST("rutas/{ruta_id}/confirmar-entrega")
    suspend fun confirmarEntrega(
        @Path("ruta_id") rutaId: Int,
        @Body confirmacion: EntregaConfirmacion
    ): Response<Unit>

    @POST("rutas/incidencia")
    suspend fun reportarIncidenciaRuta(@Body incidencia: IncidenciaRutaCreate): Response<Incidencia>

    // Incidencias
    @GET("incidencias/")
    suspend fun getIncidencias(
        @Query("estado") estado: String? = null
    ): Response<List<Incidencia>>

    @GET("incidencias/{incidencia_id}")
    suspend fun getIncidencia(@Path("incidencia_id") incidenciaId: Int): Response<Incidencia>

    @POST("incidencias/")
    suspend fun crearIncidencia(@Body incidencia: IncidenciaCreate): Response<Incidencia>

    @PUT("incidencias/{incidencia_id}")
    suspend fun actualizarIncidencia(
        @Path("incidencia_id") incidenciaId: Int,
        @Body incidencia: IncidenciaUpdate
    ): Response<Incidencia>

    @DELETE("incidencias/{incidencia_id}")
    suspend fun eliminarIncidencia(@Path("incidencia_id") incidenciaId: Int): Response<Unit>

    // Actuaciones (para proveedores)
    @GET("actuaciones/mis-incidencias")
    suspend fun getMisIncidenciasProveedor(
        @Query("estado") estado: String? = null
    ): Response<List<Incidencia>>

    @GET("actuaciones/incidencia/{incidencia_id}")
    suspend fun getActuacionesIncidencia(@Path("incidencia_id") incidenciaId: Int): Response<List<Actuacion>>

    @POST("actuaciones/")
    suspend fun crearActuacion(@Body actuacion: ActuacionCreate): Response<Actuacion>

    @PUT("actuaciones/incidencia/{incidencia_id}/estado")
    @Multipart
    suspend fun actualizarEstadoIncidencia(
        @Path("incidencia_id") incidenciaId: Int,
        @Part("estado") estado: RequestBody,
        @Part("comentario") comentario: RequestBody?
    ): Response<Incidencia>

    // Documentos
    @GET("documentos/incidencia/{incidencia_id}")
    suspend fun getDocumentosIncidencia(@Path("incidencia_id") incidenciaId: Int): Response<List<Documento>>

    @POST("documentos/")
    @Multipart
    suspend fun uploadDocumento(
        @Part("incidencia_id") incidenciaId: RequestBody,
        @Part("nombre") nombre: RequestBody,
        @Part archivo: MultipartBody.Part
    ): Response<Documento>

    @GET("documentos/{documento_id}/archivo")
    suspend fun downloadDocumento(
        @Path("documento_id") documentoId: Int,
        @Query("token") token: String
    ): Response<ResponseBody>

    @DELETE("documentos/{documento_id}")
    suspend fun eliminarDocumento(@Path("documento_id") documentoId: Int): Response<Unit>

    // Mensajes
    @GET("mensajes/incidencia/{incidencia_id}")
    suspend fun getMensajesIncidencia(@Path("incidencia_id") incidenciaId: Int): Response<List<Mensaje>>

    @POST("mensajes/incidencia/{incidencia_id}")
    suspend fun enviarMensaje(
        @Path("incidencia_id") incidenciaId: Int,
        @Body mensaje: MensajeCreate
    ): Response<Mensaje>
    
    @DELETE("mensajes/{mensaje_id}")
    suspend fun eliminarMensaje(@Path("mensaje_id") mensajeId: Int): Response<Unit>

    // Inmuebles
    @GET("inmuebles/mis-inmuebles")
    suspend fun getMisInmuebles(): Response<List<InmuebleSimple>>
    
    @GET("inmuebles/")
    suspend fun getInmuebles(
        @Query("comunidad_id") comunidadId: Int? = null,
        @Query("tipo") tipo: String? = null
    ): Response<List<InmuebleResponse>>
    
    // Proveedores
    @GET("proveedores/")
    suspend fun getProveedores(
        @Query("activo") activo: Boolean? = null,
        @Query("especialidad") especialidad: String? = null
    ): Response<List<ProveedorSimple>>
}

data class InmuebleResponse(
    val id: Int,
    val referencia: String,
    val direccion: String? = null,
    val comunidad_id: Int? = null,
    val metros: Float? = null,
    val tipo: String? = null
)

