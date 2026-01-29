import { Injectable } from '@angular/core';
import { Router, CanActivate, ActivatedRouteSnapshot, RouterStateSnapshot } from '@angular/router';
import { AuthService } from '../services/auth.service';

const ROLES_ADMIN = ['super_admin', 'admin_fincas', 'admin_transportes'];

@Injectable({
  providedIn: 'root'
})
export class AdminOnlyGuard implements CanActivate {
  constructor(
    private authService: AuthService,
    private router: Router
  ) {}

  canActivate(
    route: ActivatedRouteSnapshot,
    state: RouterStateSnapshot
  ): boolean {
    if (!this.authService.isAuthenticated()) {
      this.router.navigate(['/login']);
      return false;
    }

    const usuario = this.authService.getUsuario();
    if (!usuario || !ROLES_ADMIN.includes(usuario.rol)) {
      this.router.navigate(['/modulos']);
      return false;
    }

    return true;
  }
}
