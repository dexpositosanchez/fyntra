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
  usuario: any = null;
  numeroAlertas: number = 0;
  private routerSubscription?: Subscription;
  
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
      fechaProximoMantenimientoFormateada = new Date(fecha.getTime() - fecha.getTimezoneOffset() * 60000).toISOString().slice(0, 16);
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
        const fechaProximoMantenimiento = new Date(this.mantenimientoForm.fecha_proximo_mantenimiento);
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
      this.apiService.createMantenimiento(mantenimientoData).subscribe({
        next: () => {
          this.cargarMantenimientos();
          this.mostrarFormulario = false;
          this.loading = false;
          this.error = '';
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

  getMantenimientoStatusClass(mantenimiento: any): string {
    if (mantenimiento.estado === 'vencido') {
      return 'vencido';
    }
    if (mantenimiento.estado === 'en_curso') {
      return 'en-curso';
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
    
    // Está próximo a vencer si está entre hoy y 30 días
    return diasRestantes >= 0 && diasRestantes <= 30;
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
}

