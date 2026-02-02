import { Component, OnInit, OnDestroy } from '@angular/core';
import { Router, NavigationEnd } from '@angular/router';
import { Subscription } from 'rxjs';
import { filter } from 'rxjs/operators';
import { ApiService } from '../../services/api.service';
import { AuthService } from '../../services/auth.service';

@Component({
  selector: 'app-incidencias',
  templateUrl: './incidencias.component.html',
  styleUrls: ['./incidencias.component.scss']
})
export class IncidenciasComponent implements OnInit, OnDestroy {
  incidencias: any[] = [];
  inmuebles: any[] = [];
  proveedores: any[] = [];
  loading: boolean = false;
  error: string = '';
  filtroFecha: string = '';
  filtroPrioridad: string = '';
  textoBusqueda: string = '';
  incidenciasFiltradas: any[] = [];
  currentRoute: string = '';
  mostrarMenuUsuario: boolean = false;
  mostrarMenuNav: boolean = false;
  mostrarFormulario: boolean = false;
  editandoIncidencia: boolean = false;
  incidenciaIdEditando: number | null = null;
  incidenciaSeleccionada: any = null;
  mostrarHistorial: boolean = false;
  usuario: any = null;
  esPropietario: boolean = false;
  esProveedor: boolean = false;
  mostrarActuaciones: boolean = false;
  mostrarActuacionesModal: boolean = false;
  actuaciones: any[] = [];
  mostrarFormActuacion: boolean = false;
  actuacionForm: any = {
    descripcion: '',
    fecha: '',
    coste: null
  };
  // Documentos
  documentos: any[] = [];
  mostrarDocumentosModal: boolean = false;
  mostrarFormDocumento: boolean = false;
  documentoForm: any = { nombre: '' };
  archivoSeleccionado: File | null = null;
  mostrarVisorDocumento: boolean = false;
  documentoVisualizando: any = null;
  // Mensajes/Chat
  mensajes: any[] = [];
  mostrarChatModal: boolean = false;
  nuevoMensaje: string = '';
  cargandoMensajes: boolean = false;
  // Pestañas por estado
  incidenciasPorEstado: { [key: string]: any[] } = {};
  tabs: { estado: string, label: string, count: number }[] = [];
  tabActiva: string = '';
  exportandoDatos: boolean = false;
  eliminandoCuenta: boolean = false;
  private routerSubscription?: Subscription;

  incidenciaForm: any = {
    titulo: '',
    descripcion: '',
    prioridad: 'media',
    inmueble_id: '',
    estado: 'abierta',
    proveedor_id: null,
    comentario_cambio: ''
  };

  estados = [
    { value: 'abierta', label: 'Abierta' },
    { value: 'asignada', label: 'Asignada' },
    { value: 'en_progreso', label: 'En Progreso' },
    { value: 'resuelta', label: 'Resuelta' },
    { value: 'cerrada', label: 'Cerrada' }
  ];

  prioridades = [
    { value: 'baja', label: 'Baja' },
    { value: 'media', label: 'Media' },
    { value: 'alta', label: 'Alta' },
    { value: 'urgente', label: 'Urgente' }
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
    this.esProveedor = this.usuario?.rol === 'proveedor';
    
    if (!this.esProveedor) {
      this.cargarInmuebles();
    }
    // Cargar proveedores para admin y propietarios (propietarios necesitan ver el proveedor asignado)
    if (!this.esProveedor) {
      this.cargarProveedores();
    }
    this.actualizarVista();
    
    // Suscribirse a cambios de ruta
    this.routerSubscription = this.router.events
      .pipe(filter(event => event instanceof NavigationEnd))
      .subscribe((event: any) => {
        this.currentRoute = event.url;
        this.actualizarVista();
      });
  }

  cargarInmuebles(): void {
    this.apiService.getInmuebles().subscribe({
      next: (data) => this.inmuebles = data,
      error: () => this.inmuebles = []
    });
  }

  cargarProveedores(): void {
    this.apiService.getProveedores().subscribe({
      next: (data) => this.proveedores = data,
      error: () => this.proveedores = []
    });
  }

  actualizarVista(): void {
    // Solo cargar incidencias si estamos en la ruta de incidencias
    if (this.currentRoute.includes('/incidencias') && this.incidencias.length === 0) {
      this.cargarIncidencias();
    }
  }

  ngOnDestroy(): void {
    if (this.routerSubscription) {
      this.routerSubscription.unsubscribe();
    }
  }

  cargarIncidencias(): void {
    this.loading = true;
    
    // Proveedores usan endpoint diferente
    // Admin y superadmin ven todas las incidencias (incluidas cerradas)
    // Propietarios ven todas sus incidencias (incluidas cerradas) para conocer el motivo
    let observable;
    if (this.esProveedor) {
      observable = this.apiService.getMisIncidencias();
    } else if (this.usuario?.rol === 'super_admin' || this.usuario?.rol === 'admin_fincas') {
      // Admin y superadmin ven todas las incidencias
      observable = this.apiService.getIncidencias();
    } else {
      // Propietarios ven todas sus incidencias (incluidas cerradas)
      observable = this.apiService.getIncidencias();
    }
    
    observable.subscribe({
      next: (data) => {
        this.incidencias = data;
        this.aplicarFiltroTexto();
        this.loading = false;
      },
      error: (err) => {
        this.error = 'Error al cargar incidencias';
        this.loading = false;
        this.incidencias = [];
      }
    });
  }

  aplicarFiltroTexto(): void {
    // Aplicar filtro de búsqueda de texto sobre las incidencias cargadas
    if (!this.textoBusqueda || this.textoBusqueda.trim() === '') {
      this.incidenciasFiltradas = [...this.incidencias];
    } else {
      const busqueda = this.textoBusqueda.toLowerCase().trim();
      this.incidenciasFiltradas = this.incidencias.filter(incidencia => {
        const titulo = (incidencia.titulo || '').toLowerCase();
        const referencia = (incidencia.inmueble?.referencia || '').toLowerCase();
        
        // Extraer nombre del proveedor de forma segura - el proveedor viene como objeto con nombre
        let proveedorNombre = '';
        if (incidencia.proveedor) {
          // Verificar si es un objeto con propiedad nombre
          if (incidencia.proveedor && typeof incidencia.proveedor === 'object' && incidencia.proveedor.nombre) {
            proveedorNombre = String(incidencia.proveedor.nombre || '').toLowerCase();
          }
          // Si es un string directamente (caso poco probable pero por si acaso)
          else if (typeof incidencia.proveedor === 'string') {
            proveedorNombre = incidencia.proveedor.toLowerCase();
          }
        }
        
        // Buscar en título, referencia o nombre del proveedor
        const coincideTitulo = titulo.includes(busqueda);
        const coincideReferencia = referencia.includes(busqueda);
        const coincideProveedor = proveedorNombre && proveedorNombre.includes(busqueda);
        
        return coincideTitulo || coincideReferencia || coincideProveedor;
      });
    }
    
    // Organizar las incidencias filtradas por estado
    this.agruparPorEstado();
  }

  limpiarBusqueda(): void {
    this.textoBusqueda = '';
    this.aplicarFiltroTexto();
  }

  limpiarTodosFiltros(): void {
    this.filtroPrioridad = '';
    this.textoBusqueda = '';
    this.aplicarFiltroTexto();
  }

  aplicarFiltros(): void {
    // Si solo hay búsqueda de texto, aplicar filtro local
    this.aplicarFiltroTexto();
  }

  agruparPorEstado(): void {
    // Inicializar objeto de agrupación
    this.incidenciasPorEstado = {};
    
    // Filtrar por prioridad si hay filtro (sobre las incidencias ya filtradas por texto)
    let incidenciasParaOrganizar = this.incidenciasFiltradas;
    if (this.filtroPrioridad) {
      incidenciasParaOrganizar = this.incidenciasFiltradas.filter(incidencia => 
        incidencia.prioridad === this.filtroPrioridad
      );
    }
    
    // Agrupar incidencias por estado
    incidenciasParaOrganizar.forEach(incidencia => {
      // Asegurar que el estado sea un string (puede venir como enum del backend)
      const estado = (typeof incidencia.estado === 'string' ? incidencia.estado : incidencia.estado?.value || incidencia.estado) || 'abierta';
      if (!this.incidenciasPorEstado[estado]) {
        this.incidenciasPorEstado[estado] = [];
      }
      this.incidenciasPorEstado[estado].push(incidencia);
    });

    // Crear array de tabs con contadores, excluyendo estados con 0 items
    this.tabs = this.estados
      .map(estado => ({
        estado: estado.value,
        label: estado.label,
        count: this.incidenciasPorEstado[estado.value]?.length || 0
      }))
      .filter(tab => tab.count > 0)
      .sort((a, b) => {
        // Ordenar: primero "abierta" o similar, al final "cerrada" o similar
        const ordenEstados: { [key: string]: number } = {
          'abierta': 1,
          'asignada': 2,
          'en_progreso': 3,
          'resuelta': 4,
          'cerrada': 99
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

  getIncidenciasTabActiva(): any[] {
    return this.incidenciasPorEstado[this.tabActiva] || [];
  }

  getPrioridadClass(prioridad: string): string {
    const clases: { [key: string]: string } = {
      'urgente': 'prioridad-urgente',
      'alta': 'prioridad-alta',
      'media': 'prioridad-media',
      'baja': 'prioridad-baja'
    };
    return clases[prioridad?.toLowerCase()] || 'prioridad-media';
  }
  
  getPrioridadTexto(prioridad: string): string {
    const textos: { [key: string]: string } = {
      'urgente': 'Urgente',
      'alta': 'Alta',
      'media': 'Media',
      'baja': 'Baja'
    };
    return textos[prioridad?.toLowerCase()] || prioridad || 'Media';
  }

  mostrarForm(): void {
    this.mostrarFormulario = true;
    this.editandoIncidencia = false;
    this.incidenciaIdEditando = null;
    this.incidenciaForm = {
      titulo: '',
      descripcion: '',
      prioridad: 'media',
      inmueble_id: this.inmuebles.length === 1 ? this.inmuebles[0].id : '',
      estado: 'abierta',
      proveedor_id: null,
      comentario_cambio: ''
    };
  }

  editarIncidencia(incidencia: any): void {
    this.mostrarFormulario = true;
    this.editandoIncidencia = true;
    this.incidenciaIdEditando = incidencia.id;
    this.incidenciaForm = {
      titulo: incidencia.titulo,
      descripcion: incidencia.descripcion || '',
      prioridad: incidencia.prioridad,
      inmueble_id: incidencia.inmueble_id,
      estado: incidencia.estado,
      proveedor_id: incidencia.proveedor_id,
      comentario_cambio: '',
      version: incidencia.version
    };
  }

  cancelarForm(): void {
    this.mostrarFormulario = false;
    this.editandoIncidencia = false;
    this.incidenciaIdEditando = null;
    this.error = '';
  }

  onSubmit(): void {
    this.loading = true;
    this.error = '';

    if (this.editandoIncidencia && this.incidenciaIdEditando) {
      const updateData: any = {
        titulo: this.incidenciaForm.titulo,
        descripcion: this.incidenciaForm.descripcion,
        prioridad: this.incidenciaForm.prioridad,
        estado: this.incidenciaForm.estado,
        proveedor_id: this.incidenciaForm.proveedor_id || null,
        version: this.incidenciaForm.version,
        comentario_cambio: this.incidenciaForm.comentario_cambio || null
      };

      this.apiService.updateIncidencia(this.incidenciaIdEditando, updateData).subscribe({
        next: () => {
          this.loading = false;
          this.cancelarForm();
          this.cargarIncidencias();
        },
        error: (err) => {
          this.loading = false;
          this.error = err.error?.detail || 'Error al actualizar incidencia';
        }
      });
    } else {
      const createData = {
        titulo: this.incidenciaForm.titulo,
        descripcion: this.incidenciaForm.descripcion,
        prioridad: this.incidenciaForm.prioridad,
        inmueble_id: parseInt(this.incidenciaForm.inmueble_id)
      };

      this.apiService.createIncidencia(createData).subscribe({
        next: () => {
          this.loading = false;
          this.cancelarForm();
          this.cargarIncidencias();
        },
        error: (err) => {
          this.loading = false;
          this.error = err.error?.detail || 'Error al crear incidencia';
        }
      });
    }
  }

  puedeEliminarIncidencia(incidencia: any): boolean {
    // Admin siempre puede eliminar
    if (!this.esPropietario && !this.esProveedor) {
      return true;
    }
    // Propietario solo puede eliminar si es el creador
    if (this.esPropietario && this.usuario && incidencia.creador_usuario_id === this.usuario.id) {
      return true;
    }
    return false;
  }

  eliminarIncidencia(incidencia: any, event: Event): void {
    event.stopPropagation();
    if (confirm(`¿Eliminar incidencia "${incidencia.titulo}"?`)) {
      this.loading = true;
      this.apiService.deleteIncidencia(incidencia.id).subscribe({
        next: () => {
          this.loading = false;
          this.cargarIncidencias();
        },
        error: (err) => {
          this.loading = false;
          this.error = err.error?.detail || 'Error al eliminar';
        }
      });
    }
  }

  verHistorial(incidencia: any, event: Event): void {
    event.stopPropagation();
    this.incidenciaSeleccionada = incidencia;
    this.mostrarHistorial = true;
  }

  cerrarHistorial(): void {
    this.mostrarHistorial = false;
    this.incidenciaSeleccionada = null;
  }

  getEstadoLabel(estado: string): string {
    const est = this.estados.find(e => e.value === estado);
    return est ? est.label : estado;
  }

  getEstadoClass(estado: string): string {
    return 'estado-' + estado.replace('_', '-');
  }

  getInmuebleNombre(inmuebleId: number): string {
    const inmueble = this.inmuebles.find(i => i.id === inmuebleId);
    return inmueble ? `${inmueble.referencia} - ${inmueble.direccion || ''}` : 'N/A';
  }

  getProveedorNombre(incidencia: any): string | null {
    // Verificar si hay proveedor asignado
    if (!incidencia.proveedor) {
      return null;
    }
    
    // Si es un objeto con nombre
    if (typeof incidencia.proveedor === 'object' && incidencia.proveedor.nombre) {
      return incidencia.proveedor.nombre;
    }
    
    // Si es un string directamente
    if (typeof incidencia.proveedor === 'string') {
      return incidencia.proveedor;
    }
    
    return null;
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

  estaEnModuloTransportes(): boolean {
    return this.currentRoute.includes('/vehiculos') || 
           this.currentRoute.includes('/conductores') || 
           this.currentRoute.includes('/rutas') || 
           this.currentRoute.includes('/pedidos');
  }

  puedeCambiarModulo(): boolean {
    if (this.esPropietario || this.esProveedor) return false;
    const r = this.usuario?.rol;
    return r === 'super_admin' || r === 'admin_fincas' || r === 'admin_transportes';
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

  /** RGPD Art. 15 y 20: exportar datos personales */
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

  /** RGPD Art. 17: eliminar mi cuenta */
  eliminarMiCuenta(): void {
    if (!confirm('¿Está seguro de que desea eliminar su cuenta? Se anonimizarán sus datos y no podrá volver a iniciar sesión. Esta acción no se puede deshacer.')) return;
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

  // Métodos para proveedores y actuaciones
  verActuaciones(incidencia: any, event?: Event): void {
    if (event) event.stopPropagation();
    this.incidenciaSeleccionada = incidencia;
    
    if (this.esProveedor) {
      // Proveedores: vista completa de gestión
      this.mostrarActuaciones = true;
    } else {
      // Admin/Propietario: modal de solo lectura
      this.mostrarActuacionesModal = true;
    }
    this.cargarActuaciones(incidencia.id);
  }

  cargarActuaciones(incidenciaId: number): void {
    this.apiService.getActuacionesIncidencia(incidenciaId).subscribe({
      next: (data) => {
        // Ordenar actuaciones por fecha descendente (más reciente primero)
        this.actuaciones = data.sort((a: any, b: any) => {
          const fechaA = new Date(a.fecha).getTime();
          const fechaB = new Date(b.fecha).getTime();
          return fechaB - fechaA; // Orden descendente
        });
      },
      error: () => this.actuaciones = []
    });
  }

  cerrarActuaciones(): void {
    this.mostrarActuaciones = false;
    this.mostrarActuacionesModal = false;
    this.incidenciaSeleccionada = null;
    this.actuaciones = [];
    this.mostrarFormActuacion = false;
  }

  mostrarFormularioActuacion(): void {
    this.mostrarFormActuacion = true;
    this.actuacionForm = {
      descripcion: '',
      fecha: new Date().toISOString().split('T')[0],
      coste: null
    };
  }

  cancelarFormActuacion(): void {
    this.mostrarFormActuacion = false;
  }

  guardarActuacion(): void {
    if (!this.incidenciaSeleccionada) return;
    
    const data = {
      incidencia_id: this.incidenciaSeleccionada.id,
      descripcion: this.actuacionForm.descripcion,
      fecha: new Date(this.actuacionForm.fecha).toISOString(),
      coste: this.actuacionForm.coste || null
    };

    this.apiService.createActuacion(data).subscribe({
      next: () => {
        this.cargarActuaciones(this.incidenciaSeleccionada.id);
        this.cancelarFormActuacion();
        this.cargarIncidencias(); // Actualizar lista
      },
      error: (err) => this.error = err.error?.detail || 'Error al crear actuación'
    });
  }

  cambiarEstadoProveedor(nuevoEstado: string): void {
    if (!this.incidenciaSeleccionada) return;
    
    this.apiService.cambiarEstadoIncidenciaProveedor(
      this.incidenciaSeleccionada.id, 
      nuevoEstado
    ).subscribe({
      next: () => {
        this.incidenciaSeleccionada.estado = nuevoEstado;
        this.cargarIncidencias();
      },
      error: (err) => this.error = err.error?.detail || 'Error al cambiar estado'
    });
  }

  estadosProveedor = [
    { value: 'en_progreso', label: 'En Progreso' },
    { value: 'resuelta', label: 'Resuelta' }
  ];

  eliminarActuacion(actuacion: any, event: Event): void {
    event.stopPropagation();
    if (confirm('¿Eliminar esta actuación?')) {
      this.apiService.deleteActuacion(actuacion.id).subscribe({
        next: () => this.cargarActuaciones(this.incidenciaSeleccionada.id),
        error: (err) => this.error = err.error?.detail || 'Error al eliminar'
      });
    }
  }

  // Métodos para documentos
  verDocumentos(incidencia: any, event: Event): void {
    event.stopPropagation();
    this.incidenciaSeleccionada = incidencia;
    this.mostrarDocumentosModal = true;
    this.cargarDocumentos(incidencia.id);
  }

  cargarDocumentos(incidenciaId: number): void {
    this.apiService.getDocumentosIncidencia(incidenciaId).subscribe({
      next: (data) => this.documentos = data,
      error: () => this.documentos = []
    });
  }

  cerrarDocumentos(): void {
    this.mostrarDocumentosModal = false;
    this.mostrarFormDocumento = false;
    this.documentos = [];
    this.archivoSeleccionado = null;
  }

  mostrarFormularioDocumento(): void {
    this.mostrarFormDocumento = true;
    this.documentoForm = { nombre: '' };
    this.archivoSeleccionado = null;
  }

  cancelarFormDocumento(): void {
    this.mostrarFormDocumento = false;
    this.archivoSeleccionado = null;
  }

  onArchivoSeleccionado(event: any): void {
    const file = event.target.files[0];
    if (file) {
      this.archivoSeleccionado = file;
      if (!this.documentoForm.nombre) {
        this.documentoForm.nombre = file.name.split('.')[0];
      }
    }
  }

  subirDocumento(): void {
    if (!this.incidenciaSeleccionada || !this.archivoSeleccionado) return;

    this.loading = true;
    this.apiService.subirDocumento(
      this.incidenciaSeleccionada.id,
      this.documentoForm.nombre,
      this.archivoSeleccionado
    ).subscribe({
      next: () => {
        this.loading = false;
        this.cancelarFormDocumento();
        this.cargarDocumentos(this.incidenciaSeleccionada.id);
        this.cargarIncidencias(); // Actualizar contador
      },
      error: (err) => {
        this.loading = false;
        this.error = err.error?.detail || 'Error al subir documento';
      }
    });
  }

  verDocumento(documento: any): void {
    const url = this.apiService.getUrlDocumento(documento.id);
    const token = localStorage.getItem('access_token');
    const fullUrl = url + '?token=' + token;
    
    // Para imágenes, mostrar en modal
    if (documento.tipo_archivo?.startsWith('image/')) {
      this.documentoVisualizando = { ...documento, url: fullUrl };
      this.mostrarVisorDocumento = true;
    } else {
      // Para PDFs y otros archivos, abrir en nueva pestaña
      window.open(fullUrl, '_blank');
    }
  }

  cerrarVisor(): void {
    this.mostrarVisorDocumento = false;
    this.documentoVisualizando = null;
  }

  eliminarDocumento(documento: any, event: Event): void {
    event.stopPropagation();
    if (confirm(`¿Eliminar documento "${documento.nombre}"?`)) {
      this.apiService.eliminarDocumento(documento.id).subscribe({
        next: () => {
          this.cargarDocumentos(this.incidenciaSeleccionada.id);
          this.cargarIncidencias();
        },
        error: (err) => this.error = err.error?.detail || 'Error al eliminar'
      });
    }
  }

  formatearTamano(bytes: number): string {
    if (!bytes) return '';
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
  }

  esImagenOPdf(tipo: string): boolean {
    return tipo?.startsWith('image/') || tipo === 'application/pdf';
  }

  puedeEliminarDocumento(documento: any): boolean {
    return documento.usuario_id === this.usuario?.id || this.usuario?.rol === 'super_admin';
  }

  // ========== CHAT / MENSAJES ==========
  abrirChat(incidencia: any, event: Event): void {
    event.stopPropagation();
    this.incidenciaSeleccionada = incidencia;
    this.mostrarChatModal = true;
    this.cargarMensajes(incidencia.id);
  }

  cerrarChat(): void {
    this.mostrarChatModal = false;
    this.mensajes = [];
    this.nuevoMensaje = '';
  }

  cargarMensajes(incidenciaId: number): void {
    this.cargandoMensajes = true;
    this.apiService.getMensajesIncidencia(incidenciaId).subscribe({
      next: (data) => {
        this.mensajes = data;
        this.cargandoMensajes = false;
        setTimeout(() => this.scrollChatAlFinal(), 100);
      },
      error: (err) => {
        this.error = err.error?.detail || 'Error al cargar mensajes';
        this.cargandoMensajes = false;
      }
    });
  }

  enviarMensaje(): void {
    if (!this.nuevoMensaje.trim() || !this.incidenciaSeleccionada) return;
    
    this.apiService.enviarMensaje(this.incidenciaSeleccionada.id, this.nuevoMensaje.trim()).subscribe({
      next: (mensaje) => {
        this.mensajes.push(mensaje);
        this.nuevoMensaje = '';
        setTimeout(() => this.scrollChatAlFinal(), 100);
      },
      error: (err) => this.error = err.error?.detail || 'Error al enviar mensaje'
    });
  }

  eliminarMensaje(mensaje: any): void {
    if (confirm('¿Eliminar este mensaje?')) {
      this.apiService.eliminarMensaje(mensaje.id).subscribe({
        next: () => {
          this.mensajes = this.mensajes.filter(m => m.id !== mensaje.id);
        },
        error: (err) => this.error = err.error?.detail || 'Error al eliminar mensaje'
      });
    }
  }

  puedeEliminarMensaje(mensaje: any): boolean {
    // Solo el autor puede eliminar y solo si es el último mensaje
    if (mensaje.usuario_id !== this.usuario?.id) return false;
    if (this.mensajes.length === 0) return false;
    const ultimoMensaje = this.mensajes[this.mensajes.length - 1];
    return ultimoMensaje.id === mensaje.id;
  }

  scrollChatAlFinal(): void {
    const chatBody = document.querySelector('.chat-messages');
    if (chatBody) {
      chatBody.scrollTop = chatBody.scrollHeight;
    }
  }

  getRolLabel(rol: string): string {
    const roles: {[key: string]: string} = {
      'super_admin': 'Admin',
      'admin_fincas': 'Admin Fincas',
      'propietario': 'Propietario',
      'proveedor': 'Proveedor'
    };
    return roles[rol] || rol;
  }

  esMiMensaje(mensaje: any): boolean {
    return mensaje.usuario_id === this.usuario?.id;
  }
}
