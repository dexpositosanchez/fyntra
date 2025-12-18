import { NgModule, LOCALE_ID } from '@angular/core';
import { BrowserModule } from '@angular/platform-browser';
import { BrowserAnimationsModule } from '@angular/platform-browser/animations';
import { HttpClientModule } from '@angular/common/http';
import { FormsModule } from '@angular/forms';
import { RouterModule } from '@angular/router';
import { registerLocaleData } from '@angular/common';
import localeEs from '@angular/common/locales/es';
import { AppComponent } from './app.component';
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
import { AppRoutingModule } from './app-routing.module';

@NgModule({
  declarations: [
    AppComponent,
    LoginComponent,
    ModuloSelectorComponent,
    IncidenciasComponent,
    VehiculosComponent,
    ConductoresComponent,
    PedidosComponent,
    RutasComponent,
    MantenimientosComponent,
    ComunidadesComponent,
    InmueblesComponent,
    PropietariosComponent
  ],
  imports: [
    BrowserModule,
    BrowserAnimationsModule,
    HttpClientModule,
    FormsModule,
    RouterModule,
    AppRoutingModule
  ],
  providers: [
    { provide: LOCALE_ID, useValue: 'es-ES' }
  ],
  bootstrap: [AppComponent]
})
export class AppModule { }

// Registrar configuración regional española para pipes de fecha/número
registerLocaleData(localeEs);

