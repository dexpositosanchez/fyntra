import { Component, OnInit, OnDestroy } from '@angular/core';
import { Router, NavigationEnd } from '@angular/router';
import { Subscription } from 'rxjs';
import { filter } from 'rxjs/operators';
import { ApiService } from '../../services/api.service';
import { AuthService } from '../../services/auth.service';

@Component({
  selector: 'app-propietarios',
  templateUrl: './propietarios.component.html',
  styleUrls: ['./propietarios.component.scss']
})
export class PropietariosComponent implements OnInit, OnDestroy {
  propietarios: any[] = [];
  inmuebles: any[] = [];
  mostrarFormulario: boolean = false;
  editandoPropietario: boolean = false;
  propietarioIdEditando: number | null = null;
  propietarioForm: any = {
    nombre: '',
    apellidos: '',
    email: '',
    telefono: '',
    dni: '',
    inmueble_ids: [],
    crear_usuario: false,
    password: ''
  };
  loading: boolean = false;
  error: string = '';
  currentRoute: string = '';
  mostrarMenuUsuario: boolean = false;
  mostrarMenuNav: boolean = false;
  usuario: any = null;
  exportandoDatos: boolean = false;
  eliminandoCuenta: boolean = false;
  textoBusqueda: string = '';
  propietariosFiltrados: any[] = [];
  private routerSubscription?: Subscription;

  constructor(
    private apiService: ApiService,
    private authService: AuthService,
    private router: Router
  ) {}

  ngOnInit(): void {
    this.currentRoute = this.router.url;
    this.usuario = this.authService.getUsuario();
    this.cargarInmuebles();
    this.cargarPropietarios();
    
    this.routerSubscription = this.router.events
      .pipe(filter(event => event instanceof NavigationEnd))
      .subscribe((event: any) => {
        this.currentRoute = event.url;
      });
  }

  ngOnDestroy(): void {
    if (this.routerSubscription) {
      this.routerSubscription.unsubscribe();
    }
  }

  cargarInmuebles(): void {
    this.apiService.getInmuebles().subscribe({
      next: (data) => {
        this.inmuebles = data;
      },
      error: (err) => {
        console.error('Error al cargar inmuebles:', err);
      }
    });
  }

  cargarPropietarios(): void {
    this.loading = true;
    this.error = '';
    
    this.apiService.getPropietarios().subscribe({
      next: (data) => {
        this.propietarios = data;
        this.aplicarFiltroBusqueda();
        this.loading = false;
      },
      error: (err) => {
        if (err.status === 401) {
          this.authService.logout();
        } else {
          this.error = err.error?.detail || 'Error al cargar propietarios';
        }
        this.loading = false;
      }
    });
  }

  mostrarForm(): void {
    this.editandoPropietario = false;
    this.propietarioIdEditando = null;
    this.mostrarFormulario = true;
    this.propietarioForm = {
      nombre: '',
      apellidos: '',
      email: '',
      telefono: '',
      dni: '',
      inmueble_ids: [],
      crear_usuario: false,
      password: ''
    };
  }

  editarPropietario(propietario: any): void {
    this.editandoPropietario = true;
    this.propietarioIdEditando = propietario.id;
    this.mostrarFormulario = true;
    
    this.propietarioForm = {
      nombre: propietario.nombre || '',
      apellidos: propietario.apellidos || '',
      email: propietario.email || '',
      telefono: propietario.telefono || '',
      dni: propietario.dni || '',
      inmueble_ids: propietario.inmuebles?.map((i: any) => i.id) || [],
      crear_usuario: false,
      password: '',
      tiene_acceso: propietario.tiene_acceso || false
    };
  }

  cancelarForm(): void {
    this.mostrarFormulario = false;
    this.editandoPropietario = false;
    this.propietarioIdEditando = null;
  }

  toggleInmueble(inmuebleId: number): void {
    const index = this.propietarioForm.inmueble_ids.indexOf(inmuebleId);
    if (index > -1) {
      this.propietarioForm.inmueble_ids.splice(index, 1);
    } else {
      this.propietarioForm.inmueble_ids.push(inmuebleId);
    }
  }

  isInmuebleSeleccionado(inmuebleId: number): boolean {
    return this.propietarioForm.inmueble_ids.includes(inmuebleId);
  }

  getInmuebleNombre(inmuebleId: number): string {
    const inmueble = this.inmuebles.find(i => i.id === inmuebleId);
    return inmueble ? inmueble.referencia : 'Desconocido';
  }

  getInmueblesDisponibles(): any[] {
    return this.inmuebles.filter(i => !this.propietarioForm.inmueble_ids.includes(i.id));
  }

  onInmuebleSelect(event: any): void {
    const inmuebleId = Number(event.target.value);
    if (inmuebleId && !this.propietarioForm.inmueble_ids.includes(inmuebleId)) {
      this.propietarioForm.inmueble_ids.push(inmuebleId);
    }
    event.target.value = '';
  }

  onSubmit(): void {
    if (!this.propietarioForm.nombre) {
      this.error = 'El nombre es obligatorio';
      return;
    }
    
    if (this.propietarioForm.crear_usuario) {
      if (!this.propietarioForm.email) {
        this.error = 'Se requiere email para crear acceso al sistema';
        return;
      }
      if (!this.propietarioForm.password || this.propietarioForm.password.length < 6) {
        this.error = 'La contraseña debe tener al menos 6 caracteres';
        return;
      }
    }

    this.loading = true;
    
    // Preparar datos (no enviar password si no se crea usuario)
    const data = { ...this.propietarioForm };
    if (!data.crear_usuario) {
      delete data.password;
    }
    delete data.tiene_acceso;
    
    if (this.editandoPropietario && this.propietarioIdEditando) {
      // En edición no se puede crear usuario (por ahora)
      delete data.crear_usuario;
      delete data.password;
      this.apiService.updatePropietario(this.propietarioIdEditando, data).subscribe({
        next: () => {
          this.cargarPropietarios();
          this.mostrarFormulario = false;
          this.editandoPropietario = false;
          this.propietarioIdEditando = null;
          this.loading = false;
          this.error = '';
        },
        error: (err) => {
          this.error = err.error?.detail || 'Error al actualizar propietario';
          this.loading = false;
        }
      });
    } else {
      this.apiService.createPropietario(data).subscribe({
        next: () => {
          this.cargarPropietarios();
          this.mostrarFormulario = false;
          this.loading = false;
          this.error = '';
        },
        error: (err) => {
          this.error = err.error?.detail || 'Error al crear propietario';
          this.loading = false;
        }
      });
    }
  }

  eliminarPropietario(propietario: any, event: Event): void {
    event.stopPropagation();
    if (confirm(`¿Está seguro de eliminar al propietario "${propietario.nombre} ${propietario.apellidos || ''}"?`)) {
      this.apiService.deletePropietario(propietario.id).subscribe({
        next: () => {
          this.cargarPropietarios();
        },
        error: (err) => {
          this.error = err.error?.detail || 'Error al eliminar propietario';
        }
      });
    }
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

  estaEnModuloFincas(): boolean {
    return this.currentRoute.includes('/incidencias') || 
           this.currentRoute.includes('/comunidades') ||
           this.currentRoute.includes('/inmuebles') ||
           this.currentRoute.includes('/propietarios') ||
           this.currentRoute.includes('/proveedores') ||
           this.currentRoute.includes('/informes');
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

  aplicarFiltroBusqueda(): void {
    // Aplicar filtro de búsqueda
    if (!this.textoBusqueda || this.textoBusqueda.trim() === '') {
      this.propietariosFiltrados = [...this.propietarios];
    } else {
      const busqueda = this.textoBusqueda.toLowerCase().trim();
      this.propietariosFiltrados = this.propietarios.filter(propietario => {
        const nombreCompleto = `${propietario.nombre || ''} ${propietario.apellidos || ''}`.toLowerCase();
        const telefono = (propietario.telefono || '').toLowerCase();
        const email = (propietario.email || '').toLowerCase();
        const dni = (propietario.dni || '').toLowerCase();
        
        return nombreCompleto.includes(busqueda) ||
               telefono.includes(busqueda) ||
               email.includes(busqueda) ||
               dni.includes(busqueda);
      });
    }
  }

  limpiarBusqueda(): void {
    this.textoBusqueda = '';
    this.aplicarFiltroBusqueda();
  }
}

