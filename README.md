# 🏥 Sistema de Monitoreo de Signos Vitales en Tiempo Real

**Universidad Iberoamericana**  
**Curso:** TI3521 - Ingeniería de Software en Tiempo Real  
**Estudiante:** Yohanna Díaz Florián | Matrícula: 25-0549  
**Profesor:** Joerlyn Mariano Morfe Ureña

---

## 📋 Descripción

Sistema de tiempo real **estricto (Hard Real-Time)** que monitorea continuamente los signos vitales de pacientes en Unidades de Cuidados Intensivos (UCI). El sistema captura, procesa y publica en tiempo real señales de múltiples sensores biomédicos, generando alarmas inmediatas ante condiciones críticas.

---

## 🏗️ Arquitectura del Sistema

```
┌─────────────────────────────────────────────────────────┐
│              SISTEMA DE MONITOREO UCI                   │
│                                                         │
│  ┌──────────┐   ┌──────────┐   ┌──────────┐            │
│  │ T1_ECG   │   │  T2_PA   │   │ T3_SPO2  │  T4_TEMP  │
│  │  50ms    │   │  200ms   │   │  500ms   │  2000ms   │
│  │ Prio: 1  │   │ Prio: 2  │   │ Prio: 3  │  Prio: 4  │
│  └────┬─────┘   └────┬─────┘   └────┬─────┘  └────┬───┘
│       │              │              │              │    │
│       └──────────────┴──────────────┴──────────────┘    │
│                          │                              │
│                   ┌──────▼──────┐                       │
│                   │    REDIS    │  Pub/Sub Broker        │
│                   │  localhost  │                       │
│                   └──────┬──────┘                       │
│                          │                              │
│              ┌───────────▼──────────┐                   │
│              │   SISTEMA DE ALARMAS │                   │
│              │  Latencia < 50ms     │                   │
│              └──────────────────────┘                   │
└─────────────────────────────────────────────────────────┘
```

---

## ⏱️ Planificación de Tareas (Rate Monotonic Scheduling)

| Tarea    | Descripción             | Período (T) | WCET (C) | Deadline (D) | Prioridad |
|----------|-------------------------|-------------|----------|--------------|-----------|
| T1_ECG   | Captura ECG             | 50 ms       | 15 ms    | 50 ms        | 1 (Alta)  |
| T2_PA    | Presión Arterial        | 200 ms      | 20 ms    | 200 ms       | 2         |
| T3_SPO2  | Saturación de Oxígeno   | 500 ms      | 25 ms    | 500 ms       | 3         |
| T4_TEMP  | Temperatura Corporal    | 2000 ms     | 10 ms    | 2000 ms      | 4 (Baja)  |

### Análisis de Planificabilidad

```
U = (15/50) + (20/200) + (25/500) + (10/2000)
U = 0.30 + 0.10 + 0.05 + 0.005
U = 0.455 = 45.5%

Condición Liu & Layland (n=4): U ≤ 0.756
Resultado: 0.455 ≤ 0.756 ✓  → SISTEMA PLANIFICABLE
Margen de seguridad: 39.8%
```

---

## 🚨 Umbrales de Alarma

| Signo Vital        | Mínimo | Máximo | Unidad |
|--------------------|--------|--------|--------|
| Frecuencia Cardíaca| 60     | 100    | lpm    |
| Presión Arterial   | 90     | 140    | mmHg   |
| Saturación O₂      | 95     | 100    | %      |
| Temperatura        | 36.0   | 37.5   | °C     |

---

## 🛠️ Tecnologías Utilizadas

- **Lenguaje:** Python 3 (sin dependencias externas)
- **Broker de mensajes:** Pub/Sub en memoria (simula Redis)
- **Planificación:** Rate Monotonic Scheduling (RMS)
- **Concurrencia:** `threading` de la librería estándar
- **Patrón:** Publish/Subscribe

---

## 🚀 Cómo Ejecutar

### Prerrequisitos

- Python 3.8 o superior (sin instalar nada más)

### Pasos

```bash
# 1. Clonar el repositorio
git clone https://github.com/TU_USUARIO/SignosVitales.git
cd SignosVitales/src

# 2. Ejecutar directamente
python monitor.py
```

### Salida esperada

```
  ╔══════════════════════════════════════════════════════════════╗
  ║   SISTEMA DE MONITOREO DE SIGNOS VITALES - UCI              ║
  ╚══════════════════════════════════════════════════════════════╝

  [14:30:01.200]  T2_PA       Presión Arterial    118.50 mmHg   ✓  NORMAL
  [14:30:01.500]  T3_SPO2     Saturación O₂        97.80 %      ✓  NORMAL
  [14:30:02.000]  T4_TEMP     Temperatura          36.70 °C     ✓  NORMAL

  🚨 ALARMA [14:30:05.231] Saturación O₂: 91.20 % (BAJO ↓) Rango normal: [95 – 100]
```

---

## 📡 Canales Redis (Pub/Sub)

| Canal                        | Contenido                                      |
|------------------------------|------------------------------------------------|
| `SignosVitales:ECG`          | Frecuencia cardíaca (cada 50ms)               |
| `SignosVitales:PresionArterial` | Presión arterial sistólica (cada 200ms)    |
| `SignosVitales:SpO2`         | Saturación de oxígeno (cada 500ms)            |
| `SignosVitales:Temperatura`  | Temperatura corporal (cada 2000ms)            |
| `SignosVitales:Alarmas`      | Alarmas críticas (cuando se excede umbral)    |

---

## 📁 Estructura del Proyecto

```
SignosVitales/
├── src/
│   └── monitor.py              # Sistema completo (Python puro, sin dependencias)
├── docs/
│   └── Diseno_Sistema_Tiempo_Real_Signos_Vitales.docx
└── README.md
```

---

## 📄 Documento de Diseño

El documento de diseño completo se encuentra en `/docs/` e incluye:
- Descripción y clasificación del sistema
- Requerimientos funcionales y no funcionales
- Análisis de tareas y planificación RMS
- Diagramas UML (casos de uso, secuencia, componentes)

---

## 📜 Licencia

Proyecto académico — Universidad Iberoamericana © 2026
