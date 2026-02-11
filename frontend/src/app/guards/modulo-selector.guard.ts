import { Injectable } from '@angular/core';
import { Router, CanActivate } from '@angular/router';
import { AuthService } from '../services/auth.service';

/**
 * Solo el super_admin puede acceder al selector de módulos.
 * admin_fincas y admin_transportes van directamente a su módulo (ver login).
 */
@Injectable({
  providedIn: 'root'
})
export class ModuloSelectorGuard implements CanActivate {
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

    if (rol === 'super_admin') {
      return true;
    }
    if (rol === 'admin_fincas') {
      this.router.navigate(['/incidencias']);
      return false;
    }
    if (rol === 'admin_transportes') {
      this.router.navigate(['/vehiculos']);
      return false;
    }
    if (rol === 'propietario' || rol === 'proveedor') {
      this.router.navigate(['/incidencias']);
      return false;
    }

    this.router.navigate(['/login']);
    return false;
  }
}
