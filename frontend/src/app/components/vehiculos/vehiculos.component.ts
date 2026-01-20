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
  vehiculosPorEstado: { [key: string]: any[] } = {};
  tabs: { estado: string, label: string, count: number }[] = [];
  tabActiva: string = '';
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
        this.agruparPorEstado();
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
    // Convertir cadenas vacías a null para campos opcionales
    const vehiculoData: any = {
      ...this.vehiculoForm,
      año: this.vehiculoForm.ano || null,
      capacidad: this.vehiculoForm.capacidad || null,
      tipo_combustible: this.vehiculoForm.tipo_combustible && this.vehiculoForm.tipo_combustible.trim() !== '' 
        ? this.vehiculoForm.tipo_combustible 
        : null
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
          this.error = this.parsearError(err);
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
          this.error = this.parsearError(err);
          this.loading = false;
          if (err.status === 401) {
            this.authService.logout();
          }
        }
      });
    }
  }

  parsearError(err: HttpErrorResponse): string {
    // Si hay un detalle directo y es un string, usarlo
    if (err.error?.detail && typeof err.error.detail === 'string') {
      // Mejorar mensajes de validación comunes
      let mensaje = err.error.detail;
      
      // Mensajes de validación de Pydantic
      if (mensaje.includes('tipo_combustible')) {
        if (mensaje.includes("Input should be")) {
          return 'El tipo de combustible seleccionado no es válido. Por favor, seleccione una opción válida o deje el campo vacío.';
        }
        return 'Error en el tipo de combustible. Por favor, seleccione una opción válida o deje el campo vacío.';
      }
      
      // Otros errores comunes
      if (mensaje.includes('matricula')) {
        return 'Ya existe un vehículo con esta matrícula. Por favor, use una matrícula diferente.';
      }
      
      return mensaje;
    }
    
    // Si hay un array de errores (formato de validación de Pydantic)
    if (Array.isArray(err.error?.detail)) {
      const errores = err.error.detail.map((e: any) => {
        const campo = e.loc && e.loc.length > 1 ? e.loc[e.loc.length - 1] : 'campo';
        let mensajeCampo = '';
        
        // Traducir nombres de campos
        const nombresCampos: { [key: string]: string } = {
          'tipo_combustible': 'Tipo de combustible',
          'matricula': 'Matrícula',
          'nombre': 'Nombre',
          'marca': 'Marca',
          'modelo': 'Modelo',
          'año': 'Año',
          'capacidad': 'Capacidad',
          'estado': 'Estado'
        };
        
        const nombreCampo = nombresCampos[campo] || campo;
        
        if (e.type === 'enum') {
          return `${nombreCampo}: Por favor, seleccione una opción válida o deje el campo vacío.`;
        }
        
        if (e.msg) {
          mensajeCampo = e.msg;
          // Mejorar mensajes comunes
          if (mensajeCampo.includes('Input should be')) {
            return `${nombreCampo}: El valor proporcionado no es válido.`;
          }
          return `${nombreCampo}: ${mensajeCampo}`;
        }
        
        return `${nombreCampo}: Error de validación`;
      });
      
      return errores.join(' ');
    }
    
    // Si hay un objeto con mensaje
    if (err.error?.message) {
      return err.error.message;
    }
    
    // Mensaje genérico
    return 'Error al procesar la solicitud. Por favor, verifique los datos e intente nuevamente.';
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

  agruparPorEstado(): void {
    // Inicializar objeto de agrupación
    this.vehiculosPorEstado = {};
    
    // Agrupar vehículos por estado
    this.vehiculos.forEach(vehiculo => {
      const estado = vehiculo.estado || 'inactivo';
      if (!this.vehiculosPorEstado[estado]) {
        this.vehiculosPorEstado[estado] = [];
      }
      this.vehiculosPorEstado[estado].push(vehiculo);
    });

    // Crear array de tabs con contadores, excluyendo estados con 0 items
    this.tabs = this.estados
      .map(estado => ({
        estado: estado.value,
        label: estado.label,
        count: this.vehiculosPorEstado[estado.value]?.length || 0
      }))
      .filter(tab => tab.count > 0)
      .sort((a, b) => {
        // Ordenar: primero "activo" o similar, al final "inactivo" o similar
        const ordenEstados: { [key: string]: number } = {
          'activo': 1,
          'en_mantenimiento': 2,
          'inactivo': 99
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

  getVehiculosTabActiva(): any[] {
    return this.vehiculosPorEstado[this.tabActiva] || [];
  }

  eliminarVehiculo(vehiculo: any, event: Event): void {
    event.stopPropagation();
    const nombreVehiculo = vehiculo.nombre || vehiculo.matricula || 'este vehículo';
    if (confirm(`¿Está seguro de eliminar el vehículo "${nombreVehiculo}"?`)) {
      this.loading = true;
      this.apiService.deleteVehiculo(vehiculo.id).subscribe({
        next: () => {
          this.cargarVehiculos();
          this.loading = false;
          this.error = '';
        },
        error: (err: HttpErrorResponse) => {
          this.error = err.error?.detail || 'Error al eliminar vehículo';
          this.loading = false;
          if (err.status === 401) {
            this.authService.logout();
          }
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

