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
  loading: boolean = false;
  error: string = '';
  mostrarFormulario: boolean = false;
  editandoProveedor: boolean = false;
  proveedorIdEditando: number | null = null;
  mostrarMenuUsuario: boolean = false;
  usuario: any = null;
  filtroEspecialidad: string = '';
  filtroActivo: string = '';

  proveedorForm: any = {
    nombre: '',
    email: '',
    telefono: '',
    especialidad: '',
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
    if (this.filtroActivo !== '') {
      params.activo = this.filtroActivo === 'true';
    }
    if (this.filtroEspecialidad) {
      params.especialidad = this.filtroEspecialidad;
    }

    this.apiService.getProveedores(params).subscribe({
      next: (data) => {
        this.proveedores = data;
        this.loading = false;
      },
      error: (err) => {
        this.error = 'Error al cargar proveedores';
        this.loading = false;
      }
    });
  }

  aplicarFiltros(): void {
    this.cargarProveedores();
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
      activo: true,
      password: '',
      crearUsuario: false
    };
  }

  editarProveedor(proveedor: any): void {
    this.mostrarFormulario = true;
    this.editandoProveedor = true;
    this.proveedorIdEditando = proveedor.id;
    this.proveedorForm = {
      nombre: proveedor.nombre,
      email: proveedor.email || '',
      telefono: proveedor.telefono || '',
      especialidad: proveedor.especialidad || '',
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

    const data: any = {
      nombre: this.proveedorForm.nombre,
      email: this.proveedorForm.email || null,
      telefono: this.proveedorForm.telefono || null,
      especialidad: this.proveedorForm.especialidad || null,
      activo: this.proveedorForm.activo
    };

    // Si se quiere crear usuario, añadir contraseña
    if (this.proveedorForm.crearUsuario && this.proveedorForm.password && !this.editandoProveedor) {
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
      next: () => this.cargarProveedores(),
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

  logout(): void {
    this.mostrarMenuUsuario = false;
    this.authService.logout();
  }
}


