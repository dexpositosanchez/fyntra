import { Component } from '@angular/core';
import { Router } from '@angular/router';
import { AuthService } from '../../services/auth.service';
import { ApiService } from '../../services/api.service';

@Component({
  selector: 'app-modulo-selector',
  templateUrl: './modulo-selector.component.html',
  styleUrls: ['./modulo-selector.component.scss']
})
export class ModuloSelectorComponent {
  usuario: any;
  mensajeRGPD: string = '';
  errorRGPD: string = '';
  exportando: boolean = false;
  eliminando: boolean = false;

  constructor(
    private router: Router,
    private authService: AuthService,
    private apiService: ApiService
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

  /** RGPD: Exportar mis datos (Art. 15 y 20) */
  exportarMisDatos(): void {
    this.mensajeRGPD = '';
    this.errorRGPD = '';
    this.exportando = true;
    this.apiService.getMisDatos().subscribe({
      next: (datos) => {
        const blob = new Blob([JSON.stringify(datos, null, 2)], { type: 'application/json' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `mis-datos-${this.usuario?.email?.replace('@', '-at-') || 'usuario'}-${new Date().toISOString().slice(0, 10)}.json`;
        a.click();
        window.URL.revokeObjectURL(url);
        this.mensajeRGPD = 'Datos exportados correctamente. Se ha descargado el archivo JSON.';
        this.exportando = false;
      },
      error: (err) => {
        this.errorRGPD = err.error?.detail || 'Error al exportar los datos.';
        this.exportando = false;
      }
    });
  }

  /** RGPD: Eliminar mi cuenta (Art. 17) */
  eliminarMiCuenta(): void {
    this.mensajeRGPD = '';
    this.errorRGPD = '';
    const confirmar = confirm(
      '¿Está seguro de que desea eliminar su cuenta? Se anonimizarán sus datos personales y no podrá volver a iniciar sesión. Esta acción no se puede deshacer.'
    );
    if (!confirmar) return;
    const password = prompt('Opcional: introduzca su contraseña para confirmar (o deje en blanco):');
    this.eliminando = true;
    this.apiService.eliminarMiCuenta(password || undefined).subscribe({
      next: () => {
        this.eliminando = false;
        this.authService.logout();
        this.router.navigate(['/login']);
      },
      error: (err) => {
        this.errorRGPD = err.error?.detail || 'Error al eliminar la cuenta.';
        this.eliminando = false;
      }
    });
  }
}

