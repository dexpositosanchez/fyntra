import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';
import { LoginComponent } from './components/login/login.component';
import { ModuloSelectorComponent } from './components/modulo-selector/modulo-selector.component';
import { IncidenciasComponent } from './components/incidencias/incidencias.component';
import { VehiculosComponent } from './components/vehiculos/vehiculos.component';
import { ConductoresComponent } from './components/conductores/conductores.component';
import { PedidosComponent } from './components/pedidos/pedidos.component';
import { RutasComponent } from './components/rutas/rutas.component';
import { AuthGuard } from './guards/auth.guard';

const routes: Routes = [
  { path: '', redirectTo: '/login', pathMatch: 'full' },
  { path: 'login', component: LoginComponent },
  { path: 'modulos', component: ModuloSelectorComponent, canActivate: [AuthGuard] },
  { path: 'incidencias', component: IncidenciasComponent, canActivate: [AuthGuard] },
  { path: 'vehiculos', component: VehiculosComponent, canActivate: [AuthGuard] },
  { path: 'propietarios', component: IncidenciasComponent, canActivate: [AuthGuard] },
  { path: 'propiedades', component: IncidenciasComponent, canActivate: [AuthGuard] },
  { path: 'comunidades', component: IncidenciasComponent, canActivate: [AuthGuard] },
  { path: 'proveedores', component: IncidenciasComponent, canActivate: [AuthGuard] },
  { path: 'conductores', component: ConductoresComponent, canActivate: [AuthGuard] },
  { path: 'rutas', component: RutasComponent, canActivate: [AuthGuard] },
  { path: 'pedidos', component: PedidosComponent, canActivate: [AuthGuard] },
  { path: '**', redirectTo: '/login' }
];

@NgModule({
  imports: [RouterModule.forRoot(routes)],
  exports: [RouterModule]
})
export class AppRoutingModule { }

