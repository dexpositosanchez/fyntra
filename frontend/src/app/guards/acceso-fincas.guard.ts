import { Injectable } from '@angular/core';
import { Router, CanActivate } from '@angular/router';
import { AuthService } from '../services/auth.service';

/**
 * Guard para rutas del módulo Fincas (incidencias, inmuebles).
 * Permite: super_admin, admin_fincas, propietario, proveedor.
 * Bloquea admin_transportes -> redirige a /vehiculos.
 */
@Injectable({
  providedIn: 'root'
})
export class AccesoFincasGuard implements CanActivate {
  constructor(
    private authService: AuthService,
    private router: Router
  ) {}

  canActivate(): boolean {
    if (!this.authService.isAuthenticated()) {
      this.router.navigate(['/login']);
      return false;
    }

    const usuario = this.authService.getUsuario();
    const rol = usuario?.rol;

    if (rol === 'admin_transportes') {
      this.router.navigate(['/vehiculos']);
      return false;
    }

    const rolesPermitidos = ['super_admin', 'admin_fincas', 'propietario', 'proveedor'];
    if (rolesPermitidos.includes(rol)) {
      return true;
    }

    this.router.navigate(['/login']);
    return false;
  }
}
