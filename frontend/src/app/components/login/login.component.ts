import { Component } from '@angular/core';
import { Router } from '@angular/router';
import { AuthService } from '../../services/auth.service';

@Component({
  selector: 'app-login',
  templateUrl: './login.component.html',
  styleUrls: ['./login.component.scss']
})
export class LoginComponent {
  email: string = '';
  password: string = '';
  error: string = '';
  loading: boolean = false;

  constructor(
    private authService: AuthService,
    private router: Router
  ) {}

  onSubmit(): void {
    if (!this.email || !this.password) {
      this.error = 'Por favor, complete todos los campos';
      return;
    }

    this.loading = true;
    this.error = '';

    this.authService.login(this.email, this.password).subscribe({
      next: () => {
        const usuario = this.authService.getUsuario();
        const rol = usuario?.rol;
        if (rol === 'propietario' || rol === 'proveedor') {
          this.router.navigate(['/incidencias']);
        } else if (rol === 'admin_fincas') {
          this.router.navigate(['/incidencias']);
        } else if (rol === 'admin_transportes') {
          this.router.navigate(['/vehiculos']);
        } else if (rol === 'super_admin') {
          this.router.navigate(['/modulos']);
        } else {
          this.router.navigate(['/modulos']);
        }
      },
      error: (err) => {
        this.error = err.error?.detail || 'Error al iniciar sesión';
        this.loading = false;
      }
    });
  }
}

