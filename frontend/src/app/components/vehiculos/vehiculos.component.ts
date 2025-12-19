import { Component, OnInit, OnDestroy } from '@angular/core';
import { Router, NavigationEnd } from '@angular/router';
import { Subscription } from 'rxjs';
import { filter } from 'rxjs/operators';
import { ApiService } from '../../services/api.service';
import { AuthService } from '../../services/auth.service';
import { HttpErrorResponse } from '@angular/common/http';

@Component({
  selector: 'app-vehiculos',
  templateUrl: './vehiculos.component.html',
  styleUrls: ['./vehiculos.component.scss']
})
export class VehiculosComponent implements OnInit, OnDestroy {
  vehiculos: any[] = [];
  mostrarFormulario: boolean = false;
  editandoVehiculo: boolean = false;
  vehiculoIdEditando: number | null = null;
  vehiculoForm: any = {
    nombre: '',
    matricula: '',
    marca: '',
    modelo: '',
    ano: null,
    capacidad: null,
    tipo_combustible: '',
    estado: 'activo'
  };
  loading: boolean = false;
  error: string = '';
  currentRoute: string = '';
  mostrarMenuUsuario: boolean = false;
  usuario: any = null;
  private routerSubscription?: Subscription;
  
  estados = [
    { value: 'activo', label: 'Activo' },
    { value: 'en_mantenimiento', label: 'En Mantenimiento' },
    { value: 'inactivo', label: 'Inactivo' }
  ];
  
  tiposCombustible = [
    { value: 'gasolina', label: 'Gasolina' },
    { value: 'diesel', label: 'Diesel' },
    { value: 'electrico', label: 'Eléctrico' },
    { value: 'hibrido', label: 'Híbrido' },
    { value: 'gas', label: 'Gas' }
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
    if (!this.currentRoute.includes('/vehiculos')) {
      this.mostrarFormulario = false;
    }
    
    // Solo cargar vehículos si estamos en la ruta de vehículos
    if (this.currentRoute.includes('/vehiculos') && this.vehiculos.length === 0) {
      this.cargarVehiculos();
    }
  }

  ngOnDestroy(): void {
    if (this.routerSubscription) {
      this.routerSubscription.unsubscribe();
    }
  }

  cargarVehiculos(): void {
    this.loading = true;
    this.error = '';
    this.apiService.getVehiculos().subscribe({
      next: (data) => {
        // Mapear 'año' del backend a 'ano' para el frontend (opcional, pero mantenemos ambos)
        this.vehiculos = data.map((v: any) => ({
          ...v,
          ano: v['año'] || v.año // Añadir 'ano' para compatibilidad
        }));
        this.loading = false;
      },
      error: (err) => {
        if (err.status === 401) {
          this.authService.logout();
        } else {
          this.error = err.error?.detail || 'Error al cargar vehículos';
        }
        this.loading = false;
      }
    });
  }

  mostrarForm(): void {
    this.editandoVehiculo = false;
    this.vehiculoIdEditando = null;
    this.mostrarFormulario = true;
    this.vehiculoForm = {
      nombre: '',
      matricula: '',
      marca: '',
      modelo: '',
      ano: null,
      capacidad: null,
      tipo_combustible: '',
      estado: 'activo'
    };
  }

  editarVehiculo(vehiculo: any): void {
    this.editandoVehiculo = true;
    this.vehiculoIdEditando = vehiculo.id;
    this.mostrarFormulario = true;
    this.vehiculoForm = {
      nombre: vehiculo.nombre || '',
      matricula: vehiculo.matricula,
      marca: vehiculo.marca,
      modelo: vehiculo.modelo,
      ano: vehiculo['año'] || vehiculo.ano || null,
      capacidad: vehiculo.capacidad || null,
      tipo_combustible: vehiculo.tipo_combustible || '',
      estado: vehiculo.estado || 'activo'
    };
  }

  cancelarForm(): void {
    this.mostrarFormulario = false;
    this.editandoVehiculo = false;
    this.vehiculoIdEditando = null;
  }

  onSubmit(): void {
    if (!this.vehiculoForm.nombre || !this.vehiculoForm.matricula || !this.vehiculoForm.marca || !this.vehiculoForm.modelo) {
      this.error = 'El nombre, matrícula, marca y modelo son obligatorios';
      return;
    }

    // Mapear 'ano' a 'año' para el backend
    const vehiculoData = {
      ...this.vehiculoForm,
      año: this.vehiculoForm.ano
    };
    delete vehiculoData.ano;

    this.loading = true;
    
    if (this.editandoVehiculo && this.vehiculoIdEditando) {
      // Actualizar vehículo existente
      this.apiService.updateVehiculo(this.vehiculoIdEditando, vehiculoData).subscribe({
        next: () => {
          this.cargarVehiculos();
          this.mostrarFormulario = false;
          this.editandoVehiculo = false;
          this.vehiculoIdEditando = null;
          this.loading = false;
          this.error = '';
        },
        error: (err: HttpErrorResponse) => {
          this.error = err.error?.detail || err.error?.message || err.message || 'Error al actualizar vehículo';
          this.loading = false;
          if (err.status === 401) {
            this.authService.logout();
          }
        }
      });
    } else {
      // Crear nuevo vehículo
      this.apiService.createVehiculo(vehiculoData).subscribe({
        next: () => {
          this.cargarVehiculos();
          this.mostrarFormulario = false;
          this.loading = false;
          this.error = '';
        },
        error: (err: HttpErrorResponse) => {
          this.error = err.error?.detail || err.error?.message || err.message || 'Error al crear vehículo';
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
      'activo': 'activo',
      'en_mantenimiento': 'mantenimiento',
      'inactivo': 'inactivo'
    };
    return clases[estado?.toLowerCase()] || 'inactivo';
  }

  getEstadoTexto(estado: string): string {
    const textos: { [key: string]: string } = {
      'activo': 'Activo',
      'en_mantenimiento': 'En Mantenimiento',
      'inactivo': 'Inactivo'
    };
    return textos[estado?.toLowerCase()] || estado || 'Inactivo';
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

