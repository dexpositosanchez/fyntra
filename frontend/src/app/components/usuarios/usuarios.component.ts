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
  usuariosPorEstado: { [key: string]: any[] } = {};
  tabs: { estado: string, label: string, count: number }[] = [];
  tabActiva: string = '';
  loading: boolean = false;
  error: string = '';
  mostrarFormulario: boolean = false;
  editandoUsuario: boolean = false;
  usuarioIdEditando: number | null = null;
  mostrarMenuUsuario: boolean = false;
  usuario: any = null;
  filtroRol: string = '';

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
        this.organizarUsuariosPorEstado();
        this.loading = false;
      },
      error: (err) => {
        this.error = 'Error al cargar usuarios';
        this.loading = false;
      }
    });
  }

  organizarUsuariosPorEstado(): void {
    // Inicializar objetos
    this.usuariosPorEstado = {
      'activo': [],
      'inactivo': []
    };

    // Filtrar por rol si hay filtro
    let usuariosFiltrados = this.usuarios;
    if (this.filtroRol) {
      usuariosFiltrados = this.usuarios.filter(u => u.rol === this.filtroRol);
    }

    // Organizar por estado
    usuariosFiltrados.forEach(usuario => {
      const estado = usuario.activo ? 'activo' : 'inactivo';
      this.usuariosPorEstado[estado].push(usuario);
    });

    // Crear tabs
    this.tabs = [
      {
        estado: 'activo',
        label: 'Activos',
        count: this.usuariosPorEstado['activo'].length
      },
      {
        estado: 'inactivo',
        label: 'Inactivos',
        count: this.usuariosPorEstado['inactivo'].length
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

  getUsuariosTabActiva(): any[] {
    return this.usuariosPorEstado[this.tabActiva] || [];
  }

  aplicarFiltros(): void {
    this.organizarUsuariosPorEstado();
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

    // Validar contraseña solo si se proporciona (al crear o al cambiar)
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

    // Si estamos editando y se proporcionó una contraseña, actualizar primero el usuario
    // y luego cambiar la contraseña
    if (this.editandoUsuario && this.usuarioIdEditando) {
      const usuarioId = this.usuarioIdEditando; // Guardar en variable local para TypeScript
      this.apiService.actualizarUsuario(usuarioId, data).subscribe({
        next: () => {
          // Si se proporcionó una contraseña, cambiarla
          if (this.usuarioForm.password && this.usuarioForm.password.trim() !== '') {
            this.apiService.cambiarPasswordUsuario(usuarioId, this.usuarioForm.password).subscribe({
              next: () => {
                this.loading = false;
                this.cancelarForm();
                this.cargarUsuarios();
              },
              error: (err) => {
                this.loading = false;
                this.error = err.error?.detail || 'Error al cambiar contraseña';
              }
            });
          } else {
            // No se cambió la contraseña, solo actualizar datos
            this.loading = false;
            this.cancelarForm();
            this.cargarUsuarios();
          }
        },
        error: (err) => {
          this.loading = false;
          this.error = err.error?.detail || 'Error al guardar usuario';
        }
      });
    } else {
      // Crear nuevo usuario
      this.apiService.crearUsuario(data).subscribe({
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
  }

  toggleActivo(usuario: any, event: Event): void {
    event.stopPropagation();
    this.apiService.actualizarUsuario(usuario.id, { activo: !usuario.activo }).subscribe({
      next: () => this.cargarUsuarios(),
      error: (err) => this.error = err.error?.detail || 'Error al cambiar estado'
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


  getRolLabel(rol: string): string {
    const rolObj = this.roles.find(r => r.value === rol);
    return rolObj ? rolObj.label : rol;
  }

  getModuloLabel(rol: string): string {
    const rolObj = this.roles.find(r => r.value === rol);
    return rolObj ? rolObj.modulo : '';
  }


  irAModulos(): void {
    this.router.navigate(['/modulos']);
  }

  logout(): void {
    this.authService.logout();
    this.router.navigate(['/login']);
  }
}

