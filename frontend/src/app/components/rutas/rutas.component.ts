import { Component, OnInit, OnDestroy } from '@angular/core';
import { Router, NavigationEnd } from '@angular/router';
import { Subscription } from 'rxjs';
import { filter } from 'rxjs/operators';
import { ApiService } from '../../services/api.service';
import { AuthService } from '../../services/auth.service';
import { HttpErrorResponse } from '@angular/common/http';
import { ChangeDetectorRef } from '@angular/core';

@Component({
  selector: 'app-rutas',
  templateUrl: './rutas.component.html',
  styleUrls: ['./rutas.component.scss']
})
export class RutasComponent implements OnInit, OnDestroy {
  rutas: any[] = [];
  pedidos: any[] = [];
  conductores: any[] = [];
  vehiculos: any[] = [];
  mostrarFormulario: boolean = false;
  editandoRuta: boolean = false;
  rutaIdEditando: number | null = null;
  rutaActual: any = null; // Ruta actualmente siendo editada/visualizada
  rutaForm: any = {
    fecha: '',
    conductor_id: null,
    vehiculo_id: null,
    observaciones: '',
    pedidos_ids: []
  };
  paradasPreview: any[] = [];
  paradasExistentes: Map<number, any> = new Map(); // Mapeo de parada_id -> parada para rutas existentes
  pedidosDisponibles: any[] = [];
  pedidosSeleccionados: any[] = [];
  pedidoSeleccionado: number | null = null;
  mostrarFechasPedido: boolean = false;
  fechaHoraCarga: string = '';
  fechaHoraDescarga: string = '';
  pedidosConFechas: Map<number, { fechaCarga: string, fechaDescarga: string }> = new Map();
  loading: boolean = false;
  error: string = '';
  currentRoute: string = '';
  mostrarMenuUsuario: boolean = false;
  usuario: any = null;
  // Filtros
  filtroConductor: number | string | null = null;
  filtroVehiculo: number | string | null = null;
  filtroSoloConIncidencias: boolean = false;
  rutasFiltradas: any[] = [];
  // Pestañas por estado
  rutasPorEstado: { [key: string]: any[] } = {};
  tabs: { estado: string, label: string, count: number }[] = [];
  tabActiva: string = '';
  private routerSubscription?: Subscription;
  
  estados = [
    { value: 'planificada', label: 'Planificada' },
    { value: 'en_curso', label: 'En Progreso' },
    { value: 'completada', label: 'Completada' },
    { value: 'cancelada', label: 'Cancelada' }
  ];

  constructor(
    private apiService: ApiService,
    private authService: AuthService,
    private router: Router,
    private cdr: ChangeDetectorRef
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
    if (!this.currentRoute.includes('/rutas')) {
      this.mostrarFormulario = false;
    }
    
    if (this.currentRoute.includes('/rutas')) {
      this.cargarRutas();
      this.cargarPedidos(); // Recargar pedidos para asegurar datos actualizados
      this.cargarConductores();
      this.cargarVehiculos();
    }
  }

  ngOnDestroy(): void {
    if (this.routerSubscription) {
      this.routerSubscription.unsubscribe();
    }
  }

  cargarRutas(): void {
    this.loading = true;
    const params: any = {};
    if (this.filtroSoloConIncidencias) {
      params.solo_con_incidencias = true;
    }
    this.apiService.getRutas(params).subscribe({
      next: (data) => {
        this.rutas = data;
        this.aplicarFiltros();
        this.loading = false;
      },
      error: (err: HttpErrorResponse) => {
        this.error = err.error?.detail || 'Error al cargar rutas';
        this.loading = false;
        if (err.status === 401) {
          this.authService.logout();
        }
      }
    });
  }

  aplicarFiltros(): void {
    // Aplicar todos los filtros
    let resultados = [...this.rutas];
    
    // Filtro por conductor
    if (this.filtroConductor !== null && this.filtroConductor !== undefined && this.filtroConductor !== '') {
      const conductorId = typeof this.filtroConductor === 'string' ? parseInt(this.filtroConductor, 10) : this.filtroConductor;
      if (!isNaN(conductorId)) {
        resultados = resultados.filter(ruta => {
          return ruta.conductor_id === conductorId;
        });
      }
    }
    
    // Filtro por vehículo
    if (this.filtroVehiculo !== null && this.filtroVehiculo !== undefined && this.filtroVehiculo !== '') {
      const vehiculoId = typeof this.filtroVehiculo === 'string' ? parseInt(this.filtroVehiculo, 10) : this.filtroVehiculo;
      if (!isNaN(vehiculoId)) {
        resultados = resultados.filter(ruta => {
          return ruta.vehiculo_id === vehiculoId;
        });
      }
    }
    
    // Filtro solo rutas con incidencias
    if (this.filtroSoloConIncidencias) {
      resultados = resultados.filter(ruta => {
        return ruta.tiene_incidencias === true || (ruta.incidencias_count && ruta.incidencias_count > 0);
      });
    }
    
    this.rutasFiltradas = resultados;
    this.agruparPorEstado();
  }

  limpiarTodosFiltros(): void {
    this.filtroConductor = null;
    this.filtroVehiculo = null;
    this.aplicarFiltros();
  }

  agruparPorEstado(): void {
    // Inicializar objeto de agrupación
    this.rutasPorEstado = {};
    
    // Agrupar rutas filtradas por estado
    this.rutasFiltradas.forEach(ruta => {
      const estado = ruta.estado || 'planificada';
      if (!this.rutasPorEstado[estado]) {
        this.rutasPorEstado[estado] = [];
      }
      this.rutasPorEstado[estado].push(ruta);
    });

    // Crear array de tabs con contadores, excluyendo estados con 0 items
    this.tabs = this.estados
      .map(estado => ({
        estado: estado.value,
        label: estado.label,
        count: this.rutasPorEstado[estado.value]?.length || 0
      }))
      .filter(tab => tab.count > 0)
      .sort((a, b) => {
        // Ordenar: primero "planificada" o similar, al final "cancelada" o similar
        const ordenEstados: { [key: string]: number } = {
          'planificada': 1,
          'en_curso': 2,
          'completada': 3,
          'cancelada': 99
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

  getRutasTabActiva(): any[] {
    return this.rutasPorEstado[this.tabActiva] || [];
  }

  eliminarRuta(rutaId: number, event: Event): void {
    event.stopPropagation(); // Evitar que se active el click en la tarjeta
    if (!confirm('¿Estás seguro de que deseas eliminar esta ruta? Los pedidos volverán a estado pendiente.')) {
      return;
    }
    
    this.loading = true;
    this.apiService.deleteRuta(rutaId).subscribe({
      next: () => {
        this.cargarRutas();
        this.cargarPedidos(); // Recargar pedidos para actualizar disponibilidad
        this.loading = false;
        this.error = '';
      },
      error: (err: HttpErrorResponse) => {
        this.error = err.error?.detail || 'Error al eliminar ruta';
        this.loading = false;
        if (err.status === 401) {
          this.authService.logout();
        }
      }
    });
  }

  cargarPedidos(): void {
    // Forzar recarga sin caché para asegurar datos actualizados
    this.apiService.getPedidos({ estado: 'pendiente', no_cache: true }).subscribe({
      next: (data) => {
        this.pedidosDisponibles = data || [];
      },
      error: (err: HttpErrorResponse) => {
        this.pedidosDisponibles = [];
      }
    });
  }

  cargarConductores(): void {
    this.apiService.getConductores({ activo: true }).subscribe({
      next: (data) => {
        // Filtrar conductores con licencia válida (no caducada)
        const hoy = new Date();
        hoy.setHours(0, 0, 0, 0);
        this.conductores = data.filter((conductor: any) => {
          if (!conductor.fecha_caducidad_licencia) return false;
          const fechaCaducidad = new Date(conductor.fecha_caducidad_licencia);
          fechaCaducidad.setHours(0, 0, 0, 0);
          return fechaCaducidad >= hoy;
        });
      },
      error: (err: HttpErrorResponse) => {
        // Error silencioso
      }
    });
  }

  cargarVehiculos(): void {
    this.apiService.getVehiculos({ estado: 'activo' }).subscribe({
      next: (data) => {
        this.vehiculos = data || [];
      },
      error: (err: HttpErrorResponse) => {
        this.vehiculos = [];
      }
    });
  }

  mostrarForm(): void {
    this.editandoRuta = false;
    this.rutaIdEditando = null;
    this.rutaActual = null;
    this.mostrarFormulario = true;
    this.rutaForm = {
      fecha: '',
      fecha_inicio: '',
      fecha_fin: '',
      conductor_id: null,
      vehiculo_id: null,
      observaciones: '',
      pedidos_ids: []
    };
    this.pedidosSeleccionados = [];
    this.paradasPreview = [];
    this.paradasExistentes.clear();
  }

  editarRuta(ruta: any): void {
    this.editandoRuta = true;
    this.rutaIdEditando = ruta.id;
    this.mostrarFormulario = true;
    
    // Si la ruta está en progreso, cargar los datos completos desde el servidor
    if (ruta.estado === 'en_curso') {
      this.apiService.getRuta(ruta.id).subscribe({
        next: (rutaCompleta) => {
          this.rutaActual = rutaCompleta;
          this.cargarDatosRuta(rutaCompleta);
        },
        error: (err) => {
          this.error = 'Error al cargar los datos de la ruta';
          this.rutaActual = ruta; // Usar los datos básicos como fallback
          this.cargarDatosRuta(ruta);
        }
      });
    } else {
      this.rutaActual = ruta;
      this.cargarDatosRuta(ruta);
    }
  }

  cargarDatosRuta(ruta: any): void {
    // Formatear fecha_inicio y fecha_fin para date (YYYY-MM-DD)
    // Las fechas vienen en formato "dd/mm/YYYY HH:MM" desde el backend
    let fechaInicioFormateada = '';
    if (ruta.fecha_inicio) {
      fechaInicioFormateada = this.parsearFechaParaInput(ruta.fecha_inicio);
    }
    
    let fechaFinFormateada = '';
    if (ruta.fecha_fin) {
      fechaFinFormateada = this.parsearFechaParaInput(ruta.fecha_fin);
    }
    
    // Extraer IDs únicos de pedidos de las paradas
    const pedidosIds = ruta.paradas ? [...new Set(ruta.paradas.map((p: any) => p.pedido_id))] : [];
    
    // Cargar pedidos completos desde el servidor para los pedidos de esta ruta
    // (pueden estar en estado EN_RUTA y no estar en pedidosDisponibles)
    const pedidosMap = new Map<number, any>();
    const pedidosIdsACargar: number[] = [];
    
    if (ruta.paradas) {
      for (const parada of ruta.paradas) {
        if (parada.pedido_id && !pedidosMap.has(parada.pedido_id)) {
          // Buscar el pedido en pedidosDisponibles primero
          let pedido = this.pedidosDisponibles.find(p => p.id === parada.pedido_id);
          if (pedido) {
            pedidosMap.set(parada.pedido_id, pedido);
          } else {
            // Si no está disponible, necesitamos cargarlo del servidor
            pedidosIdsACargar.push(parada.pedido_id);
          }
        }
      }
    }
    
    // Cargar pedidos que no están en pedidosDisponibles (están en EN_RUTA)
    if (pedidosIdsACargar.length > 0) {
      let pedidosCargados = 0;
      pedidosIdsACargar.forEach(pedidoId => {
        this.apiService.getPedido(pedidoId).subscribe({
          next: (data) => {
            pedidosMap.set(pedidoId, data);
            pedidosCargados++;
            // Actualizar la lista cuando se carguen todos
            if (pedidosCargados === pedidosIdsACargar.length) {
              this.pedidosSeleccionados = Array.from(pedidosMap.values());
              this.actualizarParadasPreview();
            }
          },
          error: (err) => {
            // Si falla, construir desde la parada como fallback
            const parada = ruta.paradas.find((p: any) => p.pedido_id === pedidoId);
            if (parada && parada.pedido) {
              const pedidoFallback = {
                id: parada.pedido_id,
                cliente: parada.pedido.cliente || 'Cliente desconocido',
                origen: parada.pedido.origen || parada.direccion,
                destino: parada.pedido.destino || parada.direccion,
                peso: parada.pedido.peso || 0,
                volumen: parada.pedido.volumen || 0,
                fecha_entrega_deseada: parada.pedido.fecha_entrega_deseada || null
              };
              pedidosMap.set(pedidoId, pedidoFallback);
            }
            pedidosCargados++;
            if (pedidosCargados === pedidosIdsACargar.length) {
              this.pedidosSeleccionados = Array.from(pedidosMap.values());
              this.actualizarParadasPreview();
            }
          }
        });
      });
    } else {
      // Si todos los pedidos ya están en pedidosDisponibles, establecer directamente
      this.pedidosSeleccionados = Array.from(pedidosMap.values());
    }
    
    // Almacenar mapeo de paradas existentes (parada_id -> parada)
    this.paradasExistentes.clear();
    if (ruta.paradas) {
      for (const parada of ruta.paradas) {
        this.paradasExistentes.set(parada.id, parada);
      }
    }
    
    // Recuperar fechas/horas de las paradas
    this.pedidosConFechas.clear();
    if (ruta.paradas) {
      const fechasPorPedido: Map<number, { fechaCarga: string, fechaDescarga: string }> = new Map();
      for (const parada of ruta.paradas) {
        if (!fechasPorPedido.has(parada.pedido_id)) {
          fechasPorPedido.set(parada.pedido_id, { fechaCarga: '', fechaDescarga: '' });
        }
        const fechas = fechasPorPedido.get(parada.pedido_id)!;
        if (parada.fecha_hora_llegada) {
          const fechaLocal = this.getFechaHoraLocal(parada.fecha_hora_llegada);
          if (parada.tipo_operacion === 'carga') {
            fechas.fechaCarga = fechaLocal;
          } else if (parada.tipo_operacion === 'descarga') {
            fechas.fechaDescarga = fechaLocal;
          }
        }
      }
      this.pedidosConFechas = fechasPorPedido;
    }
    
    this.rutaForm = {
      fecha_inicio: fechaInicioFormateada,
      fecha_fin: fechaFinFormateada,
      conductor_id: ruta.conductor_id || null,
      vehiculo_id: ruta.vehiculo_id || null,
      observaciones: ruta.observaciones || '',
      pedidos_ids: pedidosIds
    };
    this.mostrarFechasPedido = false;
    this.pedidoSeleccionado = null;
    this.actualizarParadasPreview();
  }

  cancelarForm(): void {
    this.mostrarFormulario = false;
    this.editandoRuta = false;
    this.rutaIdEditando = null;
    this.rutaActual = null;
    this.mostrarFechasPedido = false;
    this.pedidoSeleccionado = null;
    this.error = '';
  }

  agregarPedido(pedidoId: number): void {
    if (!this.rutaForm.pedidos_ids.includes(pedidoId)) {
      this.rutaForm.pedidos_ids.push(pedidoId);
      // Buscar el pedido en pedidosDisponibles antes de que se filtre
      const pedido = this.pedidosDisponibles.find(p => p.id === pedidoId);
      if (pedido) {
        // Añadir una copia del pedido para evitar problemas de referencia
        this.pedidosSeleccionados.push({...pedido});
      } else {
        // Si no se encuentra, obtenerlo del servidor (no debería pasar normalmente)
        this.apiService.getPedido(pedidoId).subscribe({
          next: (data) => {
            this.pedidosSeleccionados.push(data);
          },
          error: (err) => {
            // Error silencioso
          }
        });
      }
    }
  }

  eliminarPedido(pedidoId: number): void {
    this.rutaForm.pedidos_ids = this.rutaForm.pedidos_ids.filter((id: number) => id !== pedidoId);
    this.pedidosSeleccionados = this.pedidosSeleccionados.filter(p => p.id !== pedidoId);
    this.pedidosConFechas.delete(pedidoId);
    this.actualizarParadasPreview();
  }

  calcularPesoTotal(): number {
    return this.pedidosSeleccionados.reduce((total, pedido) => total + (pedido.peso || 0), 0);
  }

  getPedidosDisponibles(): any[] {
    // Filtrar pedidos que:
    // 1. No estén ya seleccionados en esta ruta
    // 2. Estén en estado 'pendiente' (los pedidos en 'en_ruta' no deben aparecer a menos que ya estén en esta ruta)
    return this.pedidosDisponibles.filter(p => 
      !this.rutaForm.pedidos_ids.includes(p.id) && 
      p.estado === 'pendiente'
    );
  }

  onAnadirPedido(): void {
    const pedidoId = this.pedidoSeleccionado ? Number(this.pedidoSeleccionado) : null;
    if (pedidoId && !this.rutaForm.pedidos_ids.includes(pedidoId)) {
      // Mostrar los campos de fecha/hora
      this.mostrarFechasPedido = true;
      this.fechaHoraCarga = '';
      this.fechaHoraDescarga = '';
    }
  }

  confirmarAnadirPedido(): void {
    const pedidoId = this.pedidoSeleccionado ? Number(this.pedidoSeleccionado) : null;
    if (pedidoId && !this.rutaForm.pedidos_ids.includes(pedidoId)) {
      // Validar fechas si ambas están definidas
      if (this.fechaHoraCarga && this.fechaHoraDescarga) {
        const fechaCarga = new Date(this.fechaHoraCarga);
        const fechaDescarga = new Date(this.fechaHoraDescarga);
        
        if (fechaDescarga < fechaCarga) {
          this.error = `La fecha de descarga no puede ser anterior a la fecha de carga para este pedido`;
          return;
        }
      }
      
      // Guardar las fechas si están definidas
      if (this.fechaHoraCarga || this.fechaHoraDescarga) {
        this.pedidosConFechas.set(pedidoId, {
          fechaCarga: this.fechaHoraCarga,
          fechaDescarga: this.fechaHoraDescarga
        });
      }
      this.agregarPedido(pedidoId);
      this.actualizarParadasPreview();
      // Limpiar el desplegable y ocultar los campos de fecha
      this.pedidoSeleccionado = null;
      this.mostrarFechasPedido = false;
      this.fechaHoraCarga = '';
      this.fechaHoraDescarga = '';
      this.error = ''; // Limpiar error si todo está bien
    }
  }

  cancelarAnadirPedido(): void {
    this.mostrarFechasPedido = false;
    this.pedidoSeleccionado = null;
    this.fechaHoraCarga = '';
    this.fechaHoraDescarga = '';
  }

  getVehiculoSeleccionado(): any {
    if (!this.rutaForm.vehiculo_id) {
      return null;
    }
    // Convertir ambos a número para comparar correctamente (el select devuelve string)
    const vehiculoId = Number(this.rutaForm.vehiculo_id);
    return this.vehiculos.find(v => Number(v.id) === vehiculoId);
  }

  getCapacidadVehiculo(): number {
    const vehiculo = this.getVehiculoSeleccionado();
    if (!vehiculo) {
      return 0;
    }
    // Asegurar que capacidad sea un número válido
    const capacidad = vehiculo.capacidad;
    if (capacidad === null || capacidad === undefined || isNaN(capacidad)) {
      return 0;
    }
    return Number(capacidad);
  }

  onVehiculoChange(): void {
    // Forzar actualización de la vista cuando cambia el vehículo
    this.cdr.detectChanges();
  }

  hayExcesoCapacidad(): boolean {
    return this.calcularPesoTotal() > this.getCapacidadVehiculo();
  }

  getPesoAcumuladoEnParada(index: number): number {
    if (!this.paradasPreview || this.paradasPreview.length === 0) {
      return 0;
    }
    
    // Obtener la parada actual por índice
    const paradaActual = this.paradasPreview[index];
    if (!paradaActual) {
      return 0;
    }
    
    // Ordenar paradas por orden para calcular correctamente el peso acumulado
    const paradasOrdenadas = [...this.paradasPreview].sort((a, b) => (a.orden || 0) - (b.orden || 0));
    const ordenActual = paradaActual.orden || 0;
    
    // Calcular peso acumulado hasta esta parada (incluyéndola)
    let pesoAcumulado = 0;
    
    for (const parada of paradasOrdenadas) {
      if (!parada || !parada.pedido_id) continue;
      
      // Solo considerar paradas hasta la actual (incluyéndola)
      if ((parada.orden || 0) > ordenActual) {
        break;
      }
      
      // Buscar el pedido para obtener su peso
      const pedido = this.pedidosSeleccionados.find(p => p.id === parada.pedido_id);
      const pesoPedido = pedido ? (pedido.peso || 0) : 0;
      
      if (parada.tipo_operacion === 'carga') {
        // Sumar peso al cargar
        pesoAcumulado += pesoPedido;
      } else if (parada.tipo_operacion === 'descarga') {
        // Restar peso al descargar
        pesoAcumulado -= pesoPedido;
      }
    }
    
    return Math.max(0, pesoAcumulado); // No permitir peso negativo
  }

  hayExcesoPesoEnAlgunaParada(): boolean {
    if (!this.paradasPreview || this.paradasPreview.length === 0) {
      return false;
    }
    
    const capacidad = this.getCapacidadVehiculo();
    if (capacidad === 0) {
      return false; // Si no hay vehículo seleccionado, no validar
    }
    
    // Verificar cada parada
    for (let i = 0; i < this.paradasPreview.length; i++) {
      const pesoAcumulado = this.getPesoAcumuladoEnParada(i);
      if (pesoAcumulado > capacidad) {
        return true;
      }
    }
    
    return false;
  }

  private actualizarParadasPreview(): void {
    const paradas: any[] = [];
    
    // Si estamos editando, usar el orden de las paradas existentes
    if (this.editandoRuta && this.paradasExistentes.size > 0) {
      // Convertir paradas existentes a array y ordenarlas por orden
      const paradasExistentesArray = Array.from(this.paradasExistentes.values())
        .filter(p => this.rutaForm.pedidos_ids.includes(p.pedido_id))
        .sort((a, b) => a.orden - b.orden);
      
      // Crear un mapa de pedido_id -> {carga, descarga} para facilitar el acceso
      const paradasPorPedido: Map<number, { carga: any, descarga: any }> = new Map();
      for (const parada of paradasExistentesArray) {
        if (!paradasPorPedido.has(parada.pedido_id)) {
          paradasPorPedido.set(parada.pedido_id, { carga: null, descarga: null });
        }
        const paradasPedido = paradasPorPedido.get(parada.pedido_id)!;
        if (parada.tipo_operacion === 'carga') {
          paradasPedido.carga = parada;
        } else if (parada.tipo_operacion === 'descarga') {
          paradasPedido.descarga = parada;
        }
      }
      
      // Construir paradas manteniendo el orden existente
      for (const paradaExistente of paradasExistentesArray) {
        const fechas = this.pedidosConFechas.get(paradaExistente.pedido_id);
        const pedido = this.pedidosSeleccionados.find(p => p.id === paradaExistente.pedido_id);
        
        if (pedido) {
          paradas.push({
            id: paradaExistente.id,
            orden: paradaExistente.orden,
            direccion: paradaExistente.direccion,
            tipo_operacion: paradaExistente.tipo_operacion,
            etiqueta: paradaExistente.tipo_operacion === 'carga' ? 'Origen' : 'Destino',
            pedido_id: paradaExistente.pedido_id,
            fecha_hora_llegada: fechas?.fechaCarga && paradaExistente.tipo_operacion === 'carga' 
              ? fechas.fechaCarga 
              : (fechas?.fechaDescarga && paradaExistente.tipo_operacion === 'descarga' 
                ? fechas.fechaDescarga 
                : (paradaExistente.fecha_hora_llegada ? this.getFechaHoraLocal(paradaExistente.fecha_hora_llegada) : '')),
            fecha_entrega_deseada: pedido.fecha_entrega_deseada || null
          });
        }
      }
    } else {
      // Si es una nueva ruta, crear paradas en el orden de los pedidos
      let orden = 1;
      for (const pedido of this.pedidosSeleccionados) {
        const fechas = this.pedidosConFechas.get(pedido.id);
        paradas.push({
          id: null,
          orden: orden++,
          direccion: pedido.origen,
          tipo_operacion: 'carga',
          etiqueta: 'Origen',
          pedido_id: pedido.id,
          fecha_hora_llegada: fechas?.fechaCarga || '',
          fecha_entrega_deseada: pedido.fecha_entrega_deseada || null
        });
        paradas.push({
          id: null,
          orden: orden++,
          direccion: pedido.destino,
          tipo_operacion: 'descarga',
          etiqueta: 'Destino',
          pedido_id: pedido.id,
          fecha_hora_llegada: fechas?.fechaDescarga || '',
          fecha_entrega_deseada: pedido.fecha_entrega_deseada || null
        });
      }
    }
    this.paradasPreview = paradas;
  }

  moverParada(index: number, delta: number): void {
    const nuevoIndex = index + delta;
    if (nuevoIndex < 0 || nuevoIndex >= this.paradasPreview.length) return;
    const copia = [...this.paradasPreview];
    const [item] = copia.splice(index, 1);
    copia.splice(nuevoIndex, 0, item);
    // Reasignar orden secuencial
    copia.forEach((p, idx) => p.orden = idx + 1);
    this.paradasPreview = copia;
    // Sincronizar fechas después de reordenar
    this.sincronizarFechasConPedidos();
  }

  // Drag and Drop
  draggedIndex: number | null = null;

  onDragStart(event: DragEvent, index: number): void {
    this.draggedIndex = index;
    if (event.dataTransfer) {
      event.dataTransfer.effectAllowed = 'move';
      event.dataTransfer.setData('text/html', index.toString());
    }
    if (event.target) {
      (event.target as HTMLElement).classList.add('dragging');
    }
  }

  onDragEnd(event: DragEvent): void {
    if (event.target) {
      (event.target as HTMLElement).classList.remove('dragging');
    }
    this.draggedIndex = null;
  }

  onDragOver(event: DragEvent, index: number): void {
    event.preventDefault();
    if (event.dataTransfer) {
      event.dataTransfer.dropEffect = 'move';
    }
    if (this.draggedIndex !== null && this.draggedIndex !== index) {
      const paradas = [...this.paradasPreview];
      const draggedItem = paradas[this.draggedIndex];
      paradas.splice(this.draggedIndex, 1);
      paradas.splice(index, 0, draggedItem);
      // Actualizar orden
      paradas.forEach((p, i) => {
        p.orden = i + 1;
      });
      this.paradasPreview = paradas;
      this.draggedIndex = index;
      // Sincronizar fechas después de reordenar (solo visual, no se guarda hasta onDrop)
    }
  }

  onDrop(event: DragEvent, index: number): void {
    event.preventDefault();
    if (this.draggedIndex !== null && this.draggedIndex !== index) {
      const paradas = [...this.paradasPreview];
      const draggedItem = paradas[this.draggedIndex];
      paradas.splice(this.draggedIndex, 1);
      paradas.splice(index, 0, draggedItem);
      // Actualizar orden secuencialmente desde 1
      paradas.forEach((p, i) => {
        p.orden = i + 1;
      });
      this.paradasPreview = paradas;
      // Sincronizar fechas después de reordenar
      this.sincronizarFechasConPedidos();
    }
    this.draggedIndex = null;
  }

  contarParadasCarga(paradas: any[]): number {
    if (!paradas) return 0;
    return paradas.filter((p: any) => p.tipo_operacion === 'carga').length;
  }

  contarParadasDescarga(paradas: any[]): number {
    if (!paradas) return 0;
    return paradas.filter((p: any) => p.tipo_operacion === 'descarga').length;
  }

  obtenerNombrePedido(pedidoId: number): string {
    const pedido = this.pedidosDisponibles.find(p => p.id === pedidoId);
    return pedido ? `${pedido.cliente} - ${pedido.destino}` : 'Pedido no encontrado';
  }

  formatearFechaHora(fechaHora: string): string {
    if (!fechaHora) return '';
    
    // Si ya viene en formato "dd/mm/YYYY HH:MM" desde el backend, devolverlo tal cual
    if (fechaHora.includes('/') && fechaHora.includes(':')) {
      return fechaHora;
    }
    
    // Si viene en formato ISO o datetime, parsearlo
    try {
      const fecha = new Date(fechaHora);
      if (isNaN(fecha.getTime())) return fechaHora; // Si no se puede parsear, devolver tal cual
      
      const day = String(fecha.getDate()).padStart(2, '0');
      const month = String(fecha.getMonth() + 1).padStart(2, '0');
      const year = fecha.getFullYear().toString().padStart(4, '0');
      const hours = String(fecha.getHours()).padStart(2, '0');
      const minutes = String(fecha.getMinutes()).padStart(2, '0');
      // Formato dd/mm/YYYY HH:MM
      return `${day}/${month}/${year} ${hours}:${minutes}`;
    } catch (e) {
      return fechaHora; // Si hay error, devolver tal cual
    }
  }

  getFechaHoraLocal(fechaHora: string | null | undefined): string {
    if (!fechaHora) return '';
    
    // Si ya está en formato datetime-local (YYYY-MM-DDTHH:mm), devolverlo directamente
    if (fechaHora.includes('T') && fechaHora.length <= 16 && !fechaHora.includes('Z') && !fechaHora.includes('+')) {
      return fechaHora;
    }
    
    // Si viene en formato "dd/mm/YYYY HH:MM" desde el backend
    if (fechaHora.includes('/') && fechaHora.includes(':')) {
      try {
        const partes = fechaHora.trim().split(' ');
        const fechaParte = partes[0]; // "dd/mm/YYYY"
        const horaParte = partes[1] || '00:00'; // "HH:MM"
        const partesFecha = fechaParte.split('/');
        
        if (partesFecha.length === 3) {
          const dia = partesFecha[0].padStart(2, '0');
          const mes = partesFecha[1].padStart(2, '0');
          const año = partesFecha[2];
          return `${año}-${mes}-${dia}T${horaParte}`;
        }
      } catch (e) {
        console.error('Error parseando fecha:', e, fechaHora);
      }
    }
    
    // Si viene en formato ISO string, convertir a datetime-local
    try {
      const fecha = new Date(fechaHora);
      if (isNaN(fecha.getTime())) return '';
      
      // Ajustar por zona horaria local
      const localDate = new Date(fecha.getTime() - fecha.getTimezoneOffset() * 60000);
      return localDate.toISOString().slice(0, 16);
    } catch (e) {
      return '';
    }
  }

  actualizarFechaHoraParada(rutaId: number, paradaId: number, fechaHora: string): void {
    if (!fechaHora) return;
    const fechaHoraISO = new Date(fechaHora).toISOString();
    this.apiService.updateParadaRuta(rutaId, paradaId, { fecha_hora_llegada: fechaHoraISO }).subscribe({
      next: () => {
        this.cargarRutas();
      },
      error: (err: HttpErrorResponse) => {
        this.error = err.error?.detail || 'Error al actualizar fecha de llegada';
      }
    });
  }

  actualizarFechaParada(index: number, event: Event): void {
    const input = event.target as HTMLInputElement;
    const nuevaFecha = input.value;
    
    // Limpiar errores previos cuando se modifica una fecha
    this.error = '';
    
    if (!nuevaFecha) {
      // Si se elimina la fecha, limpiarla
      this.paradasPreview[index].fecha_hora_llegada = '';
      this.sincronizarFechasConPedidos();
      return;
    }
    
    // El valor viene en formato datetime-local (YYYY-MM-DDTHH:mm)
    // Guardarlo directamente en ese formato para mantener consistencia
    // Se convertirá a ISO string al enviar al backend
    this.paradasPreview[index].fecha_hora_llegada = nuevaFecha;
    
    // Sincronizar con pedidosConFechas para mantener coherencia
    this.sincronizarFechasConPedidos();
    
    // Validación básica en tiempo real (opcional, solo para feedback)
    // Las validaciones completas se harán al guardar
  }

  sincronizarFechasConPedidos(): void {
    // Actualizar pedidosConFechas basándose en las fechas de las paradas según el orden
    // Para cada pedido, buscar la primera carga y la última descarga según el orden
    const fechasPorPedido: Map<number, { primeraCarga: string, ultimaDescarga: string }> = new Map();
    
    // Ordenar paradas por orden para procesarlas correctamente
    const paradasOrdenadas = [...this.paradasPreview].sort((a, b) => a.orden - b.orden);
    
    for (const parada of paradasOrdenadas) {
      if (!parada.fecha_hora_llegada) continue;
      
      if (!fechasPorPedido.has(parada.pedido_id)) {
        fechasPorPedido.set(parada.pedido_id, {
          primeraCarga: '',
          ultimaDescarga: ''
        });
      }
      
      const fechas = fechasPorPedido.get(parada.pedido_id)!;
      
      if (parada.tipo_operacion === 'carga') {
        // Usar la primera carga según el orden
        if (!fechas.primeraCarga) {
          fechas.primeraCarga = parada.fecha_hora_llegada;
        }
      } else if (parada.tipo_operacion === 'descarga') {
        // Usar la última descarga según el orden
        if (!fechas.ultimaDescarga || parada.fecha_hora_llegada > fechas.ultimaDescarga) {
          fechas.ultimaDescarga = parada.fecha_hora_llegada;
        }
      }
    }
    
    // Actualizar pedidosConFechas con las fechas encontradas
    // No limpiar completamente, solo actualizar los que tienen fechas en las paradas
    for (const [pedidoId, fechas] of fechasPorPedido.entries()) {
      if (!this.pedidosConFechas.has(pedidoId)) {
        this.pedidosConFechas.set(pedidoId, {
          fechaCarga: '',
          fechaDescarga: ''
        });
      }
      const fechasExistentes = this.pedidosConFechas.get(pedidoId)!;
      if (fechas.primeraCarga) {
        fechasExistentes.fechaCarga = fechas.primeraCarga;
      }
      if (fechas.ultimaDescarga) {
        fechasExistentes.fechaDescarga = fechas.ultimaDescarga;
      }
    }
  }

  onSubmit(): void {
    if (!this.rutaForm.fecha_inicio || !this.rutaForm.fecha_fin || !this.rutaForm.conductor_id || !this.rutaForm.vehiculo_id) {
      this.error = 'La fecha de inicio, fecha de fin, conductor y vehículo son obligatorios';
      return;
    }

    // Validar que haya al menos un pedido seleccionado
    if (this.rutaForm.pedidos_ids.length === 0) {
      this.error = 'Debe seleccionar al menos un pedido';
      return;
    }

    this.loading = true;
    this.error = '';
    
    // Convertir fechas a formato datetime (añadir hora 00:00:00 para inicio y 23:59:59 para fin)
    // Usar hora local para evitar problemas de zona horaria
    const fechaInicioStr = this.rutaForm.fecha_inicio + 'T00:00:00';
    const fechaFinStr = this.rutaForm.fecha_fin + 'T23:59:59';
    const fechaInicio = new Date(fechaInicioStr);
    const fechaFin = new Date(fechaFinStr);
    
    // Verificar que las fechas sean válidas
    if (isNaN(fechaInicio.getTime()) || isNaN(fechaFin.getTime())) {
      this.error = 'Las fechas proporcionadas no son válidas';
      this.loading = false;
      return;
    }
    
    // Validar que fecha_fin >= fecha_inicio
    if (fechaFin < fechaInicio) {
      this.error = `La fecha de fin (${this.formatearFecha(this.rutaForm.fecha_fin)}) no puede ser anterior a la fecha de inicio (${this.formatearFecha(this.rutaForm.fecha_inicio)})`;
      this.loading = false;
      return;
    }
    
    // Validar peso acumulado en cada parada
    if (this.paradasPreview.length > 0 && this.rutaForm.vehiculo_id) {
      const capacidad = this.getCapacidadVehiculo();
      if (capacidad > 0) {
        const paradasOrdenadas = [...this.paradasPreview].sort((a, b) => (a.orden || 0) - (b.orden || 0));
        
        for (let i = 0; i < paradasOrdenadas.length; i++) {
          const pesoAcumulado = this.getPesoAcumuladoEnParada(i);
          if (pesoAcumulado > capacidad) {
            const parada = paradasOrdenadas[i];
            const pedido = this.pedidosSeleccionados.find(p => p.id === parada.pedido_id);
            const clienteInfo = pedido ? ` (Cliente: ${pedido.cliente})` : '';
            this.error = `El peso acumulado en la parada #${parada.orden} (${pesoAcumulado} kg) excede la capacidad del vehículo (${capacidad} kg)${clienteInfo}. Ajuste el orden de las paradas o seleccione un vehículo con mayor capacidad.`;
            this.loading = false;
            return;
          }
        }
      }
    }
    
    // Validar fechas según el orden de las paradas (paradasPreview ordenadas)
    // Ordenar paradas por orden
    const paradasOrdenadas = [...this.paradasPreview].sort((a, b) => (a.orden || 0) - (b.orden || 0));
    
    // Rastrear las últimas cargas por pedido para validar que no se descargue sin haber cargado
    const ultimasCargasPorPedido: Map<number, Date> = new Map();
    let ultimaDescarga: Date | null = null;
    
    for (const parada of paradasOrdenadas) {
      if (!parada.fecha_hora_llegada) {
        continue; // Saltar paradas sin fecha
      }
      
      // Convertir fecha a Date - puede venir en formato datetime-local (YYYY-MM-DDTHH:mm) o ISO string
      let fechaParada: Date;
      if (parada.fecha_hora_llegada.includes('T') && parada.fecha_hora_llegada.length <= 16) {
        // Formato datetime-local: YYYY-MM-DDTHH:mm
        fechaParada = new Date(parada.fecha_hora_llegada);
      } else {
        // Formato ISO string
        fechaParada = new Date(parada.fecha_hora_llegada);
      }
      
      // Validar que la fecha sea válida
      if (isNaN(fechaParada.getTime())) {
        this.error = `La fecha de la parada #${parada.orden} no es válida`;
        this.loading = false;
        return;
      }
      
      if (parada.tipo_operacion === 'carga') {
        // Actualizar última carga para este pedido
        const ultimaCarga = ultimasCargasPorPedido.get(parada.pedido_id);
        if (!ultimaCarga || fechaParada > ultimaCarga) {
          ultimasCargasPorPedido.set(parada.pedido_id, fechaParada);
        }
      } else if (parada.tipo_operacion === 'descarga') {
        // Validar que haya una carga anterior para este pedido
        const ultimaCarga = ultimasCargasPorPedido.get(parada.pedido_id);
        if (!ultimaCarga) {
          const pedido = this.pedidosSeleccionados.find(p => p.id === parada.pedido_id);
          const clienteInfo = pedido ? ` (Cliente: ${pedido.cliente})` : '';
          this.error = `No se puede descargar el pedido ${parada.pedido_id}${clienteInfo} en la parada #${parada.orden} sin haber cargado antes. Debe haber una parada de carga anterior para este pedido.`;
          this.loading = false;
          return;
        }
        
        // Validar que la descarga sea después de la última carga
        if (fechaParada < ultimaCarga) {
          const pedido = this.pedidosSeleccionados.find(p => p.id === parada.pedido_id);
          const clienteInfo = pedido ? ` (Cliente: ${pedido.cliente})` : '';
          this.error = `Para el pedido ${parada.pedido_id}${clienteInfo}, la fecha de descarga en la parada #${parada.orden} (${this.formatearFechaHora(parada.fecha_hora_llegada)}) no puede ser anterior a la última carga (${this.formatearFechaHora(ultimaCarga.toISOString())})`;
          this.loading = false;
          return;
        }
        
        // Actualizar última descarga global
        if (!ultimaDescarga || fechaParada > ultimaDescarga) {
          ultimaDescarga = fechaParada;
        }
      }
      
      // Validar coherencia con la parada anterior (si existe)
      const indexActual = paradasOrdenadas.indexOf(parada);
      if (indexActual > 0) {
        const paradaAnterior = paradasOrdenadas[indexActual - 1];
        if (paradaAnterior.fecha_hora_llegada) {
          // Convertir fecha anterior a Date
          let fechaAnterior: Date;
          if (paradaAnterior.fecha_hora_llegada.includes('T') && paradaAnterior.fecha_hora_llegada.length <= 16) {
            fechaAnterior = new Date(paradaAnterior.fecha_hora_llegada);
          } else {
            fechaAnterior = new Date(paradaAnterior.fecha_hora_llegada);
          }
          
          if (isNaN(fechaAnterior.getTime())) {
            this.error = `La fecha de la parada anterior #${paradaAnterior.orden} no es válida`;
            this.loading = false;
            return;
          }
          
          if (fechaParada < fechaAnterior) {
            this.error = `La fecha de la parada #${parada.orden} (${this.formatearFechaHora(parada.fecha_hora_llegada)}) no puede ser anterior a la parada anterior #${paradaAnterior.orden} (${this.formatearFechaHora(paradaAnterior.fecha_hora_llegada)}) según el orden establecido`;
            this.loading = false;
            return;
          }
        }
      }
    }
    
    // Validar que fecha_fin >= última fecha de descarga después de ordenar
    if (ultimaDescarga && fechaFin < ultimaDescarga) {
      this.error = `La fecha de fin de la ruta (${this.formatearFecha(this.rutaForm.fecha_fin)}) no puede ser anterior a la última fecha de descarga (${this.formatearFechaHora(ultimaDescarga.toISOString())}) después de ordenar las paradas`;
      this.loading = false;
      return;
    }
    
    // Sincronizar fechas antes de guardar para asegurar coherencia
    this.sincronizarFechasConPedidos();
    
    const rutaData: any = {
      fecha_inicio: fechaInicio.toISOString(),
      fecha_fin: fechaFin.toISOString(),
      conductor_id: this.rutaForm.conductor_id,
      vehiculo_id: this.rutaForm.vehiculo_id,
      observaciones: this.rutaForm.observaciones || '',
      pedidos_ids: this.rutaForm.pedidos_ids,
      paradas_con_fechas: null // Inicializar como null, se asignará después si hay paradas
    };
    
    // Añadir paradas con fechas según el orden establecido (tiene prioridad)
    // IMPORTANTE: Siempre enviar paradas si existen, para que el backend valide por peso acumulado
    // Enviar todas las paradas según el orden, para que el backend pueda validar coherencia
    // Las fechas en paradasPreview tienen prioridad sobre pedidosConFechas
    if (this.paradasPreview && this.paradasPreview.length > 0) {
      // Ordenar paradas por orden antes de enviar
      const paradasOrdenadas = [...this.paradasPreview].sort((a, b) => (a.orden || 0) - (b.orden || 0));
      
      const paradasConFechas = paradasOrdenadas
        .map((p, i) => {
          // Asegurar que la fecha esté en formato correcto
          let fechaHora = p.fecha_hora_llegada;
          
          // Si no hay fecha en la parada pero existe en pedidosConFechas, usarla
          if (!fechaHora) {
            const fechas = this.pedidosConFechas.get(p.pedido_id);
            if (fechas) {
              if (p.tipo_operacion === 'carga' && fechas.fechaCarga) {
                fechaHora = fechas.fechaCarga;
              } else if (p.tipo_operacion === 'descarga' && fechas.fechaDescarga) {
                fechaHora = fechas.fechaDescarga;
              }
            }
          }
          
          // Asegurar que el orden sea correcto (usar el orden de la parada o el índice + 1)
          const ordenFinal = p.orden ? parseInt(String(p.orden)) : (i + 1);
          
          return {
            parada_id: p.id || null, // ID si es parada existente
            pedido_id: p.pedido_id,
            orden: ordenFinal,
            tipo_operacion: p.tipo_operacion,
            fecha_hora_llegada: fechaHora ? new Date(fechaHora).toISOString() : null
          };
        });
      
      // SIEMPRE asignar paradas_con_fechas si hay paradas
      rutaData.paradas_con_fechas = paradasConFechas;
    } else {
      // Si no hay paradas, asegurar que paradas_con_fechas sea null/undefined
      rutaData.paradas_con_fechas = null;
    }
    
    // Añadir fechas/horas aproximadas para cada pedido (legacy, para compatibilidad si no hay paradas_con_fechas)
    if (this.pedidosConFechas.size > 0 && (!rutaData.paradas_con_fechas || rutaData.paradas_con_fechas.length === 0)) {
      rutaData.pedidos_con_fechas = [];
      this.pedidosConFechas.forEach((fechas, pedidoId) => {
        if (this.rutaForm.pedidos_ids.includes(pedidoId)) {
          rutaData.pedidos_con_fechas.push({
            pedido_id: pedidoId,
            fecha_hora_carga: fechas.fechaCarga ? new Date(fechas.fechaCarga).toISOString() : null,
            fecha_hora_descarga: fechas.fechaDescarga ? new Date(fechas.fechaDescarga).toISOString() : null
          });
        }
      });
    }
    
    if (this.editandoRuta && this.rutaIdEditando) {
      this.apiService.updateRuta(this.rutaIdEditando, rutaData).subscribe({
        next: () => {
          this.cargarRutas();
          this.cargarPedidos(); // Recargar pedidos para actualizar disponibilidad
          this.mostrarFormulario = false;
          this.editandoRuta = false;
          this.rutaIdEditando = null;
          this.loading = false;
          this.error = '';
        },
        error: (err: HttpErrorResponse) => {
          if (err.error?.detail) {
            if (typeof err.error.detail === 'object' && err.error.detail.error) {
              // Error de capacidad con detalles
              const detalle = err.error.detail;
              this.error = `${detalle.error}: Peso total ${detalle.peso_total} kg excede capacidad de ${detalle.capacidad_vehiculo} kg (exceso: ${detalle.exceso} kg). Pedidos problemáticos: ${detalle.pedidos_problema?.join(', ') || 'N/A'}`;
            } else {
              this.error = err.error.detail;
            }
          } else {
            this.error = err.error?.message || err.message || 'Error al actualizar ruta';
          }
          this.loading = false;
          if (err.status === 401) {
            this.authService.logout();
          }
        }
      });
    } else {
      this.apiService.createRuta(rutaData).subscribe({
        next: () => {
          this.cargarRutas();
          this.cargarPedidos(); // Recargar pedidos para actualizar disponibilidad
          this.mostrarFormulario = false;
          this.loading = false;
          this.error = '';
        },
        error: (err: HttpErrorResponse) => {
          if (err.error?.detail) {
            if (typeof err.error.detail === 'object' && err.error.detail.error) {
              // Error de capacidad con detalles
              const detalle = err.error.detail;
              this.error = `${detalle.error}: Peso total ${detalle.peso_total} kg excede capacidad de ${detalle.capacidad_vehiculo} kg (exceso: ${detalle.exceso} kg). Pedidos problemáticos: ${detalle.pedidos_problema?.join(', ') || 'N/A'}`;
            } else {
              this.error = typeof err.error.detail === 'string' ? err.error.detail : JSON.stringify(err.error.detail);
            }
          } else {
            this.error = err.error?.message || 'Error al crear ruta. Verifique los datos e intente nuevamente.';
          }
          this.loading = false;
          if (err.status === 401) {
            this.authService.logout();
          }
        }
      });
    }
  }

  getEstadoClass(estado: string): string {
    // Para los bordes dinámicos, usar clases con prefijo "estado-"
    const clases: { [key: string]: string } = {
      'planificada': 'estado-planificada',
      'en_curso': 'estado-en-curso',
      'completada': 'estado-completada',
      'cancelada': 'estado-cancelada'
    };
    return clases[estado?.toLowerCase()] || 'estado-planificada';
  }

  getEstadoTexto(estado: string): string {
    const textos: { [key: string]: string } = {
      'planificada': 'Planificada',
      'en_curso': 'En Progreso',
      'completada': 'Completada',
      'cancelada': 'Cancelada'
    };
    return textos[estado?.toLowerCase()] || estado || 'Planificada';
  }

  getProgresoParadasTexto(ruta: any): string {
    // Solo mostrar progreso en listado cuando está en progreso
    if (!ruta || ruta.estado?.toLowerCase() !== 'en_curso') return '';
    const total = ruta.paradas?.length || 0;
    if (!total) return ' (0/0 paradas)';
    const completadas = (ruta.paradas || []).filter((p: any) => p?.estado === 'entregado').length;
    return ` (${completadas}/${total} paradas)`;
  }

  parsearFechaParaInput(fechaStr: string): string {
    // Convierte fecha en formato "dd/mm/YYYY HH:MM" o "dd/mm/YYYY" a formato YYYY-MM-DD para input type="date"
    if (!fechaStr) return '';
    
    try {
      // Si ya está en formato ISO, devolver solo la parte de fecha
      if (fechaStr.includes('T') || fechaStr.match(/^\d{4}-\d{2}-\d{2}/)) {
        return fechaStr.split('T')[0].split(' ')[0];
      }
      
      // Formato "dd/mm/YYYY HH:MM" o "dd/mm/YYYY"
      const partes = fechaStr.trim().split(' ');
      const fechaParte = partes[0]; // "dd/mm/YYYY"
      const partesFecha = fechaParte.split('/');
      
      if (partesFecha.length === 3) {
        const dia = partesFecha[0].padStart(2, '0');
        const mes = partesFecha[1].padStart(2, '0');
        const año = partesFecha[2];
        return `${año}-${mes}-${dia}`;
      }
    } catch (e) {
      console.error('Error parseando fecha:', e, fechaStr);
    }
    
    return '';
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

  getParadasCompletadas(): number {
    if (!this.rutaActual || !this.rutaActual.paradas) return 0;
    return this.rutaActual.paradas.filter((p: any) => p.estado === 'entregado').length;
  }

  getTotalParadas(): number {
    if (!this.rutaActual || !this.rutaActual.paradas) return 0;
    return this.rutaActual.paradas.length;
  }

  todasParadasCompletadas(): boolean {
    if (!this.rutaActual || !this.rutaActual.paradas) return false;
    return this.rutaActual.paradas.every((p: any) => p.estado === 'entregado');
  }

  finalizarRuta(): void {
    if (!this.rutaIdEditando) return;
    
    if (!this.todasParadasCompletadas()) {
      this.error = 'No se puede finalizar la ruta. Todas las paradas deben estar completadas.';
      return;
    }

    this.loading = true;
    this.error = '';
    
    this.apiService.finalizarRuta(this.rutaIdEditando).subscribe({
      next: () => {
        this.cargarRutas();
        this.mostrarFormulario = false;
        this.editandoRuta = false;
        this.rutaIdEditando = null;
        this.rutaActual = null;
        this.loading = false;
        this.error = '';
      },
      error: (err: HttpErrorResponse) => {
        this.loading = false;
        this.error = err.error?.detail || 'Error al finalizar la ruta';
      }
    });
  }

  getUrlFoto(rutaFoto: string, paradaId: number): string {
    if (!rutaFoto || !paradaId) return '';
    // Usar el endpoint de la API para obtener la foto
    const token = localStorage.getItem('access_token');
    const tokenParam = token ? `?token=${encodeURIComponent(token)}` : '';
    return `${this.apiService.getBaseUrl()}/api/rutas/paradas/${paradaId}/foto${tokenParam}`;
  }

  getUrlFirma(rutaFirma: string, paradaId: number): string {
    if (!rutaFirma || !paradaId) return '';
    // Usar el endpoint de la API para obtener la firma
    const token = localStorage.getItem('access_token');
    const tokenParam = token ? `?token=${encodeURIComponent(token)}` : '';
    return `${this.apiService.getBaseUrl()}/api/rutas/paradas/${paradaId}/firma${tokenParam}`;
  }

  getParadasOrdenadas(): any[] {
    if (!this.rutaActual || !this.rutaActual.paradas) return [];
    return [...this.rutaActual.paradas].sort((a: any, b: any) => a.orden - b.orden);
  }

  formatearTipoIncidencia(tipo: string): string {
    const tipos: { [key: string]: string } = {
      'averia': 'Avería',
      'retraso': 'Retraso',
      'cliente_ausente': 'Cliente ausente',
      'otros': 'Otros'
    };
    return tipos[tipo] || tipo;
  }

  getUrlFotoIncidencia(incidenciaId: number, fotoId: number): string {
    if (!incidenciaId || !fotoId) return '';
    // Usar el endpoint de la API para obtener la foto
    const token = localStorage.getItem('access_token');
    const tokenParam = token ? `?token=${encodeURIComponent(token)}` : '';
    return `${this.apiService.getBaseUrl()}/api/rutas/incidencias/${incidenciaId}/fotos/${fotoId}${tokenParam}`;
  }

  getParadaOrden(paradaId: number): number {
    if (!this.rutaActual || !this.rutaActual.paradas) return 0;
    const parada = this.rutaActual.paradas.find((p: any) => p.id === paradaId);
    return parada ? parada.orden : 0;
  }
}

