import { Component, OnInit } from '@angular/core';
import { Router } from '@angular/router';
import { ApiService } from '../../services/api.service';
import { AuthService } from '../../services/auth.service';

@Component({
  selector: 'app-proveedores',
  templateUrl: './proveedores.component.html',
  styleUrls: ['./proveedores.component.scss']
})
export class ProveedoresComponent implements OnInit {
  proveedores: any[] = [];
  proveedoresPorEstado: { [key: string]: any[] } = {};
  tabs: { estado: string, label: string, count: number }[] = [];
  tabActiva: string = '';
  loading: boolean = false;
  error: string = '';
  mostrarFormulario: boolean = false;
  editandoProveedor: boolean = false;
  proveedorIdEditando: number | null = null;
  mostrarMenuUsuario: boolean = false;
  usuario: any = null;
  filtroEspecialidad: string = '';

  proveedorForm: any = {
    nombre: '',
    email: '',
    telefono: '',
    especialidad: '',
    especialidadOtros: '',
    activo: true,
    password: '',
    crearUsuario: false
  };

  especialidades = [
    'Fontanería',
    'Electricidad',
    'Albañilería',
    'Pintura',
    'Carpintería',
    'Cerrajería',
    'Climatización',
    'Limpieza',
    'Jardinería',
    'Ascensores',
    'Otros'
  ];

  constructor(
    private apiService: ApiService,
    private authService: AuthService,
    private router: Router
  ) {}

  ngOnInit(): void {
    this.usuario = this.authService.getUsuario();
    this.cargarProveedores();
  }

  cargarProveedores(): void {
    this.loading = true;
    const params: any = {};
    if (this.filtroEspecialidad) {
      params.especialidad = this.filtroEspecialidad;
    }

    this.apiService.getProveedores(params).subscribe({
      next: (data) => {
        this.proveedores = data;
        this.organizarProveedoresPorEstado();
        this.loading = false;
      },
      error: (err) => {
        this.error = 'Error al cargar proveedores';
        this.loading = false;
      }
    });
  }

  organizarProveedoresPorEstado(): void {
    // Inicializar objetos
    this.proveedoresPorEstado = {
      'activo': [],
      'inactivo': []
    };

    // Filtrar por especialidad si hay filtro
    let proveedoresFiltrados = this.proveedores;
    if (this.filtroEspecialidad) {
      if (this.filtroEspecialidad === 'Otros') {
        // Si el filtro es "Otros", mostrar proveedores con especialidad personalizada (no en la lista fija)
        proveedoresFiltrados = this.proveedores.filter(p => 
          p.especialidad && 
          p.especialidad.trim().length > 0 && 
          !this.especialidades.includes(p.especialidad)
        );
      } else {
        // Para otras especialidades, buscar coincidencia exacta
        proveedoresFiltrados = this.proveedores.filter(p => 
          p.especialidad && p.especialidad === this.filtroEspecialidad
        );
      }
    }

    // Organizar por estado
    proveedoresFiltrados.forEach(proveedor => {
      const estado = proveedor.activo ? 'activo' : 'inactivo';
      this.proveedoresPorEstado[estado].push(proveedor);
    });

    // Crear tabs
    this.tabs = [
      {
        estado: 'activo',
        label: 'Activos',
        count: this.proveedoresPorEstado['activo'].length
      },
      {
        estado: 'inactivo',
        label: 'Inactivos',
        count: this.proveedoresPorEstado['inactivo'].length
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

  getProveedoresTabActiva(): any[] {
    return this.proveedoresPorEstado[this.tabActiva] || [];
  }

  aplicarFiltros(): void {
    this.organizarProveedoresPorEstado();
  }

  mostrarForm(): void {
    this.mostrarFormulario = true;
    this.editandoProveedor = false;
    this.proveedorIdEditando = null;
    this.proveedorForm = {
      nombre: '',
      email: '',
      telefono: '',
      especialidad: '',
      especialidadOtros: '',
      activo: true,
      password: '',
      crearUsuario: false
    };
  }

  editarProveedor(proveedor: any): void {
    this.mostrarFormulario = true;
    this.editandoProveedor = true;
    this.proveedorIdEditando = proveedor.id;
    // Si la especialidad no está en la lista fija, es "Otros" → mostrar en campo libre
    const esp = (proveedor.especialidad || '').trim();
    const esOtros = esp.length > 0 && !this.especialidades.includes(esp);
    this.proveedorForm = {
      nombre: proveedor.nombre,
      email: proveedor.email || '',
      telefono: proveedor.telefono || '',
      especialidad: esOtros ? 'Otros' : esp,
      especialidadOtros: esOtros ? esp : '',
      activo: proveedor.activo
    };
  }

  cancelarForm(): void {
    this.mostrarFormulario = false;
    this.editandoProveedor = false;
    this.proveedorIdEditando = null;
    this.error = '';
  }

  onSubmit(): void {
    this.loading = true;
    this.error = '';

    // Si especialidad es "Otros", guardar el texto libre (y mostrarlo en listado/edición)
    let especialidad = this.proveedorForm.especialidad || null;
    if (especialidad === 'Otros' && this.proveedorForm.especialidadOtros?.trim()) {
      especialidad = this.proveedorForm.especialidadOtros.trim();
    }

    const data: any = {
      nombre: this.proveedorForm.nombre,
      email: this.proveedorForm.email?.trim() || null,
      telefono: this.proveedorForm.telefono || null,
      especialidad,
      activo: this.proveedorForm.activo
    };

    // Crear usuario: obligatorio email + contraseña cuando crearUsuario está marcado
    if (this.proveedorForm.crearUsuario && !this.editandoProveedor) {
      if (!data.email) {
        this.error = 'El email es obligatorio para crear acceso al sistema.';
        this.loading = false;
        return;
      }
      if (!this.proveedorForm.password || !this.proveedorForm.password.trim()) {
        this.error = 'La contraseña es obligatoria para crear acceso al sistema.';
        this.loading = false;
        return;
      }
      data.password = this.proveedorForm.password;
    }

    if (this.editandoProveedor && this.proveedorIdEditando) {
      this.apiService.updateProveedor(this.proveedorIdEditando, data).subscribe({
        next: () => {
          this.loading = false;
          this.cancelarForm();
          this.cargarProveedores();
        },
        error: (err) => {
          this.loading = false;
          this.error = err.error?.detail || 'Error al actualizar proveedor';
        }
      });
    } else {
      this.apiService.createProveedor(data).subscribe({
        next: () => {
          this.loading = false;
          this.cancelarForm();
          this.cargarProveedores();
        },
        error: (err) => {
          this.loading = false;
          this.error = err.error?.detail || 'Error al crear proveedor';
        }
      });
    }
  }

  eliminarProveedor(proveedor: any, event: Event): void {
    event.stopPropagation();
    if (confirm(`¿Eliminar proveedor "${proveedor.nombre}"?`)) {
      this.apiService.deleteProveedor(proveedor.id).subscribe({
        next: () => this.cargarProveedores(),
        error: (err) => this.error = err.error?.detail || 'Error al eliminar'
      });
    }
  }

  toggleActivo(proveedor: any, event: Event): void {
    event.stopPropagation();
    this.apiService.updateProveedor(proveedor.id, { activo: !proveedor.activo }).subscribe({
      next: () => {
        this.cargarProveedores();
      },
      error: (err) => this.error = err.error?.detail || 'Error al cambiar estado'
    });
  }

  toggleMenuUsuario(): void {
    this.mostrarMenuUsuario = !this.mostrarMenuUsuario;
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


