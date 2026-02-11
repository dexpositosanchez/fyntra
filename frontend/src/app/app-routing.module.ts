import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';
import { LoginComponent } from './components/login/login.component';
import { ModuloSelectorComponent } from './components/modulo-selector/modulo-selector.component';
import { IncidenciasComponent } from './components/incidencias/incidencias.component';
import { VehiculosComponent } from './components/vehiculos/vehiculos.component';
import { ConductoresComponent } from './components/conductores/conductores.component';
import { PedidosComponent } from './components/pedidos/pedidos.component';
import { RutasComponent } from './components/rutas/rutas.component';
import { MantenimientosComponent } from './components/mantenimientos/mantenimientos.component';
import { ComunidadesComponent } from './components/comunidades/comunidades.component';
import { InmueblesComponent } from './components/inmuebles/inmuebles.component';
import { PropietariosComponent } from './components/propietarios/propietarios.component';
import { ProveedoresComponent } from './components/proveedores/proveedores.component';
import { UsuariosComponent } from './components/usuarios/usuarios.component';
import { InformesComponent } from './components/informes/informes.component';
import { HistorialComponent } from './components/historial/historial.component';
import { AuthGuard } from './guards/auth.guard';
import { AdminFincasGuard } from './guards/admin-fincas.guard';
import { AdminTransportesGuard } from './guards/admin-transportes.guard';
import { AccesoFincasGuard } from './guards/acceso-fincas.guard';
import { ModuloSelectorGuard } from './guards/modulo-selector.guard';
import { AdminOnlyGuard } from './guards/admin-only.guard';
import { SuperAdminGuard } from './guards/super-admin.guard';

const routes: Routes = [
  { path: '', redirectTo: '/login', pathMatch: 'full' },
  { path: 'login', component: LoginComponent },
  { path: 'modulos', component: ModuloSelectorComponent, canActivate: [ModuloSelectorGuard] },
  { path: 'incidencias', component: IncidenciasComponent, canActivate: [AccesoFincasGuard] },
  { path: 'comunidades', component: ComunidadesComponent, canActivate: [AdminFincasGuard] },
  { path: 'inmuebles', component: InmueblesComponent, canActivate: [AccesoFincasGuard] },
  { path: 'propietarios', component: PropietariosComponent, canActivate: [AdminFincasGuard] },
  { path: 'proveedores', component: ProveedoresComponent, canActivate: [AdminFincasGuard] },
  { path: 'informes', component: InformesComponent, canActivate: [AdminOnlyGuard] },
  { path: 'usuarios', component: UsuariosComponent, canActivate: [SuperAdminGuard] },
  { path: 'vehiculos', component: VehiculosComponent, canActivate: [AdminTransportesGuard] },
  { path: 'conductores', component: ConductoresComponent, canActivate: [AdminTransportesGuard] },
  { path: 'mantenimientos', component: MantenimientosComponent, canActivate: [AdminTransportesGuard] },
  { path: 'rutas', component: RutasComponent, canActivate: [AdminTransportesGuard] },
  { path: 'pedidos', component: PedidosComponent, canActivate: [AdminTransportesGuard] },
  { path: 'historial', component: HistorialComponent, canActivate: [AdminTransportesGuard] },
  { path: '**', redirectTo: '/login' }
];

@NgModule({
  imports: [RouterModule.forRoot(routes)],
  exports: [RouterModule]
})
export class AppRoutingModule { }

