import { Component } from '@angular/core';
import { Router } from '@angular/router';
import { AuthService } from '../../services/auth.service';

@Component({
  selector: 'app-modulo-selector',
  templateUrl: './modulo-selector.component.html',
  styleUrls: ['./modulo-selector.component.scss']
})
export class ModuloSelectorComponent {
  usuario: any;

  constructor(
    private router: Router,
    private authService: AuthService
  ) {
    this.usuario = this.authService.getUsuario();
  }

  seleccionarModulo(modulo: string): void {
    if (modulo === 'fincas') {
      this.router.navigate(['/incidencias']);
    } else if (modulo === 'transportes') {
      this.router.navigate(['/vehiculos']);
    }
  }

  irAUsuarios(): void {
    this.router.navigate(['/usuarios']);
  }

  logout(): void {
    this.authService.logout();
  }
}

