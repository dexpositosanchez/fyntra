import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../environments/environment';

const API_URL = environment.apiUrl || 'http://localhost:8000/api';

@Injectable({
  providedIn: 'root'
})
export class ApiService {
  private apiUrl = API_URL;

  constructor(private http: HttpClient) {}

  private getHeaders(): HttpHeaders {
    const token = localStorage.getItem('access_token');
    return new HttpHeaders({
      'Content-Type': 'application/json',
      ...(token && { 'Authorization': `Bearer ${token}` })
    });
  }

  // Auth
  login(email: string, password: string): Observable<any> {
    return this.http.post(`${this.apiUrl}/auth/login`, { email, password });
  }

  register(userData: any): Observable<any> {
    return this.http.post(`${this.apiUrl}/auth/register`, userData);
  }

  // Incidencias
  getIncidencias(params?: any): Observable<any> {
    return this.http.get(`${this.apiUrl}/incidencias`, {
      headers: this.getHeaders(),
      params
    });
  }

  getIncidenciasSinResolver(): Observable<any> {
    return this.http.get(`${this.apiUrl}/incidencias/sin-resolver`, {
      headers: this.getHeaders()
    });
  }

  getIncidencia(id: number): Observable<any> {
    return this.http.get(`${this.apiUrl}/incidencias/${id}`, {
      headers: this.getHeaders()
    });
  }

  createIncidencia(data: any): Observable<any> {
    return this.http.post(`${this.apiUrl}/incidencias`, data, {
      headers: this.getHeaders()
    });
  }

  updateIncidencia(id: number, data: any): Observable<any> {
    return this.http.put(`${this.apiUrl}/incidencias/${id}`, data, {
      headers: this.getHeaders()
    });
  }

  deleteIncidencia(id: number): Observable<any> {
    return this.http.delete(`${this.apiUrl}/incidencias/${id}`, {
      headers: this.getHeaders()
    });
  }

  // Vehículos
  getVehiculos(params?: any): Observable<any> {
    return this.http.get(`${this.apiUrl}/vehiculos/`, {
      headers: this.getHeaders(),
      params
    });
  }

  getVehiculo(id: number): Observable<any> {
    return this.http.get(`${this.apiUrl}/vehiculos/${id}`, {
      headers: this.getHeaders()
    });
  }

  createVehiculo(data: any): Observable<any> {
    return this.http.post(`${this.apiUrl}/vehiculos`, data, {
      headers: this.getHeaders()
    });
  }

  updateVehiculo(id: number, data: any): Observable<any> {
    return this.http.put(`${this.apiUrl}/vehiculos/${id}`, data, {
      headers: this.getHeaders()
    });
  }

  deleteVehiculo(id: number): Observable<any> {
    return this.http.delete(`${this.apiUrl}/vehiculos/${id}`, {
      headers: this.getHeaders()
    });
  }

  // Comunidades
  getComunidades(params?: any): Observable<any> {
    return this.http.get(`${this.apiUrl}/comunidades`, {
      headers: this.getHeaders(),
      params
    });
  }

  getComunidad(id: number): Observable<any> {
    return this.http.get(`${this.apiUrl}/comunidades/${id}`, {
      headers: this.getHeaders()
    });
  }

  createComunidad(data: any): Observable<any> {
    return this.http.post(`${this.apiUrl}/comunidades`, data, {
      headers: this.getHeaders()
    });
  }

  updateComunidad(id: number, data: any): Observable<any> {
    return this.http.put(`${this.apiUrl}/comunidades/${id}`, data, {
      headers: this.getHeaders()
    });
  }

  deleteComunidad(id: number): Observable<any> {
    return this.http.delete(`${this.apiUrl}/comunidades/${id}`, {
      headers: this.getHeaders()
    });
  }

  // Inmuebles
  getInmuebles(params?: any): Observable<any> {
    return this.http.get(`${this.apiUrl}/inmuebles`, {
      headers: this.getHeaders(),
      params
    });
  }

  getInmueble(id: number): Observable<any> {
    return this.http.get(`${this.apiUrl}/inmuebles/${id}`, {
      headers: this.getHeaders()
    });
  }

  createInmueble(data: any): Observable<any> {
    return this.http.post(`${this.apiUrl}/inmuebles`, data, {
      headers: this.getHeaders()
    });
  }

  updateInmueble(id: number, data: any): Observable<any> {
    return this.http.put(`${this.apiUrl}/inmuebles/${id}`, data, {
      headers: this.getHeaders()
    });
  }

  deleteInmueble(id: number): Observable<any> {
    return this.http.delete(`${this.apiUrl}/inmuebles/${id}`, {
      headers: this.getHeaders()
    });
  }

  // Propietarios
  getPropietarios(params?: any): Observable<any> {
    return this.http.get(`${this.apiUrl}/propietarios`, {
      headers: this.getHeaders(),
      params
    });
  }

  getPropietario(id: number): Observable<any> {
    return this.http.get(`${this.apiUrl}/propietarios/${id}`, {
      headers: this.getHeaders()
    });
  }

  createPropietario(data: any): Observable<any> {
    return this.http.post(`${this.apiUrl}/propietarios`, data, {
      headers: this.getHeaders()
    });
  }

  updatePropietario(id: number, data: any): Observable<any> {
    return this.http.put(`${this.apiUrl}/propietarios/${id}`, data, {
      headers: this.getHeaders()
    });
  }

  deletePropietario(id: number): Observable<any> {
    return this.http.delete(`${this.apiUrl}/propietarios/${id}`, {
      headers: this.getHeaders()
    });
  }

  // Proveedores
  getProveedores(params?: any): Observable<any> {
    return this.http.get(`${this.apiUrl}/proveedores`, {
      headers: this.getHeaders(),
      params
    });
  }

  getProveedor(id: number): Observable<any> {
    return this.http.get(`${this.apiUrl}/proveedores/${id}`, {
      headers: this.getHeaders()
    });
  }

  createProveedor(data: any): Observable<any> {
    return this.http.post(`${this.apiUrl}/proveedores`, data, {
      headers: this.getHeaders()
    });
  }

  updateProveedor(id: number, data: any): Observable<any> {
    return this.http.put(`${this.apiUrl}/proveedores/${id}`, data, {
      headers: this.getHeaders()
    });
  }

  deleteProveedor(id: number): Observable<any> {
    return this.http.delete(`${this.apiUrl}/proveedores/${id}`, {
      headers: this.getHeaders()
    });
  }

  // Conductores
  getConductores(params?: any): Observable<any> {
    return this.http.get(`${this.apiUrl}/conductores/`, {
      headers: this.getHeaders(),
      params
    });
  }

  getConductor(id: number): Observable<any> {
    return this.http.get(`${this.apiUrl}/conductores/${id}`, {
      headers: this.getHeaders()
    });
  }

  getAlertasLicencias(diasAlerta: number = 30): Observable<any> {
    return this.http.get(`${this.apiUrl}/conductores/alertas`, {
      headers: this.getHeaders(),
      params: { dias_alerta: diasAlerta }
    });
  }

  createConductor(data: any): Observable<any> {
    return this.http.post(`${this.apiUrl}/conductores`, data, {
      headers: this.getHeaders()
    });
  }

  updateConductor(id: number, data: any): Observable<any> {
    return this.http.put(`${this.apiUrl}/conductores/${id}`, data, {
      headers: this.getHeaders()
    });
  }

  deleteConductor(id: number): Observable<any> {
    return this.http.delete(`${this.apiUrl}/conductores/${id}`, {
      headers: this.getHeaders()
    });
  }

  // Pedidos
  getPedidos(params?: any): Observable<any> {
    return this.http.get(`${this.apiUrl}/pedidos/`, {
      headers: this.getHeaders(),
      params
    });
  }

  getPedido(id: number): Observable<any> {
    return this.http.get(`${this.apiUrl}/pedidos/${id}`, {
      headers: this.getHeaders()
    });
  }

  createPedido(data: any): Observable<any> {
    return this.http.post(`${this.apiUrl}/pedidos`, data, {
      headers: this.getHeaders()
    });
  }

  updatePedido(id: number, data: any): Observable<any> {
    return this.http.put(`${this.apiUrl}/pedidos/${id}`, data, {
      headers: this.getHeaders()
    });
  }

  deletePedido(id: number): Observable<any> {
    return this.http.delete(`${this.apiUrl}/pedidos/${id}`, {
      headers: this.getHeaders()
    });
  }

  // Rutas
  getRutas(params?: any): Observable<any> {
    return this.http.get(`${this.apiUrl}/rutas/`, {
      headers: this.getHeaders(),
      params
    });
  }

  getRuta(id: number): Observable<any> {
    return this.http.get(`${this.apiUrl}/rutas/${id}`, {
      headers: this.getHeaders()
    });
  }

  createRuta(data: any): Observable<any> {
    return this.http.post(`${this.apiUrl}/rutas`, data, {
      headers: this.getHeaders()
    });
  }

  updateRuta(id: number, data: any): Observable<any> {
    return this.http.put(`${this.apiUrl}/rutas/${id}`, data, {
      headers: this.getHeaders()
    });
  }

  finalizarRuta(id: number): Observable<any> {
    return this.http.put(`${this.apiUrl}/rutas/${id}/finalizar`, {}, {
      headers: this.getHeaders()
    });
  }

  getBaseUrl(): string {
    return this.apiUrl.replace('/api', '');
  }

          deleteRuta(id: number): Observable<any> {
            return this.http.delete(`${this.apiUrl}/rutas/${id}`, {
              headers: this.getHeaders()
            });
          }

          updateParadaRuta(rutaId: number, paradaId: number, data: any): Observable<any> {
            return this.http.put(`${this.apiUrl}/rutas/${rutaId}/paradas/${paradaId}`, data, {
              headers: this.getHeaders()
            });
          }

          // Mantenimientos
          getMantenimientos(params?: any): Observable<any> {
            return this.http.get(`${this.apiUrl}/mantenimientos/`, {
              headers: this.getHeaders(),
              params
            });
          }

          getMantenimiento(id: number): Observable<any> {
            return this.http.get(`${this.apiUrl}/mantenimientos/${id}`, {
              headers: this.getHeaders()
            });
          }

          getAlertasMantenimientos(diasAlerta: number = 30): Observable<any> {
            return this.http.get(`${this.apiUrl}/mantenimientos/alertas`, {
              headers: this.getHeaders(),
              params: { dias_alerta: diasAlerta }
            });
          }

          createMantenimiento(data: any): Observable<any> {
            return this.http.post(`${this.apiUrl}/mantenimientos`, data, {
              headers: this.getHeaders()
            });
          }

          updateMantenimiento(id: number, data: any): Observable<any> {
            return this.http.put(`${this.apiUrl}/mantenimientos/${id}`, data, {
              headers: this.getHeaders()
            });
          }

          deleteMantenimiento(id: number): Observable<any> {
            return this.http.delete(`${this.apiUrl}/mantenimientos/${id}`, {
              headers: this.getHeaders()
            });
          }

          // Actuaciones (para proveedores)
          getMisIncidencias(params?: any): Observable<any> {
            return this.http.get(`${this.apiUrl}/actuaciones/mis-incidencias`, {
              headers: this.getHeaders(),
              params
            });
          }

          getActuacionesIncidencia(incidenciaId: number): Observable<any> {
            return this.http.get(`${this.apiUrl}/actuaciones/incidencia/${incidenciaId}`, {
              headers: this.getHeaders()
            });
          }

          createActuacion(data: any): Observable<any> {
            return this.http.post(`${this.apiUrl}/actuaciones`, data, {
              headers: this.getHeaders()
            });
          }

          updateActuacion(id: number, data: any): Observable<any> {
            return this.http.put(`${this.apiUrl}/actuaciones/${id}`, data, {
              headers: this.getHeaders()
            });
          }

          deleteActuacion(id: number): Observable<any> {
            return this.http.delete(`${this.apiUrl}/actuaciones/${id}`, {
              headers: this.getHeaders()
            });
          }

          cambiarEstadoIncidenciaProveedor(incidenciaId: number, estado: string, comentario?: string): Observable<any> {
            const params: any = { nuevo_estado: estado };
            if (comentario) params.comentario = comentario;
            return this.http.put(`${this.apiUrl}/actuaciones/incidencia/${incidenciaId}/estado`, null, {
              headers: this.getHeaders(),
              params
            });
          }

          // Documentos
          getDocumentosIncidencia(incidenciaId: number): Observable<any> {
            return this.http.get(`${this.apiUrl}/documentos/incidencia/${incidenciaId}`, {
              headers: this.getHeaders()
            });
          }

          subirDocumento(incidenciaId: number, nombre: string, archivo: File): Observable<any> {
            const formData = new FormData();
            formData.append('incidencia_id', incidenciaId.toString());
            formData.append('nombre', nombre);
            formData.append('archivo', archivo);
            
            const token = localStorage.getItem('access_token');
            const headers = new HttpHeaders({
              ...(token && { 'Authorization': `Bearer ${token}` })
            });
            
            return this.http.post(`${this.apiUrl}/documentos/`, formData, { headers });
          }

          getUrlDocumento(documentoId: number): string {
            return `${this.apiUrl}/documentos/${documentoId}/archivo`;
          }

          eliminarDocumento(documentoId: number): Observable<any> {
            return this.http.delete(`${this.apiUrl}/documentos/${documentoId}`, {
              headers: this.getHeaders()
            });
          }

          // Mensajes
          getMensajesIncidencia(incidenciaId: number): Observable<any> {
            return this.http.get(`${this.apiUrl}/mensajes/incidencia/${incidenciaId}`, {
              headers: this.getHeaders()
            });
          }

          enviarMensaje(incidenciaId: number, contenido: string): Observable<any> {
            return this.http.post(`${this.apiUrl}/mensajes/incidencia/${incidenciaId}`, 
              { contenido }, 
              { headers: this.getHeaders() }
            );
          }

          eliminarMensaje(mensajeId: number): Observable<any> {
            return this.http.delete(`${this.apiUrl}/mensajes/${mensajeId}`, {
              headers: this.getHeaders()
            });
          }

          // Usuarios (solo super_admin)
          getUsuarios(): Observable<any> {
            return this.http.get(`${this.apiUrl}/usuarios`, {
              headers: this.getHeaders()
            });
          }

          getUsuario(usuarioId: number): Observable<any> {
            return this.http.get(`${this.apiUrl}/usuarios/${usuarioId}`, {
              headers: this.getHeaders()
            });
          }

          crearUsuario(data: any): Observable<any> {
            return this.http.post(`${this.apiUrl}/usuarios`, data, {
              headers: this.getHeaders()
            });
          }

          actualizarUsuario(usuarioId: number, data: any): Observable<any> {
            return this.http.put(`${this.apiUrl}/usuarios/${usuarioId}`, data, {
              headers: this.getHeaders()
            });
          }

          eliminarUsuario(usuarioId: number): Observable<any> {
            return this.http.delete(`${this.apiUrl}/usuarios/${usuarioId}`, {
              headers: this.getHeaders()
            });
          }

          cambiarPasswordUsuario(usuarioId: number, password: string): Observable<any> {
            return this.http.put(`${this.apiUrl}/usuarios/${usuarioId}/password`, 
              { password }, 
              { headers: this.getHeaders() }
            );
          }

  // Informes
  getInformesComunidades(fechaInicio?: string, fechaFin?: string): Observable<any> {
    const params: any = {};
    if (fechaInicio) params.fecha_inicio = fechaInicio;
    if (fechaFin) params.fecha_fin = fechaFin;
    return this.http.get(`${this.apiUrl}/informes/comunidades`, {
      headers: this.getHeaders(),
      params
    });
  }

  getInformesProveedores(fechaInicio?: string, fechaFin?: string): Observable<any> {
    const params: any = {};
    if (fechaInicio) params.fecha_inicio = fechaInicio;
    if (fechaFin) params.fecha_fin = fechaFin;
    return this.http.get(`${this.apiUrl}/informes/proveedores`, {
      headers: this.getHeaders(),
      params
    });
  }

  exportarInformesComunidades(formato: string, fechaInicio?: string, fechaFin?: string): Observable<Blob> {
    const params: any = {};
    if (fechaInicio) params.fecha_inicio = fechaInicio;
    if (fechaFin) params.fecha_fin = fechaFin;
    return this.http.get(`${this.apiUrl}/informes/comunidades/exportar/${formato}`, {
      headers: this.getHeaders(),
      params,
      responseType: 'blob'
    });
  }

  exportarInformesProveedores(formato: string, fechaInicio?: string, fechaFin?: string): Observable<Blob> {
    const params: any = {};
    if (fechaInicio) params.fecha_inicio = fechaInicio;
    if (fechaFin) params.fecha_fin = fechaFin;
    return this.http.get(`${this.apiUrl}/informes/proveedores/exportar/${formato}`, {
      headers: this.getHeaders(),
      params,
      responseType: 'blob'
    });
  }

  // Historial de rutas (RF9)
  getHistorialPedidos(fechaDesde?: string, fechaHasta?: string, soloConRuta?: boolean): Observable<any[]> {
    const params: any = {};
    if (fechaDesde) params.fecha_desde = fechaDesde;
    if (fechaHasta) params.fecha_hasta = fechaHasta;
    if (soloConRuta !== undefined && soloConRuta !== null) params.solo_con_ruta = soloConRuta;
    return this.http.get<any[]>(`${this.apiUrl}/historial/pedidos`, {
      headers: this.getHeaders(),
      params
    });
  }

  exportarHistorialPedidos(formato: string, fechaDesde?: string, fechaHasta?: string, soloConRuta?: boolean): Observable<Blob> {
    const params: any = {};
    if (fechaDesde) params.fecha_desde = fechaDesde;
    if (fechaHasta) params.fecha_hasta = fechaHasta;
    if (soloConRuta !== undefined && soloConRuta !== null) params.solo_con_ruta = soloConRuta;
    return this.http.get(`${this.apiUrl}/historial/pedidos/exportar/${formato}`, {
      headers: this.getHeaders(),
      params,
      responseType: 'blob'
    });
  }
}

