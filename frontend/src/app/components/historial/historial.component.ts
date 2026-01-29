import { Component, OnInit } from '@angular/core';
import { Router } from '@angular/router';
import { ApiService } from '../../services/api.service';
import { AuthService } from '../../services/auth.service';

@Component({
  selector: 'app-historial',
  templateUrl: './historial.component.html',
  styleUrls: ['./historial.component.scss']
})
export class HistorialComponent implements OnInit {
  loading = false;
  error = '';
  mostrarMenuUsuario = false;
  usuario: any = null;

  listado: any[] = [];
  fechaDesde = '';
  fechaHasta = '';
  soloConRuta = false;

  constructor(
    private apiService: ApiService,
    private authService: AuthService,
    private router: Router
  ) {}

  ngOnInit(): void {
    this.usuario = this.authService.getUsuario();
    this.inicializarFechas();
    this.cargarHistorial();
  }

  get currentRoute(): string {
    return this.router.url || '';
  }

  estaEnModuloTransportes(): boolean {
    return this.currentRoute.includes('/vehiculos') ||
           this.currentRoute.includes('/conductores') ||
           this.currentRoute.includes('/rutas') ||
           this.currentRoute.includes('/pedidos') ||
           this.currentRoute.includes('/historial');
  }

  cambiarAModuloTransportes(): void {
    this.mostrarMenuUsuario = false;
    this.router.navigate(['/vehiculos']);
  }

  inicializarFechas(): void {
    const hoy = new Date();
    const primerDia = new Date(hoy.getFullYear(), hoy.getMonth(), 1);
    const ultimoDia = new Date(hoy.getFullYear(), hoy.getMonth() + 1, 0);
    this.fechaDesde = this.formatearFechaParaInput(primerDia);
    this.fechaHasta = this.formatearFechaParaInput(ultimoDia);
  }

  formatearFechaParaInput(fecha: Date): string {
    const año = fecha.getFullYear();
    const mes = String(fecha.getMonth() + 1).padStart(2, '0');
    const dia = String(fecha.getDate()).padStart(2, '0');
    return `${año}-${mes}-${dia}`;
  }

  cargarHistorial(): void {
    this.loading = true;
    this.error = '';
    this.apiService.getHistorialPedidos(this.fechaDesde, this.fechaHasta, this.soloConRuta).subscribe({
      next: (data) => {
        this.listado = Array.isArray(data) ? data : [];
        this.loading = false;
      },
      error: (err) => {
        this.error = err.error?.detail || 'Error al cargar el historial';
        this.loading = false;
      }
    });
  }

  aplicarFiltros(): void {
    if (!this.fechaDesde || !this.fechaHasta) {
      this.error = 'Debe seleccionar ambas fechas';
      return;
    }
    if (new Date(this.fechaDesde) > new Date(this.fechaHasta)) {
      this.error = 'La fecha desde debe ser anterior a la fecha hasta';
      return;
    }
    this.cargarHistorial();
  }

  descargar(formato: string): void {
    this.loading = true;
    this.error = '';
    const ext = formato === 'excel' ? 'xlsx' : formato === 'pdf' ? 'pdf' : 'csv';
    this.apiService.exportarHistorialPedidos(formato, this.fechaDesde, this.fechaHasta, this.soloConRuta).subscribe({
      next: (blob) => {
        const url = window.URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = `historial_pedidos.${ext}`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        window.URL.revokeObjectURL(url);
        this.loading = false;
      },
      error: (err) => {
        this.error = err.error?.detail || 'Error al descargar';
        this.loading = false;
      }
    });
  }

  formatearFecha(fechaStr: string): string {
    if (!fechaStr) return '-';
    const d = new Date(fechaStr);
    const dia = String(d.getDate()).padStart(2, '0');
    const mes = String(d.getMonth() + 1).padStart(2, '0');
    const año = d.getFullYear();
    return `${dia}/${mes}/${año}`;
  }

  formatearFechaHora(fechaStr: string): string {
    if (!fechaStr) return '-';
    const d = new Date(fechaStr);
    const dia = String(d.getDate()).padStart(2, '0');
    const mes = String(d.getMonth() + 1).padStart(2, '0');
    const año = d.getFullYear();
    const h = String(d.getHours()).padStart(2, '0');
    const m = String(d.getMinutes()).padStart(2, '0');
    return `${dia}/${mes}/${año} ${h}:${m}`;
  }

  getEstadoLabel(estado: string): string {
    const labels: { [key: string]: string } = {
      pendiente: 'Pendiente',
      en_ruta: 'En ruta',
      entregado: 'Entregado',
      incidencia: 'Incidencia',
      cancelado: 'Cancelado'
    };
    return labels[estado] || estado || '-';
  }

  toggleMenuUsuario(): void {
    this.mostrarMenuUsuario = !this.mostrarMenuUsuario;
  }

  logout(): void {
    this.authService.logout();
  }

  cambiarAModuloFincas(): void {
    this.mostrarMenuUsuario = false;
    this.router.navigate(['/incidencias']);
  }

  irAUsuarios(): void {
    this.mostrarMenuUsuario = false;
    this.router.navigate(['/usuarios']);
  }
}
