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
        }

