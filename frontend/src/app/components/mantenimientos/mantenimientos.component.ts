import { Component, OnInit, OnDestroy } from '@angular/core';
import { Router, NavigationEnd } from '@angular/router';
import { Subscription } from 'rxjs';
import { filter } from 'rxjs/operators';
import { ApiService } from '../../services/api.service';
import { AuthService } from '../../services/auth.service';
import { HttpErrorResponse } from '@angular/common/http';

@Component({
  selector: 'app-mantenimientos',
  templateUrl: './mantenimientos.component.html',
  styleUrls: ['./mantenimientos.component.scss']
})
export class MantenimientosComponent implements OnInit, OnDestroy {
  mantenimientos: any[] = [];
  vehiculos: any[] = [];
  mostrarFormulario: boolean = false;
  editandoMantenimiento: boolean = false;
  mantenimientoIdEditando: number | null = null;
  mantenimientoForm: any = {
    vehiculo_id: null,
    tipo: '',
    descripcion: '',
    fecha_programada: '',
    fecha_proximo_mantenimiento: '',
    fecha_inicio: '',
    fecha_fin: '',
    estado: 'programado',
    observaciones: '',
    coste: null,
    kilometraje: null,
    proveedor: ''
  };
  loading: boolean = false;
  error: string = '';
  currentRoute: string = '';
  mostrarSoloAlertas: boolean = false;
  mostrarMenuUsuario: boolean = false;
  mostrarMenuNav: boolean = false;
  usuario: any = null;
  exportandoDatos: boolean = false;
  eliminandoCuenta: boolean = false;
  numeroAlertas: number = 0;
  // Filtros
  filtroVehiculo: number | string | null = null;
  filtroTipo: string = '';
  filtroFechaProgramada: string = '';
  filtroProveedor: string = '';
  mantenimientosFiltrados: any[] = [];
  // Pestañas por estado
  mantenimientosPorEstado: { [key: string]: any[] } = {};
  tabs: { estado: string, label: string, count: number }[] = [];
  tabActiva: string = '';
  private routerSubscription?: Subscription;
  // Modal para estado del vehículo
  mostrarModalEstadoVehiculo: boolean = false;
  estadoVehiculoSeleccionado: string = '';
  mantenimientoPendienteActualizacion: any = null;
  estadosVehiculo = [
    { value: 'activo', label: 'Activo' },
    { value: 'en_mantenimiento', label: 'En Mantenimiento' },
    { value: 'inactivo', label: 'Inactivo' }
  ];
  
  tipos = [
    { value: 'preventivo', label: 'Preventivo' },
    { value: 'correctivo', label: 'Correctivo' },
    { value: 'revision', label: 'Revisión' },
    { value: 'itv', label: 'ITV' },
    { value: 'cambio_aceite', label: 'Cambio de Aceite' }
  ];
  
  estados = [
    { value: 'programado', label: 'Programado' },
    { value: 'en_curso', label: 'En Curso' },
    { value: 'completado', label: 'Completado' },
    { value: 'vencido', label: 'Vencido' },
    { value: 'cancelado', label: 'Cancelado' }
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
    if (!this.currentRoute.includes('/mantenimientos')) {
      this.mostrarFormulario = false;
      this.mostrarSoloAlertas = false;
    }

    if (this.currentRoute.includes('/mantenimientos')) {
      this.cargarMantenimientos();
      this.cargarVehiculos();
      if (!this.mostrarSoloAlertas) {
        this.cargarNumeroAlertas();
      }
    }
  }

  ngOnDestroy(): void {
    if (this.routerSubscription) {
      this.routerSubscription.unsubscribe();
    }
  }

  cargarVehiculos(): void {
    this.apiService.getVehiculos().subscribe({
      next: (data) => {
        this.vehiculos = data;
      },
      error: (err: HttpErrorResponse) => {
        console.error('Error al cargar vehículos:', err);
      }
    });
  }

  cargarMantenimientos(): void {
    this.loading = true;
    this.error = '';
    const params: any = {};
    
    if (this.mostrarSoloAlertas) {
      // Cargar solo mantenimientos con alertas (próximos a vencer o vencidos)
      console.log('🔍 Modo ALERTAS activado - Cargando solo mantenimientos con alertas...');
      this.apiService.getAlertasMantenimientos(30).subscribe({
        next: (data) => {
          console.log('✅ Alertas recibidas al filtrar:', data);
          console.log('Tipo:', typeof data, 'Es array?', Array.isArray(data));
          this.mantenimientos = Array.isArray(data) ? data : [];
          this.numeroAlertas = this.mantenimientos.length;
          console.log('📊 Total mantenimientos con alertas encontrados:', this.mantenimientos.length);
          if (this.mantenimientos.length > 0) {
            console.log('📋 Mantenimientos:', this.mantenimientos.map(m => ({
              id: m.id,
              tipo: m.tipo,
              fecha_caducidad: m.fecha_proximo_mantenimiento,
              estado: m.estado
            })));
          }
          this.aplicarFiltros();
          this.loading = false;
          this.error = '';
        },
        error: (err: HttpErrorResponse) => {
          console.error('❌ Error al cargar alertas:', err);
          console.error('Status:', err.status);
          console.error('Error completo:', err);
          this.error = err.error?.detail || err.error?.message || 'Error al cargar alertas';
          this.loading = false;
          if (err.status === 401) {
            this.authService.logout();
          }
        }
      });
    } else {
      this.apiService.getMantenimientos(params).subscribe({
        next: (data) => {
          console.log('Mantenimientos cargados:', data);
          this.mantenimientos = Array.isArray(data) ? data : [];
          
          // DEBUG: Mostrar información de los mantenimientos cargados
          if (this.mantenimientos.length > 0) {
            console.log('📋 Información de mantenimientos cargados:');
            this.mantenimientos.forEach((m: any) => {
              const fechaCaducidad = m.fecha_proximo_mantenimiento || m.fecha_programada;
              const diasRestantes = this.calcularDiasRestantes(m);
              const esProximo = this.esProximoAVencer(m);
              console.log(`  - ID: ${m.id}, Estado: ${m.estado}, Fecha caducidad: ${fechaCaducidad}, Días restantes: ${diasRestantes}, ¿Próximo? ${esProximo}`);
            });
          }
          
          this.aplicarFiltros();
          this.loading = false;
          this.error = '';
          // Cargar número de alertas en segundo plano
          this.cargarNumeroAlertas();
        },
        error: (err: any) => {
          console.error('Error completo al cargar mantenimientos:', err);
          console.error('Tipo de error:', typeof err);
          console.error('Error keys:', err ? Object.keys(err) : 'null');
          
          let errorMessage = 'Error al cargar mantenimientos';
          
          // Manejar diferentes tipos de errores
          if (err instanceof HttpErrorResponse) {
            console.error('Es HttpErrorResponse');
            console.error('Error status:', err.status);
            console.error('Error body:', err.error);
            
            if (err.status === 401) {
              this.authService.logout();
              return;
            }
            
            if (err.error) {
              if (typeof err.error === 'string') {
                errorMessage = err.error;
              } else if (err.error.detail) {
                errorMessage = err.error.detail;
              } else if (err.error.message) {
                errorMessage = err.error.message;
              } else if (err.status === 0) {
                errorMessage = 'Error de conexión. Verifique que el servidor esté ejecutándose.';
              } else {
                errorMessage = `Error ${err.status}: ${err.statusText || 'Error desconocido'}`;
              }
            } else {
              errorMessage = `Error ${err.status || 'desconocido'}: ${err.statusText || 'Error al cargar mantenimientos'}`;
            }
          } else if (err && typeof err === 'object') {
            // Error genérico
            if (err.message) {
              errorMessage = err.message;
            } else if (err.status === 0 || err.statusText === 'Unknown Error') {
              errorMessage = 'Error de conexión. Verifique que el servidor esté ejecutándose y accesible.';
            } else {
              errorMessage = 'Error desconocido al cargar mantenimientos. Revise la consola para más detalles.';
            }
          } else {
            errorMessage = 'Error desconocido al cargar mantenimientos';
          }
          
          this.error = errorMessage;
          this.loading = false;
        }
      });
    }
  }

  cargarNumeroAlertas(): void {
    console.log('Cargando número de alertas...');
    this.apiService.getAlertasMantenimientos(30).subscribe({
      next: (data) => {
        console.log('✅ Alertas recibidas del servidor:', data);
        console.log('Tipo de datos:', typeof data, 'Es array?', Array.isArray(data));
        this.numeroAlertas = Array.isArray(data) ? data.length : 0;
        console.log('📊 Número de alertas calculado:', this.numeroAlertas);
        if (this.numeroAlertas > 0) {
          console.log('🔔 Hay', this.numeroAlertas, 'mantenimientos con alertas');
        } else {
          console.log('ℹ️ No hay mantenimientos con alertas');
        }
      },
      error: (err: HttpErrorResponse) => {
        console.error('❌ Error al cargar número de alertas:', err);
        console.error('Status:', err.status);
        console.error('Error body:', err.error);
        // Silenciar errores al cargar alertas pero mantener el contador en 0
        this.numeroAlertas = 0;
      }
    });
  }

  toggleAlertas(): void {
    this.mostrarSoloAlertas = !this.mostrarSoloAlertas;
    this.cargarMantenimientos();
    // Actualizar el número de alertas después de cambiar el filtro
    if (!this.mostrarSoloAlertas) {
      this.cargarNumeroAlertas();
    }
  }

  mostrarForm(): void {
    this.editandoMantenimiento = false;
    this.mantenimientoIdEditando = null;
    this.mostrarFormulario = true;
    this.mantenimientoForm = {
      vehiculo_id: null,
      tipo: '',
      descripcion: '',
      fecha_programada: '',
      fecha_proximo_mantenimiento: '',
      fecha_inicio: '',
      fecha_fin: '',
      estado: 'programado',
      observaciones: '',
      coste: null,
      kilometraje: null,
      proveedor: ''
    };
  }

  editarMantenimiento(mantenimiento: any): void {
    this.editandoMantenimiento = true;
    this.mantenimientoIdEditando = mantenimiento.id;
    this.mostrarFormulario = true;
    
    // Formatear fechas para datetime-local
    let fechaProgramadaFormateada = '';
    if (mantenimiento.fecha_programada) {
      const fecha = new Date(mantenimiento.fecha_programada);
      fechaProgramadaFormateada = new Date(fecha.getTime() - fecha.getTimezoneOffset() * 60000).toISOString().slice(0, 16);
    }
    
    let fechaInicioFormateada = '';
    if (mantenimiento.fecha_inicio) {
      const fecha = new Date(mantenimiento.fecha_inicio);
      fechaInicioFormateada = new Date(fecha.getTime() - fecha.getTimezoneOffset() * 60000).toISOString().slice(0, 16);
    }
    
    let fechaFinFormateada = '';
    if (mantenimiento.fecha_fin) {
      const fecha = new Date(mantenimiento.fecha_fin);
      fechaFinFormateada = new Date(fecha.getTime() - fecha.getTimezoneOffset() * 60000).toISOString().slice(0, 16);
    }
    
    let fechaProximoMantenimientoFormateada = '';
    if (mantenimiento.fecha_proximo_mantenimiento) {
      const fecha = new Date(mantenimiento.fecha_proximo_mantenimiento);
      // Para input type="date", solo necesitamos YYYY-MM-DD
      // Ajustar para la zona horaria local
      const year = fecha.getFullYear();
      const month = ('0' + (fecha.getMonth() + 1)).slice(-2);
      const day = ('0' + fecha.getDate()).slice(-2);
      fechaProximoMantenimientoFormateada = `${year}-${month}-${day}`;
    }
    
    this.mantenimientoForm = {
      vehiculo_id: mantenimiento.vehiculo_id || null,
      tipo: mantenimiento.tipo || '',
      descripcion: mantenimiento.descripcion || '',
      fecha_programada: fechaProgramadaFormateada,
      fecha_proximo_mantenimiento: fechaProximoMantenimientoFormateada,
      fecha_inicio: fechaInicioFormateada,
      fecha_fin: fechaFinFormateada,
      estado: mantenimiento.estado || 'programado',
      observaciones: mantenimiento.observaciones || '',
      coste: mantenimiento.coste,
      kilometraje: mantenimiento.kilometraje,
      proveedor: mantenimiento.proveedor || ''
    };
  }

  cancelarForm(): void {
    this.mostrarFormulario = false;
    this.editandoMantenimiento = false;
    this.mantenimientoIdEditando = null;
    this.error = '';
  }

  onSubmit(): void {
    // Limpiar error previo
    this.error = '';
    
    // Validar campos obligatorios - validación simple
    if (!this.mantenimientoForm.vehiculo_id) {
      this.error = 'El vehículo es obligatorio';
      return;
    }
    
    if (!this.mantenimientoForm.tipo) {
      this.error = 'El tipo de mantenimiento es obligatorio';
      return;
    }
    
    if (!this.mantenimientoForm.fecha_programada) {
      this.error = 'La fecha programada es obligatoria';
      return;
    }

    this.loading = true;
    
    // Validar y convertir fechas
    let fechaProgramada: Date;
    try {
      fechaProgramada = new Date(this.mantenimientoForm.fecha_programada);
      if (isNaN(fechaProgramada.getTime())) {
        this.error = 'La fecha programada no es válida';
        this.loading = false;
        return;
      }
    } catch (e) {
      this.error = 'Error al procesar la fecha programada';
      this.loading = false;
      return;
    }
    
    // Convertir fechas a formato ISO y preparar datos
    const mantenimientoData: any = {
      vehiculo_id: Number(this.mantenimientoForm.vehiculo_id),
      tipo: this.mantenimientoForm.tipo,
      fecha_programada: fechaProgramada.toISOString(),
      estado: this.mantenimientoForm.estado || 'programado'
    };
    
    // Campos opcionales - solo incluir si tienen valor
    if (this.mantenimientoForm.descripcion && this.mantenimientoForm.descripcion.trim()) {
      mantenimientoData.descripcion = this.mantenimientoForm.descripcion.trim();
    }
    
    if (this.mantenimientoForm.observaciones && this.mantenimientoForm.observaciones.trim()) {
      mantenimientoData.observaciones = this.mantenimientoForm.observaciones.trim();
    }
    
    if (this.mantenimientoForm.proveedor && this.mantenimientoForm.proveedor.trim()) {
      mantenimientoData.proveedor = this.mantenimientoForm.proveedor.trim();
    }
    
    // Convertir coste y kilometraje a números si tienen valor
    if (this.mantenimientoForm.coste !== null && this.mantenimientoForm.coste !== undefined && this.mantenimientoForm.coste !== '') {
      const coste = Number(this.mantenimientoForm.coste);
      if (!isNaN(coste) && coste >= 0) {
        mantenimientoData.coste = coste;
      }
    }
    
    if (this.mantenimientoForm.kilometraje !== null && this.mantenimientoForm.kilometraje !== undefined && this.mantenimientoForm.kilometraje !== '') {
      const kilometraje = Number(this.mantenimientoForm.kilometraje);
      if (!isNaN(kilometraje) && kilometraje >= 0) {
        mantenimientoData.kilometraje = kilometraje;
      }
    }
    
    // Fechas opcionales
    if (this.mantenimientoForm.fecha_proximo_mantenimiento) {
      try {
        // Para input type="date", el valor viene como YYYY-MM-DD
        // Convertirlo a Date y luego a ISO para mantener la hora a medianoche UTC
        const fechaProximoMantenimiento = new Date(this.mantenimientoForm.fecha_proximo_mantenimiento + 'T00:00:00');
        if (!isNaN(fechaProximoMantenimiento.getTime())) {
          mantenimientoData.fecha_proximo_mantenimiento = fechaProximoMantenimiento.toISOString();
        }
      } catch (e) {
        console.warn('Error al procesar fecha_proximo_mantenimiento:', e);
      }
    }
    
    if (this.mantenimientoForm.fecha_inicio) {
      try {
        const fechaInicio = new Date(this.mantenimientoForm.fecha_inicio);
        if (!isNaN(fechaInicio.getTime())) {
          mantenimientoData.fecha_inicio = fechaInicio.toISOString();
        }
      } catch (e) {
        console.warn('Error al procesar fecha_inicio:', e);
      }
    }
    
    if (this.mantenimientoForm.fecha_fin) {
      try {
        const fechaFin = new Date(this.mantenimientoForm.fecha_fin);
        if (!isNaN(fechaFin.getTime())) {
          mantenimientoData.fecha_fin = fechaFin.toISOString();
        }
      } catch (e) {
        console.warn('Error al procesar fecha_fin:', e);
      }
    }
    
    if (this.editandoMantenimiento && this.mantenimientoIdEditando) {
      // Verificar si el estado cambió y si necesitamos mostrar el modal
      const mantenimientoOriginal = this.mantenimientos.find(m => m.id === this.mantenimientoIdEditando);
      const estadoAnterior = mantenimientoOriginal?.estado;
      const estadoNuevo = mantenimientoData.estado || this.mantenimientoForm.estado;
      
      // Si el estado cambió de "en_curso" a otro estado, mostrar modal para seleccionar estado del vehículo
      if (estadoAnterior === 'en_curso' && estadoNuevo !== 'en_curso') {
        // Guardar los datos pendientes y mostrar el modal
        this.mantenimientoPendienteActualizacion = mantenimientoData;
        this.mostrarModalEstadoVehiculo = true;
        this.estadoVehiculoSeleccionado = 'activo'; // Por defecto
        this.loading = false;
        return;
      }
      
      // Si el estado cambió a "en_curso", actualizar el vehículo manualmente a "en_mantenimiento"
      if (estadoNuevo === 'en_curso') {
        // Primero actualizar el mantenimiento
        this.apiService.updateMantenimiento(this.mantenimientoIdEditando, mantenimientoData).subscribe({
          next: () => {
            // Luego actualizar el estado del vehículo a "en_mantenimiento"
            const vehiculoId = this.mantenimientoForm.vehiculo_id;
            this.apiService.updateVehiculo(vehiculoId, { estado: 'en_mantenimiento' }).subscribe({
              next: () => {
                this.cargarVehiculos();
                this.cargarMantenimientos();
                this.mostrarFormulario = false;
                this.editandoMantenimiento = false;
                this.mantenimientoIdEditando = null;
                this.loading = false;
                this.error = '';
              },
              error: (err: HttpErrorResponse) => {
                console.error('Error al actualizar estado del vehículo:', err);
                // Continuar aunque falle la actualización del vehículo
                this.cargarMantenimientos();
                this.mostrarFormulario = false;
                this.editandoMantenimiento = false;
                this.mantenimientoIdEditando = null;
                this.loading = false;
                this.error = '';
              }
            });
          },
          error: (err: HttpErrorResponse) => {
            console.error('Error al actualizar mantenimiento:', err);
            const errorMessage = err.error?.detail || err.message || 'Error al actualizar mantenimiento';
            this.error = typeof errorMessage === 'string' ? errorMessage : JSON.stringify(errorMessage);
            this.loading = false;
            if (err.status === 401) {
              this.authService.logout();
            }
          }
        });
        return;
      }
      
      // Si no hay cambio de estado o no es "en_curso", actualizar directamente
      this.apiService.updateMantenimiento(this.mantenimientoIdEditando, mantenimientoData).subscribe({
        next: () => {
          this.cargarMantenimientos();
          this.mostrarFormulario = false;
          this.editandoMantenimiento = false;
          this.mantenimientoIdEditando = null;
          this.loading = false;
          this.error = '';
        },
        error: (err: HttpErrorResponse) => {
          console.error('Error al actualizar mantenimiento:', err);
          const errorMessage = err.error?.detail || err.message || 'Error al actualizar mantenimiento';
          this.error = typeof errorMessage === 'string' ? errorMessage : JSON.stringify(errorMessage);
          this.loading = false;
          if (err.status === 401) {
            this.authService.logout();
          }
        }
      });
    } else {
      // Al crear un nuevo mantenimiento, siempre preguntar en qué estado dejar el vehículo
      // Guardar los datos pendientes y mostrar el modal
      this.mantenimientoPendienteActualizacion = mantenimientoData;
      this.mostrarModalEstadoVehiculo = true;
      this.estadoVehiculoSeleccionado = mantenimientoData.estado === 'en_curso' ? 'en_mantenimiento' : 'activo'; // Por defecto según el estado
      this.loading = false;
      console.log('Mostrando modal para crear mantenimiento. Estado seleccionado:', this.estadoVehiculoSeleccionado);
      return;
    }
  }

  eliminarMantenimiento(mantenimientoId: number, event: Event): void {
    event.stopPropagation();
    if (confirm('¿Está seguro de que desea eliminar este mantenimiento?')) {
      this.loading = true;
      this.apiService.deleteMantenimiento(mantenimientoId).subscribe({
        next: () => {
          this.cargarMantenimientos();
          this.loading = false;
        },
        error: (err: HttpErrorResponse) => {
          this.error = err.error?.detail || 'Error al eliminar mantenimiento';
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
      'programado': 'programado',
      'en_curso': 'en-curso',
      'completado': 'completado',
      'vencido': 'vencido',
      'cancelado': 'cancelado'
    };
    return clases[estado?.toLowerCase()] || 'programado';
  }

  getEstadoTexto(estado: string): string {
    const textos: { [key: string]: string } = {
      'programado': 'Programado',
      'en_curso': 'En Curso',
      'completado': 'Completado',
      'vencido': 'Vencido',
      'cancelado': 'Cancelado'
    };
    return textos[estado?.toLowerCase()] || estado || 'Programado';
  }

  getTipoTexto(tipo: string): string {
    const textos: { [key: string]: string } = {
      'preventivo': 'Preventivo',
      'correctivo': 'Correctivo',
      'revision': 'Revisión',
      'itv': 'ITV',
      'cambio_aceite': 'Cambio de Aceite'
    };
    return textos[tipo?.toLowerCase()] || tipo || 'Preventivo';
  }

  formatearFechaHora(fecha: string): string {
    if (!fecha) return '';
    const d = new Date(fecha);
    const day = ('0' + d.getDate()).slice(-2);
    const month = ('0' + (d.getMonth() + 1)).slice(-2);
    const year = d.getFullYear();
    const hours = ('0' + d.getHours()).slice(-2);
    const minutes = ('0' + d.getMinutes()).slice(-2);
    return `${day}/${month}/${year} ${hours}:${minutes}`;
  }

  formatearFecha(fecha: string): string {
    if (!fecha) return '';
    try {
      const d = new Date(fecha);
      if (isNaN(d.getTime())) {
        return '';
      }
      const day = ('0' + d.getDate()).slice(-2);
      const month = ('0' + (d.getMonth() + 1)).slice(-2);
      const year = d.getFullYear();
      return `${day}/${month}/${year}`;
    } catch (e) {
      console.warn('Error al formatear fecha:', e);
      return '';
    }
  }

  getMantenimientoStatusClass(mantenimiento: any): string {
    // El borde verde (#20b2aa) es el estilo por defecto
    // Se puede cambiar dinámicamente según el estado:
    // - Normal/Programado: verde (#20b2aa)
    // - En curso: naranja (#ff9800)
    // - Completado: verde oscuro (#1b9d8a)
    // - Vencido: rojo (#f44336)
    // - Próximo a vencer: naranja (#ff9800)
    
    if (mantenimiento.estado === 'vencido' || this.esVencido(mantenimiento)) {
      return 'vencido';
    }
    if (mantenimiento.estado === 'en_curso') {
      return 'en-curso';
    }
    if (mantenimiento.estado === 'completado') {
      return 'completado';
    }
    // Verificar si está próximo a vencer basándose en fecha de caducidad
    if (this.esProximoAVencer(mantenimiento)) {
      return 'proximo-vencer';
    }
    return 'normal';
  }

  esProximoAVencer(mantenimiento: any): boolean {
    // IMPORTANTE: Las alertas se basan SOLO en la fecha de caducidad (fecha_proximo_mantenimiento)
    // NO usar fecha_programada como fallback
    const fechaCaducidad = mantenimiento.fecha_proximo_mantenimiento;
    if (!fechaCaducidad) {
      return false;
    }
    
    const fecha = new Date(fechaCaducidad);
    const hoy = new Date();
    const diasRestantes = Math.ceil((fecha.getTime() - hoy.getTime()) / (1000 * 60 * 60 * 24));
    
    // Está próximo a vencer si está entre hoy y 30 días (pero no vencido)
    return diasRestantes >= 0 && diasRestantes <= 30;
  }

  esVencido(mantenimiento: any): boolean {
    // Verifica si la fecha de caducidad ya pasó
    const fechaCaducidad = mantenimiento.fecha_proximo_mantenimiento;
    if (!fechaCaducidad) {
      return false;
    }
    
    const fecha = new Date(fechaCaducidad);
    const hoy = new Date();
    const diasRestantes = Math.ceil((fecha.getTime() - hoy.getTime()) / (1000 * 60 * 60 * 24));
    
    // Está vencido si la fecha ya pasó (días negativos)
    return diasRestantes < 0;
  }

  calcularDiasRestantes(mantenimiento: any): number | null {
    // IMPORTANTE: Las alertas se basan SOLO en la fecha de caducidad (fecha_proximo_mantenimiento)
    const fechaCaducidad = mantenimiento.fecha_proximo_mantenimiento;
    if (!fechaCaducidad) {
      return null;
    }
    
    const fecha = new Date(fechaCaducidad);
    const hoy = new Date();
    const diasRestantes = Math.ceil((fecha.getTime() - hoy.getTime()) / (1000 * 60 * 60 * 24));
    
    return diasRestantes;
  }

  formatearDiasRestantes(mantenimiento: any): string {
    const dias = this.calcularDiasRestantes(mantenimiento);
    if (dias === null) {
      return '';
    }
    if (dias > 0) {
      return `${dias} días restantes`;
    } else {
      return `Vencido hace ${Math.abs(dias)} días`;
    }
  }

  irAUsuarios(): void {
    this.mostrarMenuUsuario = false;
    this.router.navigate(['/usuarios']);
  }

  logout(): void {
    this.authService.logout();
  }

  toggleMenuUsuario(): void {
    this.mostrarMenuUsuario = !this.mostrarMenuUsuario;
  }

  toggleMenuNav(): void {
    if (this.mostrarMenuNav) {
      this.cerrarMenuMobile();
    } else {
      this.mostrarMenuNav = true;
    }
  }

  cerrarMenuMobile(): void {
    this.mostrarMenuNav = false;
    this.mostrarMenuUsuario = false;
  }

  puedeCambiarModulo(): boolean {
    const r = this.usuario?.rol;
    return r === 'super_admin' || r === 'admin_fincas' || r === 'admin_transportes';
  }

  exportarMisDatos(): void {
    this.exportandoDatos = true;
    this.apiService.getMisDatos().subscribe({
      next: (datos) => {
        const blob = new Blob([JSON.stringify(datos, null, 2)], { type: 'application/json' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `mis-datos-${this.usuario?.email?.replace('@', '-at-') || 'usuario'}-${new Date().toISOString().slice(0, 10)}.json`;
        a.click();
        window.URL.revokeObjectURL(url);
        this.exportandoDatos = false;
      },
      error: () => { this.exportandoDatos = false; }
    });
  }

  eliminarMiCuenta(): void {
    if (!confirm('¿Está seguro de que desea eliminar su cuenta? Se anonimizarán sus datos y no podrá volver a iniciar sesión.')) return;
    const password = prompt('Opcional: introduzca su contraseña para confirmar (o deje en blanco):');
    this.eliminandoCuenta = true;
    this.apiService.eliminarMiCuenta(password || undefined).subscribe({
      next: () => {
        this.eliminandoCuenta = false;
        this.authService.logout();
        this.router.navigate(['/login']);
      },
      error: (err) => {
        alert(err.error?.detail || 'Error al eliminar la cuenta.');
        this.eliminandoCuenta = false;
      }
    });
  }

  cambiarAModuloFincas(): void {
    this.router.navigate(['/incidencias']);
    this.mostrarMenuUsuario = false;
  }

  cambiarAModuloTransportes(): void {
    this.router.navigate(['/vehiculos']);
    this.mostrarMenuUsuario = false;
  }

  estaEnModuloTransportes(): boolean {
    return this.currentRoute.includes('/vehiculos') || 
           this.currentRoute.includes('/conductores') || 
           this.currentRoute.includes('/rutas') || 
           this.currentRoute.includes('/pedidos') ||
           this.currentRoute.includes('/mantenimientos');
  }

  aplicarFiltros(): void {
    // Aplicar todos los filtros
    let resultados = [...this.mantenimientos];
    
    // Filtro por vehículo
    if (this.filtroVehiculo !== null && this.filtroVehiculo !== undefined && this.filtroVehiculo !== '') {
      const vehiculoId = typeof this.filtroVehiculo === 'string' ? parseInt(this.filtroVehiculo, 10) : this.filtroVehiculo;
      if (!isNaN(vehiculoId)) {
        resultados = resultados.filter(mantenimiento => {
          return mantenimiento.vehiculo_id === vehiculoId;
        });
      }
    }
    
    // Filtro por tipo
    if (this.filtroTipo && this.filtroTipo.trim() !== '') {
      resultados = resultados.filter(mantenimiento => {
        return mantenimiento.tipo === this.filtroTipo;
      });
    }
    
    // Filtro por fecha programada
    if (this.filtroFechaProgramada && this.filtroFechaProgramada.trim() !== '') {
      resultados = resultados.filter(mantenimiento => {
        if (!mantenimiento.fecha_programada) return false;
        const fechaMantenimiento = new Date(mantenimiento.fecha_programada);
        const fechaFiltro = new Date(this.filtroFechaProgramada);
        // Comparar solo la fecha (sin hora)
        return fechaMantenimiento.toDateString() === fechaFiltro.toDateString();
      });
    }
    
    // Filtro por proveedor/taller (búsqueda de texto)
    if (this.filtroProveedor && this.filtroProveedor.trim() !== '') {
      const busqueda = this.filtroProveedor.toLowerCase().trim();
      resultados = resultados.filter(mantenimiento => {
        const proveedor = (mantenimiento.proveedor || '').toLowerCase();
        return proveedor.includes(busqueda);
      });
    }
    
    this.mantenimientosFiltrados = resultados;
    this.agruparPorEstado();
  }

  limpiarTodosFiltros(): void {
    this.filtroVehiculo = null;
    this.filtroTipo = '';
    this.filtroFechaProgramada = '';
    this.filtroProveedor = '';
    this.aplicarFiltros();
  }

  agruparPorEstado(): void {
    // Inicializar objeto de agrupación
    this.mantenimientosPorEstado = {};
    
    // Agrupar mantenimientos filtrados por estado
    this.mantenimientosFiltrados.forEach(mantenimiento => {
      const estado = mantenimiento.estado || 'programado';
      if (!this.mantenimientosPorEstado[estado]) {
        this.mantenimientosPorEstado[estado] = [];
      }
      this.mantenimientosPorEstado[estado].push(mantenimiento);
    });

    // Crear array de tabs con contadores, excluyendo estados con 0 items
    this.tabs = this.estados
      .map(estado => ({
        estado: estado.value,
        label: estado.label,
        count: this.mantenimientosPorEstado[estado.value]?.length || 0
      }))
      .filter(tab => tab.count > 0)
      .sort((a, b) => {
        // Ordenar: primero "programado" o similar, al final "cancelado" o similar
        const ordenEstados: { [key: string]: number } = {
          'programado': 1,
          'en_curso': 2,
          'completado': 3,
          'vencido': 4,
          'cancelado': 99
        };
        const ordenA = ordenEstados[a.estado] || 50;
        const ordenB = ordenEstados[b.estado] || 50;
        return ordenA - ordenB;
      });

    // Establecer la primera tab como activa siempre que haya tabs
    if (this.tabs.length > 0) {
      // Verificar si la tab activa actual existe en las nuevas tabs
      const tabActivaExiste = this.tabs.some(tab => tab.estado === this.tabActiva);
      // Si no existe o no hay tab activa, establecer la primera
      if (!tabActivaExiste || !this.tabActiva) {
        this.tabActiva = this.tabs[0].estado;
      }
    } else {
      // Si no hay tabs, limpiar tabActiva
      this.tabActiva = '';
    }
  }

  cambiarTab(estado: string): void {
    this.tabActiva = estado;
  }

  getMantenimientosTabActiva(): any[] {
    return this.mantenimientosPorEstado[this.tabActiva] || [];
  }

  // Funciones para el modal de estado del vehículo
  seleccionarEstadoVehiculo(estado: string): void {
    this.estadoVehiculoSeleccionado = estado;
  }

  cerrarModalEstadoVehiculo(): void {
    this.mostrarModalEstadoVehiculo = false;
    this.estadoVehiculoSeleccionado = '';
    this.mantenimientoPendienteActualizacion = null;
  }

  confirmarCambioEstadoVehiculo(): void {
    if (!this.estadoVehiculoSeleccionado || !this.mantenimientoPendienteActualizacion) {
      return;
    }

    this.loading = true;
    
    // Si estamos editando, actualizar el mantenimiento primero
    if (this.editandoMantenimiento && this.mantenimientoIdEditando) {
      this.apiService.updateMantenimiento(this.mantenimientoIdEditando, this.mantenimientoPendienteActualizacion).subscribe({
        next: () => {
          // Luego actualizar el estado del vehículo
          const vehiculoId = this.mantenimientoForm.vehiculo_id;
          this.apiService.updateVehiculo(vehiculoId, { estado: this.estadoVehiculoSeleccionado }).subscribe({
            next: () => {
              this.cargarVehiculos();
              this.cargarMantenimientos();
              this.mostrarFormulario = false;
              this.editandoMantenimiento = false;
              this.mantenimientoIdEditando = null;
              this.loading = false;
              this.error = '';
              this.cerrarModalEstadoVehiculo();
            },
            error: (err: HttpErrorResponse) => {
              console.error('Error al actualizar estado del vehículo:', err);
              const errorMessage = err.error?.detail || err.message || 'Error al actualizar estado del vehículo';
              this.error = typeof errorMessage === 'string' ? errorMessage : JSON.stringify(errorMessage);
              this.loading = false;
              if (err.status === 401) {
                this.authService.logout();
              }
            }
          });
        },
        error: (err: HttpErrorResponse) => {
          console.error('Error al actualizar mantenimiento:', err);
          const errorMessage = err.error?.detail || err.message || 'Error al actualizar mantenimiento';
          this.error = typeof errorMessage === 'string' ? errorMessage : JSON.stringify(errorMessage);
          this.loading = false;
          if (err.status === 401) {
            this.authService.logout();
          }
        }
      });
    } else {
      // Si estamos creando, crear el mantenimiento primero
      this.apiService.createMantenimiento(this.mantenimientoPendienteActualizacion).subscribe({
        next: () => {
          // Luego actualizar el estado del vehículo
          const vehiculoId = this.mantenimientoForm.vehiculo_id;
          this.apiService.updateVehiculo(vehiculoId, { estado: this.estadoVehiculoSeleccionado }).subscribe({
            next: () => {
              this.cargarVehiculos();
              this.cargarMantenimientos();
              this.mostrarFormulario = false;
              this.loading = false;
              this.error = '';
              this.cerrarModalEstadoVehiculo();
            },
            error: (err: HttpErrorResponse) => {
              console.error('Error al actualizar estado del vehículo:', err);
              const errorMessage = err.error?.detail || err.message || 'Error al actualizar estado del vehículo';
              this.error = typeof errorMessage === 'string' ? errorMessage : JSON.stringify(errorMessage);
              this.loading = false;
              if (err.status === 401) {
                this.authService.logout();
              }
            }
          });
        },
        error: (err: HttpErrorResponse) => {
          console.error('Error al crear mantenimiento:', err);
          const errorMessage = err.error?.detail || err.message || 'Error al crear mantenimiento';
          this.error = typeof errorMessage === 'string' ? errorMessage : JSON.stringify(errorMessage);
          this.loading = false;
          if (err.status === 401) {
            this.authService.logout();
          }
        }
      });
    }
  }
}

