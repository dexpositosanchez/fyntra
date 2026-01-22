import { Component, OnInit, OnDestroy } from '@angular/core';
import { Router, NavigationEnd } from '@angular/router';
import { Subscription } from 'rxjs';
import { filter } from 'rxjs/operators';
import { ApiService } from '../../services/api.service';
import { AuthService } from '../../services/auth.service';

@Component({
  selector: 'app-comunidades',
  templateUrl: './comunidades.component.html',
  styleUrls: ['./comunidades.component.scss']
})
export class ComunidadesComponent implements OnInit, OnDestroy {
  comunidades: any[] = [];
  mostrarFormulario: boolean = false;
  editandoComunidad: boolean = false;
  comunidadIdEditando: number | null = null;
  comunidadForm: any = {
    nombre: '',
    cif: '',
    direccion: '',
    telefono: '',
    email: ''
  };
  loading: boolean = false;
  error: string = '';
  currentRoute: string = '';
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
    
    this.routerSubscription = this.router.events
      .pipe(filter(event => event instanceof NavigationEnd))
      .subscribe((event: any) => {
        this.currentRoute = event.url;
        this.actualizarVista();
      });
  }

  actualizarVista(): void {
    if (!this.currentRoute.includes('/comunidades')) {
      this.mostrarFormulario = false;
    }
    
    if (this.currentRoute.includes('/comunidades') && this.comunidades.length === 0) {
      this.cargarComunidades();
    }
  }

  ngOnDestroy(): void {
    if (this.routerSubscription) {
      this.routerSubscription.unsubscribe();
    }
  }

  cargarComunidades(): void {
    this.loading = true;
    this.error = '';
    
    this.apiService.getComunidades().subscribe({
      next: (data) => {
        console.log('Comunidades recibidas:', data);
        this.comunidades = data;
        this.loading = false;
      },
      error: (err) => {
        if (err.status === 401) {
          this.authService.logout();
        } else {
          this.error = err.error?.detail || 'Error al cargar comunidades';
        }
        this.loading = false;
      }
    });
  }

  mostrarForm(): void {
    this.editandoComunidad = false;
    this.comunidadIdEditando = null;
    this.mostrarFormulario = true;
    this.comunidadForm = {
      nombre: '',
      cif: '',
      direccion: '',
      telefono: '',
      email: ''
    };
  }

  editarComunidad(comunidad: any): void {
    this.editandoComunidad = true;
    this.comunidadIdEditando = comunidad.id;
    this.mostrarFormulario = true;
    
    this.comunidadForm = {
      nombre: comunidad.nombre || '',
      cif: comunidad.cif || '',
      direccion: comunidad.direccion || '',
      telefono: comunidad.telefono || '',
      email: comunidad.email || ''
    };
  }

  cancelarForm(): void {
    this.mostrarFormulario = false;
    this.editandoComunidad = false;
    this.comunidadIdEditando = null;
  }

  onSubmit(): void {
    if (!this.comunidadForm.nombre) {
      this.error = 'El nombre es obligatorio';
      return;
    }

    this.loading = true;
    
    if (this.editandoComunidad && this.comunidadIdEditando) {
      this.apiService.updateComunidad(this.comunidadIdEditando, this.comunidadForm).subscribe({
        next: () => {
          this.cargarComunidades();
          this.mostrarFormulario = false;
          this.editandoComunidad = false;
          this.comunidadIdEditando = null;
          this.loading = false;
          this.error = '';
        },
        error: (err) => {
          this.error = err.error?.detail || 'Error al actualizar comunidad';
          this.loading = false;
        }
      });
    } else {
      this.apiService.createComunidad(this.comunidadForm).subscribe({
        next: () => {
          this.cargarComunidades();
          this.mostrarFormulario = false;
          this.loading = false;
          this.error = '';
        },
        error: (err) => {
          this.error = err.error?.detail || 'Error al crear comunidad';
          this.loading = false;
        }
      });
    }
  }

  eliminarComunidad(comunidad: any, event: Event): void {
    event.stopPropagation();
    
    console.log('Comunidad a eliminar:', comunidad);
    console.log('Inmuebles de la comunidad:', comunidad.inmuebles);
    
    const numInmuebles = comunidad.inmuebles?.length || 0;
    let mensaje = `¿Está seguro de eliminar la comunidad "${comunidad.nombre}"?`;
    
    if (numInmuebles > 0) {
      mensaje += `\n\n⚠️ ADVERTENCIA: Al eliminar esta comunidad, se eliminarán también todos sus ${numInmuebles} inmueble(s) asociado(s).`;
      mensaje += `\n\nLos propietarios NO se eliminarán, solo se quitará su relación con los inmuebles.`;
    }
    
    if (confirm(mensaje)) {
      this.apiService.deleteComunidad(comunidad.id).subscribe({
        next: () => {
          this.cargarComunidades();
        },
        error: (err) => {
          this.error = err.error?.detail || 'Error al eliminar comunidad';
        }
      });
    }
  }

  toggleMenuUsuario(): void {
    this.mostrarMenuUsuario = !this.mostrarMenuUsuario;
  }

  estaEnModuloFincas(): boolean {
    return this.currentRoute.includes('/incidencias') || 
           this.currentRoute.includes('/comunidades');
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

