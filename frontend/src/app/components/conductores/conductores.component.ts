import { Component, OnInit, OnDestroy } from '@angular/core';
import { Router, NavigationEnd } from '@angular/router';
import { Subscription } from 'rxjs';
import { filter } from 'rxjs/operators';
import { ApiService } from '../../services/api.service';
import { AuthService } from '../../services/auth.service';

@Component({
  selector: 'app-conductores',
  templateUrl: './conductores.component.html',
  styleUrls: ['./conductores.component.scss']
})
export class ConductoresComponent implements OnInit, OnDestroy {
  conductores: any[] = [];
  conductoresPorEstado: { [key: string]: any[] } = {};
  tabs: { estado: string, label: string, count: number }[] = [];
  tabActiva: string = '';
  mostrarFormulario: boolean = false;
  historialConductor: any = null;
  historialCargando: boolean = false;
  editandoConductor: boolean = false;
  conductorIdEditando: number | null = null;
  conductorForm: any = {
    nombre: '',
    apellidos: '',
    dni: '',
    telefono: '',
    email: '',
    licencia: '',
    fecha_caducidad_licencia: '',
    activo: true,
    crearAccesoMovil: false,
    password: ''
  };
  loading: boolean = false;
  error: string = '';
  currentRoute: string = '';
  mostrarSoloAlertas: boolean = false;
  mostrarMenuUsuario: boolean = false;
  usuario: any = null;
  textoBusqueda: string = '';
  conductoresFiltrados: any[] = [];
  private routerSubscription?: Subscription;

  constructor(
    private apiService: ApiService,
    private authService: AuthService,
    private router: Router
  ) {}

  ngOnInit(): void {
    this.currentRoute = this.router.url;
    this.usuario = this.authService.getUsuario();
    this.actualizarVista();
    
    // Suscribirse a cambios de ruta
    this.routerSubscription = this.router.events
      .pipe(filter(event => event instanceof NavigationEnd))
      .subscribe((event: any) => {
        this.currentRoute = event.url;
        this.actualizarVista();
      });
  }

  actualizarVista(): void {
    if (!this.currentRoute.includes('/conductores')) {
      this.mostrarFormulario = false;
      return;
    }
    this.error = '';
    if (!this.loading) {
      this.cargarConductores();
    }
  }

  ngOnDestroy(): void {
    if (this.routerSubscription) {
      this.routerSubscription.unsubscribe();
    }
  }

  cargarConductores(): void {
    this.loading = true;
    this.error = '';
    const params: any = {};
    if (this.mostrarSoloAlertas) {
      params.licencias_proximas_caducar = true;
    }
    
    this.apiService.getConductores(params).subscribe({
      next: (data) => {
        this.conductores = data;
        this.aplicarFiltroBusqueda();
        this.loading = false;
      },
      error: (err) => {
        if (err.status === 401) {
          this.authService.logout();
        } else {
          this.error = err.error?.detail || 'Error al cargar conductores';
        }
        this.loading = false;
      }
    });
  }

  aplicarFiltroBusqueda(): void {
    // Aplicar filtro de búsqueda
    if (!this.textoBusqueda || this.textoBusqueda.trim() === '') {
      this.conductoresFiltrados = [...this.conductores];
    } else {
      const busqueda = this.textoBusqueda.toLowerCase().trim();
      this.conductoresFiltrados = this.conductores.filter(conductor => {
        const nombreCompleto = `${conductor.nombre || ''} ${conductor.apellidos || ''}`.toLowerCase();
        const dni = (conductor.dni || '').toLowerCase();
        const telefono = (conductor.telefono || '').toLowerCase();
        const email = (conductor.email || '').toLowerCase();
        const licencia = (conductor.licencia || '').toLowerCase();
        
        return nombreCompleto.includes(busqueda) ||
               dni.includes(busqueda) ||
               telefono.includes(busqueda) ||
               email.includes(busqueda) ||
               licencia.includes(busqueda);
      });
    }
    
    // Organizar los conductores filtrados por estado
    this.organizarConductoresPorEstado();
  }

  limpiarBusqueda(): void {
    this.textoBusqueda = '';
    this.aplicarFiltroBusqueda();
  }

  organizarConductoresPorEstado(): void {
    // Inicializar objetos
    this.conductoresPorEstado = {
      'activo': [],
      'inactivo': []
    };

    // Organizar por estado usando los conductores filtrados
    this.conductoresFiltrados.forEach(conductor => {
      const estado = conductor.activo ? 'activo' : 'inactivo';
      this.conductoresPorEstado[estado].push(conductor);
    });

    // Crear tabs
    this.tabs = [
      {
        estado: 'activo',
        label: 'Activos',
        count: this.conductoresPorEstado['activo'].length
      },
      {
        estado: 'inactivo',
        label: 'Inactivos',
        count: this.conductoresPorEstado['inactivo'].length
      }
    ].filter(tab => tab.count > 0);

    // Establecer la primera tab como activa
    if (this.tabs.length > 0) {
      const tabActivaExiste = this.tabs.some(tab => tab.estado === this.tabActiva);
      if (!tabActivaExiste || !this.tabActiva) {
        this.tabActiva = this.tabs[0].estado;
      }
    } else {
      this.tabActiva = '';
    }
  }

  cambiarTab(estado: string): void {
    this.tabActiva = estado;
  }

  getConductoresTabActiva(): any[] {
    return this.conductoresPorEstado[this.tabActiva] || [];
  }

  toggleAlertas(): void {
    this.mostrarSoloAlertas = !this.mostrarSoloAlertas;
    this.cargarConductores();
  }

  mostrarForm(): void {
    this.editandoConductor = false;
    this.conductorIdEditando = null;
    this.mostrarFormulario = true;
    this.conductorForm = {
      nombre: '',
      apellidos: '',
      dni: '',
      telefono: '',
      email: '',
      licencia: '',
      fecha_caducidad_licencia: '',
      activo: true,
      crearAccesoMovil: false,
      password: ''
    };
  }

  editarConductor(conductor: any): void {
    this.editandoConductor = true;
    this.conductorIdEditando = conductor.id;
    this.mostrarFormulario = true;
    this.historialConductor = null;
    this.historialCargando = true;
    
    // Formatear fecha para el input date (YYYY-MM-DD)
    let fechaFormateada = '';
    if (conductor.fecha_caducidad_licencia) {
      const fecha = new Date(conductor.fecha_caducidad_licencia);
      fechaFormateada = fecha.toISOString().split('T')[0];
    }
    
    // Asegurar que activo sea un boolean
    let activoValue = true;
    if (conductor.activo !== undefined && conductor.activo !== null) {
      activoValue = conductor.activo === true || conductor.activo === 'true' || conductor.activo === 1;
    }
    
    this.conductorForm = {
      nombre: conductor.nombre || '',
      apellidos: conductor.apellidos || '',
      dni: conductor.dni || '',
      telefono: conductor.telefono || '',
      email: conductor.email || '',
      licencia: conductor.licencia || '',
      fecha_caducidad_licencia: fechaFormateada,
      activo: activoValue
    };
    this.apiService.getHistorialConductor(conductor.id).subscribe({
      next: (data) => {
        this.historialConductor = data;
        this.historialCargando = false;
      },
      error: () => {
        this.historialCargando = false;
        this.historialConductor = null;
      }
    });
  }

  cancelarForm(): void {
    this.mostrarFormulario = false;
    this.editandoConductor = false;
    this.conductorIdEditando = null;
    this.historialConductor = null;
    this.conductorForm = {
      nombre: '',
      apellidos: '',
      dni: '',
      telefono: '',
      email: '',
      licencia: '',
      fecha_caducidad_licencia: '',
      activo: true,
      crearAccesoMovil: false,
      password: ''
    };
    this.error = '';
  }

  onSubmit(): void {
    if (!this.conductorForm.nombre || !this.conductorForm.licencia || !this.conductorForm.fecha_caducidad_licencia) {
      this.error = 'El nombre, licencia y fecha de caducidad son obligatorios';
      return;
    }

    if (!this.editandoConductor && this.conductorForm.crearAccesoMovil && !this.conductorForm.password) {
      this.error = 'La contraseña es obligatoria para crear acceso móvil';
      return;
    }

    if (this.conductorForm.password && this.conductorForm.password.length < 6) {
      this.error = 'La contraseña debe tener al menos 6 caracteres';
      return;
    }

    if (this.conductorForm.crearAccesoMovil && !this.conductorForm.email) {
      this.error = 'El email es obligatorio para crear acceso móvil';
      return;
    }

    this.loading = true;
    
    const data: any = {
      nombre: this.conductorForm.nombre,
      apellidos: this.conductorForm.apellidos || null,
      dni: this.conductorForm.dni || null,
      telefono: this.conductorForm.telefono || null,
      email: this.conductorForm.email || null,
      licencia: this.conductorForm.licencia,
      fecha_caducidad_licencia: this.conductorForm.fecha_caducidad_licencia,
      activo: this.conductorForm.activo
    };

    if (!this.editandoConductor && this.conductorForm.crearAccesoMovil) {
      data.password = this.conductorForm.password;
    }

    if (this.editandoConductor && this.conductorIdEditando) {
      // Si se está editando y se proporciona password, añadirlo
      if (this.conductorForm.password) {
        data.password = this.conductorForm.password;
      }
      // Actualizar conductor existente
      this.apiService.updateConductor(this.conductorIdEditando, data).subscribe({
        next: () => {
          this.cargarConductores();
          this.mostrarFormulario = false;
          this.editandoConductor = false;
          this.conductorIdEditando = null;
          this.loading = false;
          this.error = '';
        },
        error: (err) => {
          this.error = err.error?.detail || 'Error al actualizar conductor';
          this.loading = false;
        }
      });
    } else {
      // Crear nuevo conductor
      this.apiService.createConductor(data).subscribe({
        next: () => {
          this.cargarConductores();
          this.mostrarFormulario = false;
          this.loading = false;
          this.error = '';
        },
        error: (err) => {
          this.error = err.error?.detail || 'Error al crear conductor';
          this.loading = false;
        }
      });
    }
  }

  getEstadoClass(activo: boolean): string {
    // Para los bordes dinámicos, usar clases específicas
    return activo ? 'estado-activo' : 'estado-inactivo';
  }

  getEstadoTexto(activo: boolean): string {
    return activo ? 'Activo' : 'Inactivo';
  }

  getAlertaClass(diasRestantes: number): string {
    if (diasRestantes < 0) return 'caducada';
    if (diasRestantes <= 30) return 'alerta';
    return 'ok';
  }

  getAlertaTexto(diasRestantes: number): string {
    if (diasRestantes < 0) return 'Caducada';
    if (diasRestantes <= 30) return `${diasRestantes} días`;
    return 'Válida';
  }

  formatearFecha(fecha: any): string {
    if (!fecha) return 'N/A';
    const date = fecha instanceof Date ? fecha : new Date(fecha);
    if (isNaN(date.getTime())) return 'N/A';
    const day = date.getDate().toString().padStart(2, '0');
    const month = (date.getMonth() + 1).toString().padStart(2, '0');
    const year = date.getFullYear().toString().padStart(4, '0');
    return `${day}/${month}/${year}`;
  }

  toggleActivo(conductor: any, event: Event): void {
    event.stopPropagation();
    const nuevoEstado = !conductor.activo;
    this.apiService.updateConductor(conductor.id, { activo: nuevoEstado }).subscribe({
      next: () => {
        // Actualizar el estado localmente
        conductor.activo = nuevoEstado;
        this.organizarConductoresPorEstado();
      },
      error: (err) => {
        this.error = err.error?.detail || 'Error al cambiar estado';
        this.cargarConductores();
      }
    });
  }

  eliminarConductor(conductor: any, event: Event): void {
    event.stopPropagation();
    const nombreCompleto = `${conductor.nombre} ${conductor.apellidos || ''}`.trim();
    if (confirm(`¿Está seguro de eliminar al conductor "${nombreCompleto}"?`)) {
      this.loading = true;
      this.apiService.deleteConductor(conductor.id).subscribe({
        next: () => {
          this.loading = false;
          this.cargarConductores();
        },
        error: (err) => {
          this.loading = false;
          this.error = err.error?.detail || 'Error al eliminar conductor';
        }
      });
    }
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

  irAUsuarios(): void {
    this.mostrarMenuUsuario = false;
    this.router.navigate(['/usuarios']);
  }

  logout(): void {
    this.mostrarMenuUsuario = false;
    this.authService.logout();
  }

  getEstadoRutaTexto(estado: string): string {
    const textos: { [key: string]: string } = {
      'planificada': 'Planificada',
      'en_curso': 'En curso',
      'completada': 'Completada',
      'cancelada': 'Cancelada'
    };
    return textos[estado?.toLowerCase()] || estado || '—';
  }

  getEstadoMantenimientoTexto(estado: string): string {
    const textos: { [key: string]: string } = {
      'programado': 'Programado',
      'en_curso': 'En curso',
      'completado': 'Completado',
      'vencido': 'Vencido',
      'cancelado': 'Cancelado'
    };
    return textos[estado?.toLowerCase()] || estado || '—';
  }

  getTipoMantenimientoTexto(tipo: string): string {
    const textos: { [key: string]: string } = {
      'preventivo': 'Preventivo',
      'correctivo': 'Correctivo',
      'revision': 'Revisión',
      'itv': 'ITV',
      'cambio_aceite': 'Cambio de aceite'
    };
    return textos[tipo?.toLowerCase()] || tipo || '—';
  }

  formatearFechaISO(fechaISO: string | null): string {
    if (!fechaISO) return '—';
    const d = new Date(fechaISO);
    if (isNaN(d.getTime())) return '—';
    return d.toLocaleDateString('es-ES', { day: '2-digit', month: '2-digit', year: 'numeric' }) +
      (fechaISO.includes('T') ? ' ' + d.toLocaleTimeString('es-ES', { hour: '2-digit', minute: '2-digit' }) : '');
  }
}

