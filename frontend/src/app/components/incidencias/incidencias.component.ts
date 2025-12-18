import { Component, OnInit, OnDestroy } from '@angular/core';
import { Router, NavigationEnd } from '@angular/router';
import { Subscription } from 'rxjs';
import { filter } from 'rxjs/operators';
import { ApiService } from '../../services/api.service';
import { AuthService } from '../../services/auth.service';

@Component({
  selector: 'app-incidencias',
  templateUrl: './incidencias.component.html',
  styleUrls: ['./incidencias.component.scss']
})
export class IncidenciasComponent implements OnInit, OnDestroy {
  incidencias: any[] = [];
  inmuebles: any[] = [];
  proveedores: any[] = [];
  loading: boolean = false;
  error: string = '';
  filtroFecha: string = '';
  filtroPrioridad: string = '';
  filtroEstado: string = '';
  currentRoute: string = '';
  mostrarMenuUsuario: boolean = false;
  mostrarFormulario: boolean = false;
  editandoIncidencia: boolean = false;
  incidenciaIdEditando: number | null = null;
  incidenciaSeleccionada: any = null;
  mostrarHistorial: boolean = false;
  usuario: any = null;
  esPropietario: boolean = false;
  private routerSubscription?: Subscription;

  incidenciaForm: any = {
    titulo: '',
    descripcion: '',
    prioridad: 'media',
    inmueble_id: '',
    estado: 'abierta',
    proveedor_id: null,
    comentario_cambio: ''
  };

  estados = [
    { value: 'abierta', label: 'Abierta' },
    { value: 'asignada', label: 'Asignada' },
    { value: 'en_progreso', label: 'En Progreso' },
    { value: 'resuelta', label: 'Resuelta' },
    { value: 'cerrada', label: 'Cerrada' }
  ];

  prioridades = [
    { value: 'baja', label: 'Baja' },
    { value: 'media', label: 'Media' },
    { value: 'alta', label: 'Alta' },
    { value: 'urgente', label: 'Urgente' }
  ];

  constructor(
    private apiService: ApiService,
    private authService: AuthService,
    private router: Router
  ) {}

  ngOnInit(): void {
    this.currentRoute = this.router.url;
    this.usuario = this.authService.getUsuario();
    this.esPropietario = this.usuario?.rol === 'propietario';
    this.cargarInmuebles();
    if (!this.esPropietario) {
      this.cargarProveedores();
    }
    this.actualizarVista();
    
    // Suscribirse a cambios de ruta
    this.routerSubscription = this.router.events
      .pipe(filter(event => event instanceof NavigationEnd))
      .subscribe((event: any) => {
        this.currentRoute = event.url;
        this.actualizarVista();
      });
  }

  cargarInmuebles(): void {
    this.apiService.getInmuebles().subscribe({
      next: (data) => this.inmuebles = data,
      error: () => this.inmuebles = []
    });
  }

  cargarProveedores(): void {
    this.apiService.getProveedores().subscribe({
      next: (data) => this.proveedores = data,
      error: () => this.proveedores = []
    });
  }

  actualizarVista(): void {
    // Solo cargar incidencias si estamos en la ruta de incidencias
    if (this.currentRoute.includes('/incidencias') && this.incidencias.length === 0) {
      this.cargarIncidencias();
    }
  }

  ngOnDestroy(): void {
    if (this.routerSubscription) {
      this.routerSubscription.unsubscribe();
    }
  }

  cargarIncidencias(): void {
    this.loading = true;
    this.apiService.getIncidenciasSinResolver().subscribe({
      next: (data) => {
        this.incidencias = data;
        this.loading = false;
      },
      error: (err) => {
        this.error = 'Error al cargar incidencias';
        this.loading = false;
        // Datos de prueba si no hay conexión
        this.incidencias = [
          {
            id: 1,
            prioridad: 'urgente',
            fecha_alta: new Date('2025-11-02'),
            titulo: 'Avería en fontanería'
          },
          {
            id: 2,
            prioridad: 'alta',
            fecha_alta: new Date('2025-11-02'),
            titulo: 'Problema eléctrico'
          },
          {
            id: 3,
            prioridad: 'media',
            fecha_alta: new Date('2025-11-02'),
            titulo: 'Reparación de persiana'
          },
          {
            id: 4,
            prioridad: 'baja',
            fecha_alta: new Date('2025-11-02'),
            titulo: 'Limpieza de fachada'
          }
        ];
        this.loading = false;
      }
    });
  }

  getPrioridadClass(prioridad: string): string {
    const clases: { [key: string]: string } = {
      'urgente': 'prioridad-urgente',
      'alta': 'prioridad-alta',
      'media': 'prioridad-media',
      'baja': 'prioridad-baja'
    };
    return clases[prioridad?.toLowerCase()] || 'prioridad-media';
  }
  
  getPrioridadTexto(prioridad: string): string {
    const textos: { [key: string]: string } = {
      'urgente': 'Urgente',
      'alta': 'Alta',
      'media': 'Media',
      'baja': 'Baja'
    };
    return textos[prioridad?.toLowerCase()] || prioridad || 'Media';
  }

  mostrarForm(): void {
    this.mostrarFormulario = true;
    this.editandoIncidencia = false;
    this.incidenciaIdEditando = null;
    this.incidenciaForm = {
      titulo: '',
      descripcion: '',
      prioridad: 'media',
      inmueble_id: this.inmuebles.length === 1 ? this.inmuebles[0].id : '',
      estado: 'abierta',
      proveedor_id: null,
      comentario_cambio: ''
    };
  }

  editarIncidencia(incidencia: any): void {
    this.mostrarFormulario = true;
    this.editandoIncidencia = true;
    this.incidenciaIdEditando = incidencia.id;
    this.incidenciaForm = {
      titulo: incidencia.titulo,
      descripcion: incidencia.descripcion || '',
      prioridad: incidencia.prioridad,
      inmueble_id: incidencia.inmueble_id,
      estado: incidencia.estado,
      proveedor_id: incidencia.proveedor_id,
      comentario_cambio: '',
      version: incidencia.version
    };
  }

  cancelarForm(): void {
    this.mostrarFormulario = false;
    this.editandoIncidencia = false;
    this.incidenciaIdEditando = null;
    this.error = '';
  }

  onSubmit(): void {
    this.loading = true;
    this.error = '';

    if (this.editandoIncidencia && this.incidenciaIdEditando) {
      const updateData: any = {
        titulo: this.incidenciaForm.titulo,
        descripcion: this.incidenciaForm.descripcion,
        prioridad: this.incidenciaForm.prioridad,
        estado: this.incidenciaForm.estado,
        proveedor_id: this.incidenciaForm.proveedor_id || null,
        version: this.incidenciaForm.version,
        comentario_cambio: this.incidenciaForm.comentario_cambio || null
      };

      this.apiService.updateIncidencia(this.incidenciaIdEditando, updateData).subscribe({
        next: () => {
          this.loading = false;
          this.cancelarForm();
          this.cargarIncidencias();
        },
        error: (err) => {
          this.loading = false;
          this.error = err.error?.detail || 'Error al actualizar incidencia';
        }
      });
    } else {
      const createData = {
        titulo: this.incidenciaForm.titulo,
        descripcion: this.incidenciaForm.descripcion,
        prioridad: this.incidenciaForm.prioridad,
        inmueble_id: parseInt(this.incidenciaForm.inmueble_id)
      };

      this.apiService.createIncidencia(createData).subscribe({
        next: () => {
          this.loading = false;
          this.cancelarForm();
          this.cargarIncidencias();
        },
        error: (err) => {
          this.loading = false;
          this.error = err.error?.detail || 'Error al crear incidencia';
        }
      });
    }
  }

  eliminarIncidencia(incidencia: any, event: Event): void {
    event.stopPropagation();
    if (confirm(`¿Eliminar incidencia "${incidencia.titulo}"?`)) {
      this.apiService.deleteIncidencia(incidencia.id).subscribe({
        next: () => this.cargarIncidencias(),
        error: (err) => this.error = err.error?.detail || 'Error al eliminar'
      });
    }
  }

  verHistorial(incidencia: any, event: Event): void {
    event.stopPropagation();
    this.incidenciaSeleccionada = incidencia;
    this.mostrarHistorial = true;
  }

  cerrarHistorial(): void {
    this.mostrarHistorial = false;
    this.incidenciaSeleccionada = null;
  }

  getEstadoLabel(estado: string): string {
    const est = this.estados.find(e => e.value === estado);
    return est ? est.label : estado;
  }

  getEstadoClass(estado: string): string {
    return 'estado-' + estado.replace('_', '-');
  }

  getInmuebleNombre(inmuebleId: number): string {
    const inmueble = this.inmuebles.find(i => i.id === inmuebleId);
    return inmueble ? `${inmueble.referencia} - ${inmueble.direccion || ''}` : 'N/A';
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
