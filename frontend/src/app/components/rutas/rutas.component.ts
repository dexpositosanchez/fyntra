import { Component, OnInit, OnDestroy } from '@angular/core';
import { Router, NavigationEnd } from '@angular/router';
import { Subscription } from 'rxjs';
import { filter } from 'rxjs/operators';
import { ApiService } from '../../services/api.service';
import { AuthService } from '../../services/auth.service';
import { HttpErrorResponse } from '@angular/common/http';

@Component({
  selector: 'app-rutas',
  templateUrl: './rutas.component.html',
  styleUrls: ['./rutas.component.scss']
})
export class RutasComponent implements OnInit, OnDestroy {
  rutas: any[] = [];
  pedidos: any[] = [];
  conductores: any[] = [];
  vehiculos: any[] = [];
  mostrarFormulario: boolean = false;
  editandoRuta: boolean = false;
  rutaIdEditando: number | null = null;
  rutaForm: any = {
    fecha: '',
    conductor_id: null,
    vehiculo_id: null,
    observaciones: '',
    pedidos_ids: []
  };
  pedidosDisponibles: any[] = [];
  pedidosSeleccionados: any[] = [];
  pedidoSeleccionado: number | null = null;
  mostrarFechasPedido: boolean = false;
  fechaHoraCarga: string = '';
  fechaHoraDescarga: string = '';
  pedidosConFechas: Map<number, { fechaCarga: string, fechaDescarga: string }> = new Map();
  loading: boolean = false;
  error: string = '';
  currentRoute: string = '';
  mostrarMenuUsuario: boolean = false;
  usuario: any = null;
  private routerSubscription?: Subscription;
  
  estados = [
    { value: 'planificada', label: 'Planificada' },
    { value: 'en_curso', label: 'En Curso' },
    { value: 'completada', label: 'Completada' },
    { value: 'cancelada', label: 'Cancelada' }
  ];

  constructor(
    private apiService: ApiService,
    private authService: AuthService,
    private router: Router
  ) {}

  ngOnInit(): void {
    this.currentRoute = this.router.url;
    this.usuario = this.authService.getUsuario();
    this.actualizarVista();
    
    this.routerSubscription = this.router.events
      .pipe(filter(event => event instanceof NavigationEnd))
      .subscribe((event: any) => {
        this.currentRoute = event.url;
        this.actualizarVista();
      });
  }

  actualizarVista(): void {
    if (!this.currentRoute.includes('/rutas')) {
      this.mostrarFormulario = false;
    }
    
    if (this.currentRoute.includes('/rutas')) {
      this.cargarRutas();
      this.cargarPedidos();
      this.cargarConductores();
      this.cargarVehiculos();
    }
  }

  ngOnDestroy(): void {
    if (this.routerSubscription) {
      this.routerSubscription.unsubscribe();
    }
  }

  cargarRutas(): void {
    this.loading = true;
    this.apiService.getRutas().subscribe({
      next: (data) => {
        this.rutas = data;
        this.loading = false;
      },
      error: (err: HttpErrorResponse) => {
        this.error = err.error?.detail || 'Error al cargar rutas';
        this.loading = false;
        if (err.status === 401) {
          this.authService.logout();
        }
      }
    });
  }

  cargarPedidos(): void {
    this.apiService.getPedidos({ estado: 'pendiente' }).subscribe({
      next: (data) => {
        this.pedidosDisponibles = data;
      },
      error: (err: HttpErrorResponse) => {
        console.error('Error al cargar pedidos:', err);
      }
    });
  }

  cargarConductores(): void {
    this.apiService.getConductores({ activo: true }).subscribe({
      next: (data) => {
        // Filtrar conductores con licencia válida (no caducada)
        const hoy = new Date();
        hoy.setHours(0, 0, 0, 0);
        this.conductores = data.filter((conductor: any) => {
          if (!conductor.fecha_caducidad_licencia) return false;
          const fechaCaducidad = new Date(conductor.fecha_caducidad_licencia);
          fechaCaducidad.setHours(0, 0, 0, 0);
          return fechaCaducidad >= hoy;
        });
      },
      error: (err: HttpErrorResponse) => {
        console.error('Error al cargar conductores:', err);
      }
    });
  }

  cargarVehiculos(): void {
    this.apiService.getVehiculos({ estado: 'activo' }).subscribe({
      next: (data) => {
        this.vehiculos = data;
      },
      error: (err: HttpErrorResponse) => {
        console.error('Error al cargar vehículos:', err);
      }
    });
  }

  mostrarForm(): void {
    this.editandoRuta = false;
    this.rutaIdEditando = null;
    this.mostrarFormulario = true;
    this.rutaForm = {
      fecha: '',
      fecha_inicio: '',
      fecha_fin: '',
      conductor_id: null,
      vehiculo_id: null,
      observaciones: '',
      pedidos_ids: []
    };
    this.pedidosSeleccionados = [];
  }

  editarRuta(ruta: any): void {
    this.editandoRuta = true;
    this.rutaIdEditando = ruta.id;
    this.mostrarFormulario = true;
    
    // Formatear fecha_inicio y fecha_fin para date (YYYY-MM-DD)
    let fechaInicioFormateada = '';
    if (ruta.fecha_inicio) {
      const fechaInicio = new Date(ruta.fecha_inicio);
      fechaInicioFormateada = fechaInicio.toISOString().split('T')[0];
    }
    
    let fechaFinFormateada = '';
    if (ruta.fecha_fin) {
      const fechaFin = new Date(ruta.fecha_fin);
      fechaFinFormateada = fechaFin.toISOString().split('T')[0];
    }
    
    // Extraer IDs únicos de pedidos de las paradas
    const pedidosIds = ruta.paradas ? [...new Set(ruta.paradas.map((p: any) => p.pedido_id))] : [];
    this.pedidosSeleccionados = this.pedidosDisponibles.filter(p => pedidosIds.includes(p.id));
    
    // Recuperar fechas/horas de las paradas
    this.pedidosConFechas.clear();
    if (ruta.paradas) {
      const fechasPorPedido: Map<number, { fechaCarga: string, fechaDescarga: string }> = new Map();
      for (const parada of ruta.paradas) {
        if (!fechasPorPedido.has(parada.pedido_id)) {
          fechasPorPedido.set(parada.pedido_id, { fechaCarga: '', fechaDescarga: '' });
        }
        const fechas = fechasPorPedido.get(parada.pedido_id)!;
        if (parada.fecha_hora_llegada) {
          const fechaLocal = this.getFechaHoraLocal(parada.fecha_hora_llegada);
          if (parada.tipo_operacion === 'carga') {
            fechas.fechaCarga = fechaLocal;
          } else if (parada.tipo_operacion === 'descarga') {
            fechas.fechaDescarga = fechaLocal;
          }
        }
      }
      this.pedidosConFechas = fechasPorPedido;
    }
    
    this.rutaForm = {
      fecha_inicio: fechaInicioFormateada,
      fecha_fin: fechaFinFormateada,
      conductor_id: ruta.conductor_id || null,
      vehiculo_id: ruta.vehiculo_id || null,
      observaciones: ruta.observaciones || '',
      pedidos_ids: pedidosIds
    };
    this.mostrarFechasPedido = false;
    this.pedidoSeleccionado = null;
  }

  cancelarForm(): void {
    this.mostrarFormulario = false;
    this.editandoRuta = false;
    this.rutaIdEditando = null;
    this.mostrarFechasPedido = false;
    this.pedidoSeleccionado = null;
    this.error = '';
  }

  agregarPedido(pedidoId: number): void {
    if (!this.rutaForm.pedidos_ids.includes(pedidoId)) {
      this.rutaForm.pedidos_ids.push(pedidoId);
      // Buscar el pedido en pedidosDisponibles antes de que se filtre
      const pedido = this.pedidosDisponibles.find(p => p.id === pedidoId);
      if (pedido) {
        // Añadir una copia del pedido para evitar problemas de referencia
        this.pedidosSeleccionados.push({...pedido});
      } else {
        // Si no se encuentra, obtenerlo del servidor (no debería pasar normalmente)
        console.warn(`Pedido ${pedidoId} no encontrado, obteniendo del servidor...`);
        this.apiService.getPedido(pedidoId).subscribe({
          next: (data) => {
            this.pedidosSeleccionados.push(data);
          },
          error: (err) => {
            console.error('Error al obtener pedido:', err);
          }
        });
      }
    }
  }

  eliminarPedido(pedidoId: number): void {
    this.rutaForm.pedidos_ids = this.rutaForm.pedidos_ids.filter((id: number) => id !== pedidoId);
    this.pedidosSeleccionados = this.pedidosSeleccionados.filter(p => p.id !== pedidoId);
    this.pedidosConFechas.delete(pedidoId);
  }

  calcularPesoTotal(): number {
    return this.pedidosSeleccionados.reduce((total, pedido) => total + (pedido.peso || 0), 0);
  }

  getPedidosDisponibles(): any[] {
    return this.pedidosDisponibles.filter(p => !this.rutaForm.pedidos_ids.includes(p.id));
  }

  onAnadirPedido(): void {
    if (this.pedidoSeleccionado && !this.rutaForm.pedidos_ids.includes(this.pedidoSeleccionado)) {
      // Mostrar los campos de fecha/hora
      this.mostrarFechasPedido = true;
      this.fechaHoraCarga = '';
      this.fechaHoraDescarga = '';
    }
  }

  confirmarAnadirPedido(): void {
    if (this.pedidoSeleccionado && !this.rutaForm.pedidos_ids.includes(this.pedidoSeleccionado)) {
      // Guardar las fechas si están definidas
      if (this.fechaHoraCarga || this.fechaHoraDescarga) {
        this.pedidosConFechas.set(this.pedidoSeleccionado, {
          fechaCarga: this.fechaHoraCarga,
          fechaDescarga: this.fechaHoraDescarga
        });
      }
      this.agregarPedido(this.pedidoSeleccionado);
      // Limpiar el desplegable y ocultar los campos de fecha
      this.pedidoSeleccionado = null;
      this.mostrarFechasPedido = false;
      this.fechaHoraCarga = '';
      this.fechaHoraDescarga = '';
    }
  }

  cancelarAnadirPedido(): void {
    this.mostrarFechasPedido = false;
    this.pedidoSeleccionado = null;
    this.fechaHoraCarga = '';
    this.fechaHoraDescarga = '';
  }

  getVehiculoSeleccionado(): any {
    if (!this.rutaForm.vehiculo_id) return null;
    return this.vehiculos.find(v => v.id === this.rutaForm.vehiculo_id);
  }

  getCapacidadVehiculo(): number {
    const vehiculo = this.getVehiculoSeleccionado();
    return vehiculo ? (vehiculo.capacidad || 0) : 0;
  }

  hayExcesoCapacidad(): boolean {
    return this.calcularPesoTotal() > this.getCapacidadVehiculo();
  }

  contarParadasCarga(paradas: any[]): number {
    if (!paradas) return 0;
    return paradas.filter((p: any) => p.tipo_operacion === 'carga').length;
  }

  contarParadasDescarga(paradas: any[]): number {
    if (!paradas) return 0;
    return paradas.filter((p: any) => p.tipo_operacion === 'descarga').length;
  }

  obtenerNombrePedido(pedidoId: number): string {
    const pedido = this.pedidosDisponibles.find(p => p.id === pedidoId);
    return pedido ? `${pedido.cliente} - ${pedido.destino}` : 'Pedido no encontrado';
  }

  formatearFechaHora(fechaHora: string): string {
    if (!fechaHora) return '';
    const fecha = new Date(fechaHora);
    const day = String(fecha.getDate()).padStart(2, '0');
    const month = String(fecha.getMonth() + 1).padStart(2, '0');
    const year = fecha.getFullYear();
    const hours = String(fecha.getHours()).padStart(2, '0');
    const minutes = String(fecha.getMinutes()).padStart(2, '0');
    return `${day}/${month}/${year} ${hours}:${minutes}`;
  }

  getFechaHoraLocal(fechaHora: string | null | undefined): string {
    if (!fechaHora) return '';
    const fecha = new Date(fechaHora);
    // Ajustar por zona horaria local
    const localDate = new Date(fecha.getTime() - fecha.getTimezoneOffset() * 60000);
    return localDate.toISOString().slice(0, 16);
  }

  actualizarFechaHoraParada(rutaId: number, paradaId: number, fechaHora: string): void {
    if (!fechaHora) return;
    const fechaHoraISO = new Date(fechaHora).toISOString();
    this.apiService.updateParadaRuta(rutaId, paradaId, { fecha_hora_llegada: fechaHoraISO }).subscribe({
      next: () => {
        this.cargarRutas();
      },
      error: (err: HttpErrorResponse) => {
        this.error = err.error?.detail || 'Error al actualizar fecha de llegada';
        console.error('Error al actualizar parada:', err);
      }
    });
  }

  onSubmit(): void {
    if (!this.rutaForm.fecha_inicio || !this.rutaForm.fecha_fin || !this.rutaForm.conductor_id || !this.rutaForm.vehiculo_id) {
      this.error = 'La fecha de inicio, fecha de fin, conductor y vehículo son obligatorios';
      return;
    }

    // Validar que haya al menos un pedido seleccionado
    if (this.rutaForm.pedidos_ids.length === 0) {
      this.error = 'Debe seleccionar al menos un pedido';
      return;
    }

    this.loading = true;
    this.error = '';
    
    // Convertir fechas a formato datetime (añadir hora 00:00:00 para inicio y 23:59:59 para fin)
    // Usar hora local para evitar problemas de zona horaria
    const fechaInicioStr = this.rutaForm.fecha_inicio + 'T00:00:00';
    const fechaFinStr = this.rutaForm.fecha_fin + 'T23:59:59';
    const fechaInicio = new Date(fechaInicioStr);
    const fechaFin = new Date(fechaFinStr);
    
    // Verificar que las fechas sean válidas
    if (isNaN(fechaInicio.getTime()) || isNaN(fechaFin.getTime())) {
      this.error = 'Las fechas proporcionadas no son válidas';
      this.loading = false;
      return;
    }
    
    const rutaData: any = {
      fecha_inicio: fechaInicio.toISOString(),
      fecha_fin: fechaFin.toISOString(),
      conductor_id: this.rutaForm.conductor_id,
      vehiculo_id: this.rutaForm.vehiculo_id,
      observaciones: this.rutaForm.observaciones || '',
      pedidos_ids: this.rutaForm.pedidos_ids
    };
    
    // Añadir fechas/horas aproximadas para cada pedido
    if (this.pedidosConFechas.size > 0) {
      rutaData.pedidos_con_fechas = [];
      this.pedidosConFechas.forEach((fechas, pedidoId) => {
        if (this.rutaForm.pedidos_ids.includes(pedidoId)) {
          rutaData.pedidos_con_fechas.push({
            pedido_id: pedidoId,
            fecha_hora_carga: fechas.fechaCarga ? new Date(fechas.fechaCarga).toISOString() : null,
            fecha_hora_descarga: fechas.fechaDescarga ? new Date(fechas.fechaDescarga).toISOString() : null
          });
        }
      });
    }
    
    if (this.editandoRuta && this.rutaIdEditando) {
      this.apiService.updateRuta(this.rutaIdEditando, rutaData).subscribe({
        next: () => {
          this.cargarRutas();
          this.mostrarFormulario = false;
          this.editandoRuta = false;
          this.rutaIdEditando = null;
          this.loading = false;
          this.error = '';
        },
        error: (err: HttpErrorResponse) => {
          if (err.error?.detail) {
            if (typeof err.error.detail === 'object' && err.error.detail.error) {
              // Error de capacidad con detalles
              const detalle = err.error.detail;
              this.error = `${detalle.error}: Peso total ${detalle.peso_total} kg excede capacidad de ${detalle.capacidad_vehiculo} kg (exceso: ${detalle.exceso} kg). Pedidos problemáticos: ${detalle.pedidos_problema?.join(', ') || 'N/A'}`;
            } else {
              this.error = err.error.detail;
            }
          } else {
            this.error = err.error?.message || err.message || 'Error al actualizar ruta';
          }
          this.loading = false;
          if (err.status === 401) {
            this.authService.logout();
          }
        }
      });
    } else {
      this.apiService.createRuta(rutaData).subscribe({
        next: () => {
          this.cargarRutas();
          this.cargarPedidos(); // Recargar pedidos para actualizar disponibilidad
          this.mostrarFormulario = false;
          this.loading = false;
          this.error = '';
        },
        error: (err: HttpErrorResponse) => {
          console.error('Error al crear ruta:', err);
          if (err.error?.detail) {
            if (typeof err.error.detail === 'object' && err.error.detail.error) {
              // Error de capacidad con detalles
              const detalle = err.error.detail;
              this.error = `${detalle.error}: Peso total ${detalle.peso_total} kg excede capacidad de ${detalle.capacidad_vehiculo} kg (exceso: ${detalle.exceso} kg). Pedidos problemáticos: ${detalle.pedidos_problema?.join(', ') || 'N/A'}`;
            } else {
              this.error = typeof err.error.detail === 'string' ? err.error.detail : JSON.stringify(err.error.detail);
            }
          } else {
            this.error = err.error?.message || 'Error al crear ruta. Verifique los datos e intente nuevamente.';
          }
          this.loading = false;
          if (err.status === 401) {
            this.authService.logout();
          }
        }
      });
    }
  }

  getEstadoClass(estado: string): string {
    const clases: { [key: string]: string } = {
      'planificada': 'planificada',
      'en_curso': 'en-curso',
      'completada': 'completada',
      'cancelada': 'cancelada'
    };
    return clases[estado?.toLowerCase()] || 'planificada';
  }

  getEstadoTexto(estado: string): string {
    const textos: { [key: string]: string } = {
      'planificada': 'Planificada',
      'en_curso': 'En Curso',
      'completada': 'Completada',
      'cancelada': 'Cancelada'
    };
    return textos[estado?.toLowerCase()] || estado || 'Planificada';
  }

  formatearFecha(fecha: any): string {
    if (!fecha) return 'N/A';
    const date = fecha instanceof Date ? fecha : new Date(fecha);
    if (isNaN(date.getTime())) return 'N/A';
    const day = date.getDate().toString().padStart(2, '0');
    const month = (date.getMonth() + 1).toString().padStart(2, '0');
    const year = date.getFullYear();
    return `${day}/${month}/${year}`;
  }

  toggleMenuUsuario(): void {
    this.mostrarMenuUsuario = !this.mostrarMenuUsuario;
  }

  estaEnModuloTransportes(): boolean {
    return this.currentRoute.includes('/vehiculos') || 
           this.currentRoute.includes('/conductores') || 
           this.currentRoute.includes('/rutas') || 
           this.currentRoute.includes('/pedidos');
  }

  cambiarAModuloFincas(): void {
    this.mostrarMenuUsuario = false;
    this.router.navigate(['/incidencias']);
  }

  cambiarAModuloTransportes(): void {
    this.mostrarMenuUsuario = false;
    this.router.navigate(['/vehiculos']);
  }

  logout(): void {
    this.mostrarMenuUsuario = false;
    this.authService.logout();
  }
}

