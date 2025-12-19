import { Component, OnInit } from '@angular/core';
import { Router } from '@angular/router';
import { ApiService } from '../../services/api.service';
import { AuthService } from '../../services/auth.service';

@Component({
  selector: 'app-usuarios',
  templateUrl: './usuarios.component.html',
  styleUrls: ['./usuarios.component.scss']
})
export class UsuariosComponent implements OnInit {
  usuarios: any[] = [];
  loading: boolean = false;
  error: string = '';
  mostrarFormulario: boolean = false;
  editandoUsuario: boolean = false;
  usuarioIdEditando: number | null = null;
  mostrarMenuUsuario: boolean = false;
  usuario: any = null;
  filtroRol: string = '';
  filtroActivo: string = '';
  mostrarCambiarPassword: boolean = false;
  nuevaPassword: string = '';

  usuarioForm: any = {
    nombre: '',
    email: '',
    rol: '',
    activo: true,
    password: ''
  };

  roles = [
    { value: 'admin_fincas', label: 'Admin Fincas', modulo: 'Fincas' },
    { value: 'propietario', label: 'Propietario', modulo: 'Fincas' },
    { value: 'proveedor', label: 'Proveedor', modulo: 'Fincas' },
    { value: 'admin_transportes', label: 'Admin Transportes', modulo: 'Transportes' },
    { value: 'conductor', label: 'Conductor', modulo: 'Transportes' },
    { value: 'super_admin', label: 'Super Admin', modulo: 'Sistema' }
  ];

  constructor(
    private apiService: ApiService,
    private authService: AuthService,
    private router: Router
  ) {}

  ngOnInit(): void {
    this.usuario = this.authService.getUsuario();
    
    // Solo super_admin puede acceder
    if (this.usuario?.rol !== 'super_admin') {
      this.router.navigate(['/modulos']);
      return;
    }
    
    this.cargarUsuarios();
  }

  cargarUsuarios(): void {
    this.loading = true;
    this.apiService.getUsuarios().subscribe({
      next: (data) => {
        this.usuarios = data;
        this.aplicarFiltros();
        this.loading = false;
      },
      error: (err) => {
        this.error = 'Error al cargar usuarios';
        this.loading = false;
      }
    });
  }

  aplicarFiltros(): void {
    // Los filtros se aplican en el template con *ngIf
  }

  mostrarForm(): void {
    this.mostrarFormulario = true;
    this.editandoUsuario = false;
    this.usuarioIdEditando = null;
    this.usuarioForm = {
      nombre: '',
      email: '',
      rol: '',
      activo: true,
      password: ''
    };
    this.error = '';
  }

  editarUsuario(usuario: any): void {
    this.mostrarFormulario = true;
    this.editandoUsuario = true;
    this.usuarioIdEditando = usuario.id;
    this.usuarioForm = {
      nombre: usuario.nombre,
      email: usuario.email,
      rol: usuario.rol,
      activo: usuario.activo,
      password: '' // No se muestra la contraseña
    };
    this.error = '';
  }

  cancelarForm(): void {
    this.mostrarFormulario = false;
    this.editandoUsuario = false;
    this.usuarioIdEditando = null;
    this.mostrarCambiarPassword = false;
    this.nuevaPassword = '';
    this.usuarioForm = {
      nombre: '',
      email: '',
      rol: '',
      activo: true,
      password: ''
    };
    this.error = '';
  }

  onSubmit(): void {
    if (!this.usuarioForm.nombre || !this.usuarioForm.email || !this.usuarioForm.rol) {
      this.error = 'Nombre, email y rol son obligatorios';
      return;
    }

    if (!this.editandoUsuario && !this.usuarioForm.password) {
      this.error = 'La contraseña es obligatoria al crear un usuario';
      return;
    }

    if (this.usuarioForm.password && this.usuarioForm.password.length < 6) {
      this.error = 'La contraseña debe tener al menos 6 caracteres';
      return;
    }

    this.loading = true;
    this.error = '';

    const data: any = {
      nombre: this.usuarioForm.nombre,
      email: this.usuarioForm.email,
      rol: this.usuarioForm.rol,
      activo: this.usuarioForm.activo
    };

    if (!this.editandoUsuario) {
      data.password = this.usuarioForm.password;
    }

    const obs = this.editandoUsuario && this.usuarioIdEditando
      ? this.apiService.actualizarUsuario(this.usuarioIdEditando, data)
      : this.apiService.crearUsuario(data);

    obs.subscribe({
      next: () => {
        this.loading = false;
        this.cancelarForm();
        this.cargarUsuarios();
      },
      error: (err) => {
        this.loading = false;
        this.error = err.error?.detail || 'Error al guardar usuario';
      }
    });
  }

  eliminarUsuario(usuario: any): void {
    if (confirm(`¿Eliminar usuario "${usuario.nombre}" (${usuario.email})?`)) {
      this.apiService.eliminarUsuario(usuario.id).subscribe({
        next: () => {
          this.cargarUsuarios();
        },
        error: (err) => {
          this.error = err.error?.detail || 'Error al eliminar usuario';
        }
      });
    }
  }

  abrirCambiarPassword(usuario: any): void {
    this.mostrarCambiarPassword = true;
    this.usuarioIdEditando = usuario.id;
    this.nuevaPassword = '';
    this.error = '';
  }

  cerrarCambiarPassword(): void {
    this.mostrarCambiarPassword = false;
    this.usuarioIdEditando = null;
    this.nuevaPassword = '';
  }

  cambiarPassword(): void {
    if (!this.nuevaPassword || this.nuevaPassword.length < 6) {
      this.error = 'La contraseña debe tener al menos 6 caracteres';
      return;
    }

    if (!this.usuarioIdEditando) return;

    this.loading = true;
    this.apiService.cambiarPasswordUsuario(this.usuarioIdEditando, this.nuevaPassword).subscribe({
      next: () => {
        this.loading = false;
        this.cerrarCambiarPassword();
        alert('Contraseña cambiada correctamente');
      },
      error: (err) => {
        this.loading = false;
        this.error = err.error?.detail || 'Error al cambiar contraseña';
      }
    });
  }

  getRolLabel(rol: string): string {
    const rolObj = this.roles.find(r => r.value === rol);
    return rolObj ? rolObj.label : rol;
  }

  getModuloLabel(rol: string): string {
    const rolObj = this.roles.find(r => r.value === rol);
    return rolObj ? rolObj.modulo : '';
  }

  getUsuariosFiltrados(): any[] {
    let filtrados = [...this.usuarios];
    
    if (this.filtroRol) {
      filtrados = filtrados.filter(u => u.rol === this.filtroRol);
    }
    
    if (this.filtroActivo !== '') {
      const activo = this.filtroActivo === 'true';
      filtrados = filtrados.filter(u => u.activo === activo);
    }
    
    return filtrados;
  }

  irAModulos(): void {
    this.router.navigate(['/modulos']);
  }

  logout(): void {
    this.authService.logout();
    this.router.navigate(['/login']);
  }
}

