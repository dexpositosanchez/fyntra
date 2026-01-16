#!/usr/bin/env python3
"""
Script de prueba de carga para verificar el cumplimiento del RNF1
RNF1: El sistema debe responder en menos de 2 segundos en el 95% de los casos
      con 100 usuarios concurrentes.

Uso:
    python load_test.py --host http://localhost:8000 --users 100 --spawn-rate 10

Requisitos:
    pip install locust
"""

import argparse
import json
import os
from locust import HttpUser, task, between, events
from locust.contrib.fasthttp import FastHttpUser
import time

# Variables globales para almacenar estadísticas
response_times = []

# Credenciales configurables mediante variables de entorno
TEST_EMAIL = os.getenv("TEST_EMAIL", "admin@fyntra.com")
TEST_PASSWORD = os.getenv("TEST_PASSWORD", "admin123")


class FyntraUser(FastHttpUser):
    """Usuario simulado para pruebas de carga"""
    wait_time = between(1, 3)  # Espera entre 1 y 3 segundos entre peticiones
    
    def on_start(self):
        """Se ejecuta al iniciar cada usuario simulado"""
        # Login y guardar token
        login_data = {
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        }
        
        try:
            response = self.client.post("/api/auth/login", json=login_data)
            if response.status_code == 200:
                self.token = response.json()["access_token"]
            else:
                print(f"Error en login: {response.status_code} - {response.text}")
                self.token = None
        except Exception as e:
            print(f"Error al hacer login: {e}")
            self.token = None
    
    def _get_headers(self):
        """Obtener headers con autenticación"""
        headers = {}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers
    
    @task(3)
    def list_incidencias(self):
        """Listar incidencias - operación frecuente"""
        if self.token:
            self.client.get(
                "/api/incidencias/?skip=0&limit=100",
                headers=self._get_headers()
            )
    
    @task(2)
    def list_vehiculos(self):
        """Listar vehículos - operación frecuente"""
        if self.token:
            self.client.get(
                "/api/vehiculos/?skip=0&limit=100",
                headers=self._get_headers()
            )
    
    @task(2)
    def list_rutas(self):
        """Listar rutas - operación frecuente"""
        if self.token:
            self.client.get(
                "/api/rutas/?skip=0&limit=100",
                headers=self._get_headers()
            )
    
    @task(1)
    def list_pedidos(self):
        """Listar pedidos - operación frecuente"""
        if self.token:
            self.client.get(
                "/api/pedidos/?skip=0&limit=100",
                headers=self._get_headers()
            )
    
    @task(1)
    def list_mantenimientos(self):
        """Listar mantenimientos - operación frecuente"""
        if self.token:
            self.client.get(
                "/api/mantenimientos/?skip=0&limit=100",
                headers=self._get_headers()
            )
    
    @task(1)
    def get_single_incidencia(self):
        """Obtener una incidencia específica"""
        if self.token:
            # Asumiendo que existe una incidencia con ID 1
            self.client.get(
                "/api/incidencias/1",
                headers=self._get_headers()
            )


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Se ejecuta al finalizar la prueba"""
    print("\n" + "="*60)
    print("RESUMEN DE PRUEBA DE CARGA")
    print("="*60)
    
    stats = environment.stats
    total_requests = stats.total.num_requests
    
    if total_requests > 0:
        # Obtener percentil 95 del total agregado
        # Locust calcula percentiles automáticamente, usar el del total agregado
        percentile_95 = stats.total.get_response_time_percentile(0.95)
        
        print(f"\nTotal de peticiones: {total_requests}")
        print(f"Tiempo de respuesta promedio: {stats.total.avg_response_time:.2f} ms")
        print(f"Tiempo de respuesta mediano: {stats.total.median_response_time:.2f} ms")
        print(f"Percentil 95: {percentile_95:.2f} ms")
        print(f"Tiempo máximo: {stats.total.max_response_time:.2f} ms")
        print(f"Tasa de errores: {(stats.total.num_failures / total_requests * 100):.2f}%")
        
        # Verificar cumplimiento del RNF1
        print("\n" + "-"*60)
        print("VERIFICACIÓN RNF1:")
        print("-"*60)
        rnf1_requirement = 2000  # 2 segundos en milisegundos
        
        if percentile_95 < rnf1_requirement:
            print(f"✅ CUMPLE RNF1: Percentil 95 ({percentile_95:.2f} ms) < {rnf1_requirement} ms")
        else:
            print(f"❌ NO CUMPLE RNF1: Percentil 95 ({percentile_95:.2f} ms) >= {rnf1_requirement} ms")
        
        if stats.total.num_failures == 0:
            print("✅ Sin errores en las peticiones")
        else:
            print(f"⚠️  {stats.total.num_failures} peticiones fallaron ({stats.total.num_failures / total_requests * 100:.2f}%)")
        
        # Mostrar desglose por endpoint
        print("\n" + "-"*60)
        print("DESGLOSE POR ENDPOINT:")
        print("-"*60)
        for name, entry in sorted(stats.entries.items()):
            if entry.num_requests > 0:
                p95 = entry.get_response_time_percentile(0.95)
                status = "✅" if p95 < rnf1_requirement else "⚠️"
                print(f"{status} {name}: {entry.num_requests} reqs, P95: {p95:.2f} ms, Errores: {entry.num_failures}")
    
    print("="*60)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Prueba de carga para Fyntra API")
    parser.add_argument("--host", default="http://localhost:8000", help="URL del servidor")
    parser.add_argument("--users", type=int, default=100, help="Número de usuarios concurrentes")
    parser.add_argument("--spawn-rate", type=int, default=10, help="Tasa de creación de usuarios por segundo")
    parser.add_argument("--run-time", default="5m", help="Tiempo de ejecución (ej: 5m, 1h)")
    
    args = parser.parse_args()
    
    print(f"Iniciando prueba de carga:")
    print(f"  Host: {args.host}")
    print(f"  Usuarios concurrentes: {args.users}")
    print(f"  Tasa de creación: {args.spawn_rate} usuarios/segundo")
    print(f"  Tiempo de ejecución: {args.run_time}")
    print("\nPara ejecutar con interfaz web, usar:")
    print(f"  locust -f load_test.py --host {args.host}")
    print("\nO ejecutar directamente:")
    print(f"  locust -f load_test.py --host {args.host} --users {args.users} --spawn-rate {args.spawn_rate} --run-time {args.run_time} --headless")
