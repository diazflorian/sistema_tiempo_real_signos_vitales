"""
════════════════════════════════════════════════════════════════
  SISTEMA DE MONITOREO DE SIGNOS VITALES EN TIEMPO REAL
  Universidad Iberoamericana
  Curso:      TI3521 - Ingeniería de Software en Tiempo Real
  Estudiante: Yohanna Díaz Florián  |  Matrícula: 25-0549
  Profesor:   Joerlyn Mariano Morfe Ureña
════════════════════════════════════════════════════════════════

Planificación: Rate Monotonic Scheduling (RMS)
  T1_ECG   → Período  50ms  | Prioridad 1 (más alta)
  T2_PA    → Período 200ms  | Prioridad 2
  T3_SPO2  → Período 500ms  | Prioridad 3
  T4_TEMP  → Período 2000ms | Prioridad 4 (más baja)

Utilización CPU: U = 45.5% ≤ 75.6% (Liu & Layland) ✓
"""

import threading
import time
import random
import queue
from datetime import datetime

# ──────────────────────────────────────────────────────────────
# CONFIGURACIÓN DE UMBRALES MÉDICOS
# ──────────────────────────────────────────────────────────────
UMBRALES = {
    "ECG":   {"min": 60,   "max": 100,  "unidad": "lpm",  "nombre": "Frec. Cardíaca"},
    "PA":    {"min": 90,   "max": 140,  "unidad": "mmHg", "nombre": "Presión Arterial"},
    "SPO2":  {"min": 95,   "max": 100,  "unidad": "%",    "nombre": "Saturación O₂"},
    "TEMP":  {"min": 36.0, "max": 37.5, "unidad": "°C",   "nombre": "Temperatura"},
}

# Cola de alarmas (simula el canal Redis de alarmas)
cola_alarmas = queue.Queue()

# Contador de alarmas y lock para consola
alarmas_total = 0
lock_consola  = threading.Lock()

# ──────────────────────────────────────────────────────────────
# COLORES ANSI PARA LA CONSOLA
# ──────────────────────────────────────────────────────────────
class Color:
    RESET  = "\033[0m"
    ROJO   = "\033[91m"
    VERDE  = "\033[92m"
    AMARILLO = "\033[93m"
    CYAN   = "\033[96m"
    BLANCO = "\033[97m"
    NEGRITA = "\033[1m"

# ──────────────────────────────────────────────────────────────
# SIMULADORES DE SENSORES
# (5% probabilidad de valor crítico para demostración)
# ──────────────────────────────────────────────────────────────
def simular_ecg():
    if random.random() < 0.05:
        return round(random.choice([
            random.uniform(40, 58),   # Bradicardia
            random.uniform(102, 130)  # Taquicardia
        ]), 1)
    return round(random.uniform(62, 98), 1)

def simular_presion_arterial():
    if random.random() < 0.05:
        return round(random.choice([
            random.uniform(75, 88),   # Hipotensión
            random.uniform(142, 165)  # Hipertensión
        ]), 1)
    return round(random.uniform(92, 138), 1)

def simular_spo2():
    if random.random() < 0.05:
        return round(random.uniform(88, 93), 1)  # Hipoxia
    return round(random.uniform(96, 99.9), 1)

def simular_temperatura():
    if random.random() < 0.05:
        return round(random.choice([
            random.uniform(34.5, 35.8),  # Hipotermia
            random.uniform(37.8, 39.5)   # Fiebre
        ]), 2)
    return round(random.uniform(36.1, 37.4), 2)

SIMULADORES = {
    "ECG":  simular_ecg,
    "PA":   simular_presion_arterial,
    "SPO2": simular_spo2,
    "TEMP": simular_temperatura,
}

# ──────────────────────────────────────────────────────────────
# BROKER PUB/SUB (simula Redis sin necesidad de instalarlo)
# ──────────────────────────────────────────────────────────────
class BrokerPubSub:
    """
    Broker de mensajes en memoria que simula el comportamiento
    de Redis Pub/Sub. Los sensores publican en canales y
    los suscriptores reciben las lecturas en tiempo real.
    """
    def __init__(self):
        self._suscriptores = {}
        self._lock = threading.Lock()

    def suscribir(self, canal, callback):
        with self._lock:
            if canal not in self._suscriptores:
                self._suscriptores[canal] = []
            self._suscriptores[canal].append(callback)

    def publicar(self, canal, mensaje):
        with self._lock:
            callbacks = self._suscriptores.get(canal, [])[:]
        for cb in callbacks:
            threading.Thread(target=cb, args=(canal, mensaje), daemon=True).start()

# Instancia global del broker
broker = BrokerPubSub()

# ──────────────────────────────────────────────────────────────
# TAREA DE SENSOR (Rate Monotonic Scheduling)
# ──────────────────────────────────────────────────────────────
def tarea_sensor(nombre, periodo_seg, canal, tipo, evento_stop):
    """
    Ejecuta una tarea periódica siguiendo Rate Monotonic Scheduling.
    - nombre:      identificador de la tarea (ej: T1_ECG)
    - periodo_seg: período en segundos
    - canal:       canal pub/sub donde publicar
    - tipo:        clave en UMBRALES y SIMULADORES
    - evento_stop: threading.Event para detener la tarea
    """
    global alarmas_total

    while not evento_stop.is_set():
        inicio = time.perf_counter()

        # ── Captura del sensor ──────────────────────────────
        valor     = SIMULADORES[tipo]()
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        umbral    = UMBRALES[tipo]
        es_critico = valor < umbral["min"] or valor > umbral["max"]

        # ── Publicar en broker (simula Redis pub/sub) ───────
        mensaje = {
            "tarea":     nombre,
            "tipo":      tipo,
            "valor":     valor,
            "unidad":    umbral["unidad"],
            "nombre":    umbral["nombre"],
            "timestamp": timestamp,
            "critico":   es_critico,
        }
        broker.publicar(canal, mensaje)

        # ── Si es crítico → publicar alarma ─────────────────
        if es_critico:
            tipo_alarma = "BAJO ↓" if valor < umbral["min"] else "ALTO ↑"
            alarma = {
                "tarea":      nombre,
                "nombre":     umbral["nombre"],
                "valor":      valor,
                "unidad":     umbral["unidad"],
                "tipo":       tipo_alarma,
                "rango":      f"[{umbral['min']} – {umbral['max']}]",
                "timestamp":  timestamp,
            }
            broker.publicar("ALARMAS", alarma)
            alarmas_total += 1

        # ── Esperar hasta el siguiente período ───────────────
        transcurrido = time.perf_counter() - inicio
        espera = periodo_seg - transcurrido
        if espera > 0:
            evento_stop.wait(timeout=espera)

# ──────────────────────────────────────────────────────────────
# CALLBACKS DE SUSCRIPTORES (reciben y muestran las lecturas)
# ──────────────────────────────────────────────────────────────
def mostrar_lectura(canal, mensaje):
    """Muestra en consola la lectura de cada sensor (excepto ECG, muy frecuente)."""
    if mensaje["tarea"] == "T1_ECG":
        return  # ECG cada 50ms saturaria la pantalla

    with lock_consola:
        if mensaje["critico"]:
            color = Color.ROJO
            estado = "⚠  CRITICO"
        else:
            color = Color.VERDE
            estado = "✓  NORMAL "

        print(
            f"  {color}[{mensaje['timestamp']}]  "
            f"{mensaje['tarea']:<10}  "
            f"{mensaje['nombre']:<18}  "
            f"{mensaje['valor']:>7.2f} {mensaje['unidad']:<5}  "
            f"{estado}{Color.RESET}"
        )

def mostrar_alarma(canal, mensaje):
    """Muestra una alarma crítica con formato destacado."""
    with lock_consola:
        print(f"\n  {Color.ROJO}{Color.NEGRITA}"
              f"🚨 ALARMA [{mensaje['timestamp']}]  "
              f"{mensaje['nombre']}: {mensaje['valor']:.2f} {mensaje['unidad']}  "
              f"({mensaje['tipo']})  Rango normal: {mensaje['rango']}"
              f"{Color.RESET}\n")

# ──────────────────────────────────────────────────────────────
# REPORTE DE ESTADO DEL SISTEMA (cada 10 segundos)
# ──────────────────────────────────────────────────────────────
def reporte_estado(evento_stop):
    while not evento_stop.is_set():
        evento_stop.wait(timeout=10)
        if evento_stop.is_set():
            break
        with lock_consola:
            print(f"\n  {Color.CYAN}"
                  f"── Estado [{datetime.now().strftime('%H:%M:%S')}] ─────────────────────────────────────────\n"
                  f"     Tareas: T1_ECG(50ms) T2_PA(200ms) T3_SPO2(500ms) T4_TEMP(2000ms)\n"
                  f"     Utilización CPU: 45.5%  |  Alarmas generadas: {alarmas_total}\n"
                  f"  ──────────────────────────────────────────────────────────────────"
                  f"{Color.RESET}\n")

# ──────────────────────────────────────────────────────────────
# PROGRAMA PRINCIPAL
# ──────────────────────────────────────────────────────────────
def main():
    print(f"\n{Color.CYAN}{Color.NEGRITA}")
    print("  ╔══════════════════════════════════════════════════════════════╗")
    print("  ║   SISTEMA DE MONITOREO DE SIGNOS VITALES - UCI              ║")
    print("  ║   Universidad Iberoamericana | TI3521 Tiempo Real           ║")
    print("  ║   Estudiante: Yohanna Díaz Florián  |  Mat: 25-0549         ║")
    print("  ╚══════════════════════════════════════════════════════════════╝")
    print(Color.RESET)

    print(f"  {Color.AMARILLO}Planificación: Rate Monotonic Scheduling (RMS){Color.RESET}")
    print(f"  Utilización CPU: U = (15/50)+(20/200)+(25/500)+(10/2000) = {Color.VERDE}45.5% ✓{Color.RESET}")
    print(f"  Condición Liu & Layland (n=4): 45.5% ≤ 75.6% → {Color.VERDE}SISTEMA PLANIFICABLE{Color.RESET}\n")

    print(f"  {Color.AMARILLO}Canales activos:{Color.RESET}")
    print("   • SignosVitales:ECG            (cada  50ms - Prioridad 1)")
    print("   • SignosVitales:PresionArterial(cada 200ms - Prioridad 2)")
    print("   • SignosVitales:SpO2           (cada 500ms - Prioridad 3)")
    print("   • SignosVitales:Temperatura    (cada 2000ms- Prioridad 4)")
    print()

    input(f"  {Color.BLANCO}Presiona ENTER para iniciar el monitoreo...{Color.RESET}")
    print()

    # Suscribir callbacks al broker
    for canal in ["SignosVitales:ECG", "SignosVitales:PA",
                  "SignosVitales:SPO2", "SignosVitales:TEMP"]:
        broker.suscribir(canal, mostrar_lectura)
    broker.suscribir("ALARMAS", mostrar_alarma)

    # Evento de parada compartido entre hilos
    evento_stop = threading.Event()

    # Definición de tareas según RMS
    # (nombre, periodo_seg, canal, tipo_sensor)
    tareas_config = [
        ("T1_ECG",  0.050, "SignosVitales:ECG",  "ECG"),
        ("T2_PA",   0.200, "SignosVitales:PA",   "PA"),
        ("T3_SPO2", 0.500, "SignosVitales:SPO2", "SPO2"),
        ("T4_TEMP", 2.000, "SignosVitales:TEMP", "TEMP"),
    ]

    hilos = []

    # Lanzar tareas de sensores
    for nombre, periodo, canal, tipo in tareas_config:
        hilo = threading.Thread(
            target=tarea_sensor,
            args=(nombre, periodo, canal, tipo, evento_stop),
            name=nombre,
            daemon=True
        )
        hilo.start()
        hilos.append(hilo)

    # Lanzar reporte de estado
    hilo_reporte = threading.Thread(
        target=reporte_estado, args=(evento_stop,), daemon=True
    )
    hilo_reporte.start()

    print(f"  {Color.VERDE}✓ Monitoreo iniciado. Presiona Ctrl+C para detener.{Color.RESET}\n")
    print(f"  {'─'*70}")
    print(f"  {'Timestamp':<16} {'Tarea':<10} {'Signo Vital':<18} {'Valor':<13} Estado")
    print(f"  {'─'*70}\n")

    try:
        while True:
            time.sleep(0.1)
    except KeyboardInterrupt:
        pass

    # Detener todos los hilos
    evento_stop.set()
    for h in hilos:
        h.join(timeout=2)

    print(f"\n\n  {Color.AMARILLO}{'─'*70}")
    print(f"  RESUMEN FINAL")
    print(f"  {'─'*70}")
    print(f"  Total de alarmas generadas: {alarmas_total}")
    print(f"  Sistema detenido correctamente.")
    print(f"  {'─'*70}{Color.RESET}\n")


if __name__ == "__main__":
    main()
