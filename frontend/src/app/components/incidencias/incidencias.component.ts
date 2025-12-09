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
  loading: boolean = false;
  error: string = '';
  filtroFecha: string = '';
  filtroPrioridad: string = '';
  currentRoute: string = '';
  mostrarMenuUsuario: boolean = false;
  usuario: any = null;
  private routerSubscription?: Subscription;

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
    this.apiService.getIncidenciasSinResolver().subscribe({
      next: (data) => {
        this.incidencias = data;
        this.loading = false;
      },
      error: (err) => {
        this.error = 'Error al cargar incidencias';
        this.loading = false;
        // Datos de prueba si no hay conexión
        this.incidencias = [
          {
            id: 1,
            prioridad: 'urgente',
            fecha_alta: new Date('2025-11-02'),
            titulo: 'Avería en fontanería'
          },
          {
            id: 2,
            prioridad: 'alta',
            fecha_alta: new Date('2025-11-02'),
            titulo: 'Problema eléctrico'
          },
          {
            id: 3,
            prioridad: 'media',
            fecha_alta: new Date('2025-11-02'),
            titulo: 'Reparación de persiana'
          },
          {
            id: 4,
            prioridad: 'baja',
            fecha_alta: new Date('2025-11-02'),
            titulo: 'Limpieza de fachada'
          }
        ];
        this.loading = false;
      }
    });
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

  verDetalle(id: number): void {
    // Implementar navegación a detalle
    console.log('Ver detalle incidencia:', id);
  }

  resolver(id: number): void {
    // Implementar resolución de incidencia
    console.log('Resolver incidencia:', id);
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

  logout(): void {
    this.mostrarMenuUsuario = false;
    this.authService.logout();
  }
}
