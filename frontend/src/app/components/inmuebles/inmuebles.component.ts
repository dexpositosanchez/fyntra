import { Component, OnInit, OnDestroy } from '@angular/core';
import { Router, NavigationEnd } from '@angular/router';
import { Subscription } from 'rxjs';
import { filter } from 'rxjs/operators';
import { ApiService } from '../../services/api.service';
import { AuthService } from '../../services/auth.service';

@Component({
  selector: 'app-inmuebles',
  templateUrl: './inmuebles.component.html',
  styleUrls: ['./inmuebles.component.scss']
})
export class InmueblesComponent implements OnInit, OnDestroy {
  inmuebles: any[] = [];
  comunidades: any[] = [];
  propietarios: any[] = [];
  mostrarFormulario: boolean = false;
  editandoInmueble: boolean = false;
  inmuebleIdEditando: number | null = null;
  inmuebleForm: any = {
    comunidad_id: '',
    referencia: '',
    direccion: '',
    metros: null,
    tipo: '',
    propietario_ids: []
  };
  loading: boolean = false;
  error: string = '';
  currentRoute: string = '';
  mostrarMenuUsuario: boolean = false;
  usuario: any = null;
  filtroComunidad: string = '';
  filtroTipo: string = '';
  textoBusqueda: string = '';
  inmueblesFiltrados: any[] = [];
  esPropietario: boolean = false;
  private routerSubscription?: Subscription;

  tiposInmueble = [
    { value: 'vivienda', label: 'Vivienda' },
    { value: 'local', label: 'Local' },
    { value: 'garaje', label: 'Garaje' },
    { value: 'trastero', label: 'Trastero' },
    { value: 'oficina', label: 'Oficina' }
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
    if (!this.esPropietario) {
      this.cargarComunidades();
      this.cargarPropietarios();
    }
    this.cargarInmuebles();
    
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

  cargarComunidades(): void {
    this.apiService.getComunidades().subscribe({
      next: (data) => {
        this.comunidades = data;
      },
      error: (err) => {
        console.error('Error al cargar comunidades:', err);
      }
    });
  }

  cargarPropietarios(): void {
    this.apiService.getPropietarios().subscribe({
      next: (data) => {
        this.propietarios = data;
      },
      error: (err) => {
        console.error('Error al cargar propietarios:', err);
      }
    });
  }

  cargarInmuebles(): void {
    this.loading = true;
    this.error = '';
    
    const params: any = {};
    if (this.filtroComunidad) params.comunidad_id = this.filtroComunidad;
    if (this.filtroTipo) params.tipo = this.filtroTipo;
    
    this.apiService.getInmuebles(params).subscribe({
      next: (data) => {
        this.inmuebles = data;
        this.aplicarFiltroTexto();
        this.loading = false;
      },
      error: (err) => {
        if (err.status === 401) {
          this.authService.logout();
        } else {
          this.error = err.error?.detail || 'Error al cargar inmuebles';
        }
        this.loading = false;
      }
    });
  }

  aplicarFiltros(): void {
    // Si hay filtros de comunidad o tipo, recargar desde el backend
    if (this.filtroComunidad || this.filtroTipo) {
      this.cargarInmuebles();
    } else {
      // Si solo hay búsqueda de texto, aplicar filtro local
      this.aplicarFiltroTexto();
    }
  }

  aplicarFiltroTexto(): void {
    // Aplicar filtro de búsqueda de texto sobre los inmuebles cargados
    if (!this.textoBusqueda || this.textoBusqueda.trim() === '') {
      this.inmueblesFiltrados = [...this.inmuebles];
    } else {
      const busqueda = this.textoBusqueda.toLowerCase().trim();
      this.inmueblesFiltrados = this.inmuebles.filter(inmueble => {
        const referencia = (inmueble.referencia || '').toLowerCase();
        const direccion = (inmueble.direccion || '').toLowerCase();
        
        return referencia.includes(busqueda) ||
               direccion.includes(busqueda);
      });
    }
  }

  limpiarBusqueda(): void {
    this.textoBusqueda = '';
    this.aplicarFiltroTexto();
  }

  limpiarFiltros(): void {
    this.filtroComunidad = '';
    this.filtroTipo = '';
    this.textoBusqueda = '';
    this.cargarInmuebles();
  }

  mostrarForm(): void {
    this.editandoInmueble = false;
    this.inmuebleIdEditando = null;
    this.mostrarFormulario = true;
    this.inmuebleForm = {
      comunidad_id: '',
      referencia: '',
      direccion: '',
      metros: null,
      tipo: '',
      propietario_ids: []
    };
  }

  editarInmueble(inmueble: any): void {
    this.editandoInmueble = true;
    this.inmuebleIdEditando = inmueble.id;
    this.mostrarFormulario = true;
    
    // Filtrar propietarios que realmente existen (por si alguno fue eliminado)
    const propietariosValidos = inmueble.propietarios?.filter((p: any) => 
      this.propietarios.some(prop => prop.id === p.id)
    ) || [];
    
    this.inmuebleForm = {
      comunidad_id: inmueble.comunidad_id || '',
      referencia: inmueble.referencia || '',
      direccion: inmueble.direccion || '',
      metros: inmueble.metros || null,
      tipo: inmueble.tipo || '',
      propietario_ids: propietariosValidos.map((p: any) => p.id)
    };
  }

  cancelarForm(): void {
    this.mostrarFormulario = false;
    this.editandoInmueble = false;
    this.inmuebleIdEditando = null;
  }

  onSubmit(): void {
    if (!this.inmuebleForm.comunidad_id || !this.inmuebleForm.referencia) {
      this.error = 'La comunidad y referencia son obligatorias';
      return;
    }

    this.loading = true;
    
    const data = {
      ...this.inmuebleForm,
      comunidad_id: Number(this.inmuebleForm.comunidad_id),
      metros: this.inmuebleForm.metros ? Number(this.inmuebleForm.metros) : null
    };
    
    if (this.editandoInmueble && this.inmuebleIdEditando) {
      this.apiService.updateInmueble(this.inmuebleIdEditando, data).subscribe({
        next: () => {
          this.cargarInmuebles();
          this.mostrarFormulario = false;
          this.editandoInmueble = false;
          this.inmuebleIdEditando = null;
          this.loading = false;
          this.error = '';
        },
        error: (err) => {
          this.error = err.error?.detail || 'Error al actualizar inmueble';
          this.loading = false;
        }
      });
    } else {
      this.apiService.createInmueble(data).subscribe({
        next: () => {
          this.cargarInmuebles();
          this.mostrarFormulario = false;
          this.loading = false;
          this.error = '';
        },
        error: (err) => {
          this.error = err.error?.detail || 'Error al crear inmueble';
          this.loading = false;
        }
      });
    }
  }

  eliminarInmueble(inmueble: any, event: Event): void {
    event.stopPropagation();
    if (confirm(`¿Está seguro de eliminar el inmueble "${inmueble.referencia}"?`)) {
      this.apiService.deleteInmueble(inmueble.id).subscribe({
        next: () => {
          this.cargarInmuebles();
        },
        error: (err) => {
          this.error = err.error?.detail || 'Error al eliminar inmueble';
        }
      });
    }
  }

  getTipoLabel(tipo: string): string {
    const found = this.tiposInmueble.find(t => t.value === tipo);
    return found ? found.label : tipo || 'Sin tipo';
  }

  getTipoClass(tipo: string): string {
    return tipo || 'sin-tipo';
  }

  // Métodos para selector de propietarios
  togglePropietario(propietarioId: number): void {
    const index = this.inmuebleForm.propietario_ids.indexOf(propietarioId);
    if (index > -1) {
      this.inmuebleForm.propietario_ids.splice(index, 1);
    } else {
      this.inmuebleForm.propietario_ids.push(propietarioId);
    }
  }

  getPropietarioNombre(propietarioId: number): string {
    const prop = this.propietarios.find(p => p.id === propietarioId);
    // Si no se encuentra, el propietario fue eliminado - retornar string vacío para que no se muestre
    return prop ? `${prop.nombre} ${prop.apellidos || ''}`.trim() : '';
  }

  getPropietariosDisponibles(): any[] {
    return this.propietarios.filter(p => !this.inmuebleForm.propietario_ids.includes(p.id));
  }

  onPropietarioSelect(event: any): void {
    const propietarioId = Number(event.target.value);
    if (propietarioId && !this.inmuebleForm.propietario_ids.includes(propietarioId)) {
      this.inmuebleForm.propietario_ids.push(propietarioId);
    }
    event.target.value = '';
  }

  toggleMenuUsuario(): void {
    this.mostrarMenuUsuario = !this.mostrarMenuUsuario;
  }

  estaEnModuloFincas(): boolean {
    return this.currentRoute.includes('/incidencias') || 
           this.currentRoute.includes('/comunidades') ||
           this.currentRoute.includes('/inmuebles');
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

