import { NgModule } from '@angular/core';
import { BrowserModule } from '@angular/platform-browser';
import { BrowserAnimationsModule } from '@angular/platform-browser/animations';
import { HttpClientModule } from '@angular/common/http';
import { FormsModule } from '@angular/forms';
import { RouterModule } from '@angular/router';
import { AppComponent } from './app.component';
import { LoginComponent } from './components/login/login.component';
import { ModuloSelectorComponent } from './components/modulo-selector/modulo-selector.component';
import { IncidenciasComponent } from './components/incidencias/incidencias.component';
import { VehiculosComponent } from './components/vehiculos/vehiculos.component';
import { ConductoresComponent } from './components/conductores/conductores.component';
import { AppRoutingModule } from './app-routing.module';

@NgModule({
  declarations: [
    AppComponent,
    LoginComponent,
    ModuloSelectorComponent,
    IncidenciasComponent,
    VehiculosComponent,
    ConductoresComponent
  ],
  imports: [
    BrowserModule,
    BrowserAnimationsModule,
    HttpClientModule,
    FormsModule,
    RouterModule,
    AppRoutingModule
  ],
  providers: [],
  bootstrap: [AppComponent]
})
export class AppModule { }

