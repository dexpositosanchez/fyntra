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
  mostrarFormulario: boolean = false;
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
    // Ocultar formulario si cambiamos de ruta
    if (!this.currentRoute.includes('/conductores')) {
      this.mostrarFormulario = false;
    }
    
    // Solo cargar conductores si estamos en la ruta de conductores
    if (this.currentRoute.includes('/conductores') && this.conductores.length === 0) {
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
  }

  cancelarForm(): void {
    this.mostrarFormulario = false;
    this.editandoConductor = false;
    this.conductorIdEditando = null;
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
}

