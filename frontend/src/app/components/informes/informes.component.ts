import { Component, OnInit } from '@angular/core';
import { Router } from '@angular/router';
import { ApiService } from '../../services/api.service';
import { AuthService } from '../../services/auth.service';

@Component({
  selector: 'app-informes',
  templateUrl: './informes.component.html',
  styleUrls: ['./informes.component.scss']
})
export class InformesComponent implements OnInit {
  tabActiva: string = 'comunidades';
  loading: boolean = false;
  error: string = '';
  mostrarMenuUsuario: boolean = false;
  usuario: any = null;

  // Datos de comunidades
  informesComunidades: any = null;
  comunidadesExpandidas: Set<number> = new Set();

  // Datos de proveedores
  informesProveedores: any = null;

  // Filtros de fecha
  fechaInicio: string = '';
  fechaFin: string = '';

  constructor(
    private apiService: ApiService,
    private authService: AuthService,
    private router: Router
  ) {}

  ngOnInit(): void {
    this.usuario = this.authService.getUsuario();
    this.inicializarFechas();
    this.cargarInformes();
  }

  inicializarFechas(): void {
    // Por defecto, mes actual
    const hoy = new Date();
    const primerDia = new Date(hoy.getFullYear(), hoy.getMonth(), 1);
    const ultimoDia = new Date(hoy.getFullYear(), hoy.getMonth() + 1, 0);
    
    this.fechaInicio = this.formatearFechaParaInput(primerDia);
    this.fechaFin = this.formatearFechaParaInput(ultimoDia);
  }

  formatearFechaParaInput(fecha: Date): string {
    const año = fecha.getFullYear();
    const mes = String(fecha.getMonth() + 1).padStart(2, '0');
    const dia = String(fecha.getDate()).padStart(2, '0');
    return `${año}-${mes}-${dia}`;
  }

  cambiarTab(tab: string): void {
    this.tabActiva = tab;
    this.cargarInformes();
  }

  cargarInformes(): void {
    this.loading = true;
    this.error = '';

    if (this.tabActiva === 'comunidades') {
      this.cargarInformesComunidades();
    } else {
      this.cargarInformesProveedores();
    }
  }

  cargarInformesComunidades(): void {
    this.apiService.getInformesComunidades(this.fechaInicio, this.fechaFin).subscribe({
      next: (data) => {
        this.informesComunidades = data;
        this.loading = false;
      },
      error: (err) => {
        this.error = err.error?.detail || 'Error al cargar informes de comunidades';
        this.loading = false;
      }
    });
  }

  cargarInformesProveedores(): void {
    this.apiService.getInformesProveedores(this.fechaInicio, this.fechaFin).subscribe({
      next: (data) => {
        this.informesProveedores = data;
        this.loading = false;
      },
      error: (err) => {
        this.error = err.error?.detail || 'Error al cargar informes de proveedores';
        this.loading = false;
      }
    });
  }

  aplicarFiltroFechas(): void {
    if (!this.fechaInicio || !this.fechaFin) {
      this.error = 'Debe seleccionar ambas fechas';
      return;
    }

    if (new Date(this.fechaInicio) > new Date(this.fechaFin)) {
      this.error = 'La fecha de inicio debe ser anterior a la fecha de fin';
      return;
    }

    this.cargarInformes();
  }

  toggleExpandirComunidad(comunidadId: number): void {
    if (this.comunidadesExpandidas.has(comunidadId)) {
      this.comunidadesExpandidas.delete(comunidadId);
    } else {
      this.comunidadesExpandidas.add(comunidadId);
    }
  }

  estaExpandida(comunidadId: number): boolean {
    return this.comunidadesExpandidas.has(comunidadId);
  }

  descargarInforme(formato: string): void {
    this.loading = true;
    this.error = '';

    const extension = this.getExtensionDescarga(formato);
    if (this.tabActiva === 'comunidades') {
      this.apiService.exportarInformesComunidades(formato, this.fechaInicio, this.fechaFin).subscribe({
        next: (blob) => {
          const url = window.URL.createObjectURL(blob);
          const link = document.createElement('a');
          link.href = url;
          
          const fechaInicioStr = this.fechaInicio.replace(/-/g, '');
          const fechaFinStr = this.fechaFin.replace(/-/g, '');
          
          link.download = `informes_comunidades_${fechaInicioStr}_${fechaFinStr}.${extension}`;
          document.body.appendChild(link);
          link.click();
          document.body.removeChild(link);
          window.URL.revokeObjectURL(url);
          
          this.loading = false;
        },
        error: (err) => {
          this.error = err.error?.message || 'Error al descargar el informe';
          this.loading = false;
        }
      });
    } else {
      this.apiService.exportarInformesProveedores(formato, this.fechaInicio, this.fechaFin).subscribe({
        next: (blob) => {
          const url = window.URL.createObjectURL(blob);
          const link = document.createElement('a');
          link.href = url;
          
          const fechaInicioStr = this.fechaInicio.replace(/-/g, '');
          const fechaFinStr = this.fechaFin.replace(/-/g, '');
          
          link.download = `informes_proveedores_${fechaInicioStr}_${fechaFinStr}.${extension}`;
          document.body.appendChild(link);
          link.click();
          document.body.removeChild(link);
          window.URL.revokeObjectURL(url);
          
          this.loading = false;
        },
        error: (err) => {
          this.error = err.error?.message || 'Error al descargar el informe';
          this.loading = false;
        }
      });
    }
  }

  private getExtensionDescarga(formato: string): string {
    const f = (formato || '').toLowerCase();
    if (f === 'excel') return 'xlsx';
    if (f === 'pdf') return 'pdf';
    return 'csv';
  }

  toggleMenuUsuario(): void {
    this.mostrarMenuUsuario = !this.mostrarMenuUsuario;
  }

  logout(): void {
    this.authService.logout();
  }

  cambiarAModuloTransportes(): void {
    this.router.navigate(['/vehiculos']);
  }

  irAUsuarios(): void {
    this.router.navigate(['/usuarios']);
  }

  formatearMoneda(valor: number): string {
    return new Intl.NumberFormat('es-ES', {
      style: 'currency',
      currency: 'EUR'
    }).format(valor);
  }

  formatearFecha(fechaStr: string): string {
    if (!fechaStr) return '';
    const fecha = new Date(fechaStr);
    const dia = String(fecha.getDate()).padStart(2, '0');
    const mes = String(fecha.getMonth() + 1).padStart(2, '0');
    const año = fecha.getFullYear();
    return `${dia}/${mes}/${año}`;
  }

  getEstadosArray(estadosObj: any): any[] {
    if (!estadosObj) return [];
    return Object.keys(estadosObj).map(key => ({
      key: key,
      value: estadosObj[key]
    }));
  }

  getEstadoLabel(estado: string): string {
    const labels: { [key: string]: string } = {
      'abierta': 'Abierta',
      'asignada': 'Asignada',
      'en_progreso': 'En Progreso',
      'resuelta': 'Resuelta',
      'cerrada': 'Cerrada'
    };
    return labels[estado] || estado;
  }

  tieneIncidenciasPorEstado(incidenciasPorEstado: any): boolean {
    if (!incidenciasPorEstado) return false;
    return Object.keys(incidenciasPorEstado).length > 0;
  }
}
