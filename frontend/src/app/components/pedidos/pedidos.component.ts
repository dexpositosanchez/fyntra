import { Component, OnInit, OnDestroy } from '@angular/core';
import { Router, NavigationEnd } from '@angular/router';
import { Subscription } from 'rxjs';
import { filter } from 'rxjs/operators';
import { ApiService } from '../../services/api.service';
import { AuthService } from '../../services/auth.service';
import { HttpErrorResponse } from '@angular/common/http';

@Component({
  selector: 'app-pedidos',
  templateUrl: './pedidos.component.html',
  styleUrls: ['./pedidos.component.scss']
})
export class PedidosComponent implements OnInit, OnDestroy {
  pedidos: any[] = [];
  mostrarFormulario: boolean = false;
  editandoPedido: boolean = false;
  pedidoIdEditando: number | null = null;
  pedidoForm: any = {
    origen: '',
    destino: '',
    cliente: '',
    volumen: null,
    peso: null,
    tipo_mercancia: '',
    fecha_entrega_deseada: '',
    estado: 'pendiente'
  };
  loading: boolean = false;
  error: string = '';
  currentRoute: string = '';
  mostrarMenuUsuario: boolean = false;
  usuario: any = null;
  private routerSubscription?: Subscription;
  
  estados = [
    { value: 'pendiente', label: 'Pendiente' },
    { value: 'en_ruta', label: 'En Ruta' },
    { value: 'entregado', label: 'Entregado' },
    { value: 'incidencia', label: 'Incidencia' },
    { value: 'cancelado', label: 'Cancelado' }
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
    
    this.routerSubscription = this.router.events
      .pipe(filter(event => event instanceof NavigationEnd))
      .subscribe((event: any) => {
        this.currentRoute = event.url;
        this.actualizarVista();
      });
  }

  actualizarVista(): void {
    if (!this.currentRoute.includes('/pedidos')) {
      this.mostrarFormulario = false;
    }
    
    if (this.currentRoute.includes('/pedidos')) {
      this.cargarPedidos();
    }
  }

  ngOnDestroy(): void {
    if (this.routerSubscription) {
      this.routerSubscription.unsubscribe();
    }
  }

  cargarPedidos(): void {
    this.loading = true;
    this.apiService.getPedidos().subscribe({
      next: (data) => {
        // Convertir fechas de string a Date para el pipe date
        this.pedidos = data.map((pedido: any) => ({
          ...pedido,
          fecha_entrega_deseada: pedido.fecha_entrega_deseada ? new Date(pedido.fecha_entrega_deseada) : null
        }));
        this.loading = false;
      },
      error: (err: HttpErrorResponse) => {
        this.error = err.error?.detail || 'Error al cargar pedidos';
        this.loading = false;
        if (err.status === 401) {
          this.authService.logout();
        }
      }
    });
  }

  mostrarForm(): void {
    this.editandoPedido = false;
    this.pedidoIdEditando = null;
    this.mostrarFormulario = true;
    this.pedidoForm = {
      origen: '',
      destino: '',
      cliente: '',
      volumen: null,
      peso: null,
      tipo_mercancia: '',
      fecha_entrega_deseada: '',
      estado: 'pendiente'
    };
  }

  editarPedido(pedido: any): void {
    this.editandoPedido = true;
    this.pedidoIdEditando = pedido.id;
    this.mostrarFormulario = true;
    
    // Formatear fecha para el input date (YYYY-MM-DD)
    let fechaFormateada = '';
    if (pedido.fecha_entrega_deseada) {
      const fecha = new Date(pedido.fecha_entrega_deseada);
      fechaFormateada = fecha.toISOString().split('T')[0];
    }
    
    this.pedidoForm = {
      origen: pedido.origen || '',
      destino: pedido.destino || '',
      cliente: pedido.cliente || '',
      volumen: pedido.volumen || null,
      peso: pedido.peso || null,
      tipo_mercancia: pedido.tipo_mercancia || '',
      fecha_entrega_deseada: fechaFormateada,
      estado: pedido.estado || 'pendiente'
    };
  }

  cancelarForm(): void {
    this.mostrarFormulario = false;
    this.editandoPedido = false;
    this.pedidoIdEditando = null;
    this.error = '';
  }

  onSubmit(): void {
    if (!this.pedidoForm.origen || !this.pedidoForm.destino || !this.pedidoForm.cliente || !this.pedidoForm.fecha_entrega_deseada) {
      this.error = 'El origen, destino, cliente y fecha de entrega son obligatorios';
      return;
    }

    this.loading = true;
    
    if (this.editandoPedido && this.pedidoIdEditando) {
      this.apiService.updatePedido(this.pedidoIdEditando, this.pedidoForm).subscribe({
        next: () => {
          this.cargarPedidos();
          this.mostrarFormulario = false;
          this.editandoPedido = false;
          this.pedidoIdEditando = null;
          this.loading = false;
          this.error = '';
        },
        error: (err: HttpErrorResponse) => {
          this.error = err.error?.detail || 'Error al actualizar pedido';
          this.loading = false;
          if (err.status === 401) {
            this.authService.logout();
          }
        }
      });
    } else {
      this.apiService.createPedido(this.pedidoForm).subscribe({
        next: () => {
          this.cargarPedidos();
          this.mostrarFormulario = false;
          this.loading = false;
          this.error = '';
        },
        error: (err: HttpErrorResponse) => {
          this.error = err.error?.detail || 'Error al crear pedido';
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
      'pendiente': 'pendiente',
      'en_ruta': 'en-ruta',
      'entregado': 'entregado',
      'incidencia': 'incidencia',
      'cancelado': 'cancelado'
    };
    return clases[estado?.toLowerCase()] || 'pendiente';
  }

  getEstadoTexto(estado: string): string {
    const textos: { [key: string]: string } = {
      'pendiente': 'Pendiente',
      'en_ruta': 'En Ruta',
      'entregado': 'Entregado',
      'incidencia': 'Incidencia',
      'cancelado': 'Cancelado'
    };
    return textos[estado?.toLowerCase()] || estado || 'Pendiente';
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
}

