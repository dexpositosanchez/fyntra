import { Injectable } from '@angular/core';
import { Router, CanActivate } from '@angular/router';
import { AuthService } from '../services/auth.service';

/**
 * Solo super_admin y admin_transportes pueden acceder a rutas del módulo Transportes.
 * admin_fincas, propietario y proveedor son redirigidos a incidencias.
 */
@Injectable({
  providedIn: 'root'
})
export class AdminTransportesGuard implements CanActivate {
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

    if (rol === 'super_admin' || rol === 'admin_transportes') {
      return true;
    }

    this.router.navigate(['/incidencias']);
    return false;
  }
}
