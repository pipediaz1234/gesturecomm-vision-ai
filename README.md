# GestureConnect — Sistema Inteligente de Reconocimiento de Gestos para Comunicación Inclusiva

> Sistema de visión por computador en tiempo real que facilita la comunicación entre personas con discapacidad auditiva y establecimientos comerciales, mediante detección de gestos, síntesis de voz y reconocimiento de habla.

---

## Tabla de Contenidos

- [Descripción del Proyecto](#descripción-del-proyecto)
- [Capturas del Sistema](#capturas-del-sistema)
- [Código Fuente](#código-fuente)
- [Demo y Flujo del Sistema](#demo-y-flujo-del-sistema)
- [Arquitectura del Sistema](#arquitectura-del-sistema)
- [Tecnologías Utilizadas](#tecnologías-utilizadas)
- [Instalación](#instalación)
- [Uso del Sistema](#uso-del-sistema)
- [Estructura del Proyecto](#estructura-del-proyecto)
- [Resultados y Validación](#resultados-y-validación)
- [Limitaciones](#limitaciones)
- [Futuras Mejoras](#futuras-mejoras)
- [Autores](#autores)
- [Licencia](#licencia)

---

## Descripción del Proyecto

**GestureConnect** es un sistema inteligente de visión por computador diseñado para facilitar la comunicación entre personas con discapacidad auditiva y proveedores de servicios comerciales. El sistema captura los movimientos de la mano del usuario a través de una cámara estándar, interpreta gestos predefinidos mediante detección de puntos de referencia y los traduce automáticamente en mensajes de voz sintetizados, permitiendo una interacción fluida y sin barreras en entornos comerciales.

Como canal complementario, el sistema integra un módulo de reconocimiento de voz (STT) que permite al vendedor responder verbalmente, con la respuesta hablada convertida en texto visible en pantalla para el usuario con discapacidad auditiva. En conjunto, estos dos canales conforman un ciclo de interacción bidireccional, accesible y completamente en tiempo real.

Este proyecto aborda una brecha crítica en la accesibilidad cotidiana, aplicando técnicas de vanguardia en visión por computador y procesamiento de lenguaje natural a un problema social concreto.

**Capacidades principales:**

- Detección de manos y reconocimiento de gestos en tiempo real mediante MediaPipe
- Traducción automática de gestos a voz mediante TTS
- Comunicación bidireccional a través de STT para las respuestas del vendedor
- Interfaz gráfica interactiva con selección de cantidades mediante gestos
- Control de flujo de interacción basado en máquina de estados

---

## Capturas del Sistema

### Arquitectura visual de la interfaz

<img width="831" height="565" alt="image" src="https://github.com/user-attachments/assets/d3eb9623-c2d3-4c89-a4c3-8550ee0ef3ad" />

---

### Detección de gesto y despliegue de menú en tiempo real

<img width="915" height="529" alt="image" src="https://github.com/user-attachments/assets/eba361c4-a8f6-47cb-aed6-215a4fa36cf6" />

---

### Selección de cantidad mediante gesto con dedo índice

<img width="714" height="378" alt="image" src="https://github.com/user-attachments/assets/d890e464-1d58-4ee7-9c7f-4efacd6b8a2d" />

---

### Panel de cliente — gesto reconocido e historial de conversación

<img width="583" height="713" alt="image" src="https://github.com/user-attachments/assets/23cb74cf-0e0f-4909-acdc-dcd141ff2f93" />

---

### Respuesta del vendedor mostrada en pantalla

<img width="915" height="489" alt="image" src="https://github.com/user-attachments/assets/2a453b01-262d-42b8-bb93-46a4598bbc76" />

---

## Código Fuente

El código principal del sistema se encuentra disponible públicamente en GitHub. Puedes revisar la implementación completa del módulo central directamente en el siguiente enlace:

### [Ver código fuente — `sistema_comunicacion.py`](https://github.com/pipediaz1234/gesturecomm-vision-ai/blob/main/GestureComm2/sistema_comunicacion.py)

> Este archivo contiene la lógica central del sistema: captura de video, detección de manos con MediaPipe, clasificación de gestos, integración TTS/STT y control de la interfaz gráfica.

### [Explorar el repositorio completo en GitHub](https://github.com/pipediaz1234/gesturecomm-vision-ai)

---

## Demo y Flujo del Sistema

El sistema opera a través del siguiente flujo de interacción:

```
[Usuario levanta la mano]
        |
        v
[Cámara captura el fotograma]
        |
        v
[MediaPipe detecta los puntos de referencia de la mano]
        |
        v
[Clasificador identifica el gesto]
        |
        v
[Gesto mapeado a intención / solicitud de producto]
        |
        v
[Motor TTS sintetiza y reproduce audio para el vendedor]
        |
        v
[Vendedor responde verbalmente]
        |
        v
[Módulo STT transcribe la respuesta del vendedor]
        |
        v
[Transcripción mostrada en pantalla para el usuario]
```

**Ejemplo de interacción real:**

1. El usuario realiza el gesto asociado a **"Bebidas"**.
2. El sistema detecta el gesto, lo clasifica y reproduce: *"Quisiera una bebida por favor."*
3. El vendedor responde verbalmente: *"Claro, enseguida."*
4. El sistema captura la voz y muestra en pantalla: **"Claro, enseguida."**
5. El usuario selecciona la cantidad señalando con el dedo índice sobre el número deseado (1 al 5).
6. El sistema sintetiza: *"Cliente eligió: 2 (dos)."*

---

## Arquitectura del Sistema

```
┌──────────────────────────────────────────────────────────────┐
│                        GestureConnect                        │
│                                                              │
│  ┌───────────────┐   ┌──────────────────┐   ┌─────────────┐ │
│  │  Capa Entrada │   │  Capa Procesam.  │   │ Capa Salida │ │
│  │               │   │                  │   │             │ │
│  │  - Cámara     │──►│  - OpenCV        │──►│  - Motor TTS│ │
│  │  - Micrófono  │   │  - MediaPipe     │   │  - GUI (Tk) │ │
│  └───────────────┘   │  - Clasificador  │   │  - Pantalla │ │
│                      │    de Gestos     │   │    de Texto │ │
│                      │  - Motor STT     │   └─────────────┘ │
│                      │  - Máquina de    │                    │
│                      │    Estados       │                    │
│                      └──────────────────┘                    │
└──────────────────────────────────────────────────────────────┘
```

**Módulos principales:**

| Módulo | Responsabilidad |
|---|---|
| `captura` | Adquisición y preprocesamiento de fotogramas con OpenCV |
| `detector_manos` | Extracción de puntos de referencia con MediaPipe Hands |
| `clasificador_gestos` | Reconocimiento de gestos basado en reglas y/o ML |
| `modulo_tts` | Conversión de texto a voz y reproducción de audio |
| `modulo_stt` | Captura de voz y transcripción en tiempo real |
| `maquina_estados` | Control del flujo de interacción y estado de sesión |
| `interfaz_gui` | Interfaz gráfica de usuario basada en Tkinter |

**Diagrama de máquina de estados:**

```
[EN ESPERA] ──► [DETECTANDO] ──► [GESTO RECONOCIDO] ──► [REPRODUCIENDO]
                    │                                          │
                    └──────────────────────────────────────────┘
                         [CAPTURANDO VOZ] ──► [MOSTRANDO RESPUESTA]
                                  │
                                  ▼
                        [SELECCIONANDO NÚMERO]
```

---

## Tecnologías Utilizadas

| Tecnología | Versión | Propósito |
|---|---|---|
| Python | 3.9+ | Lenguaje de programación principal |
| OpenCV | 4.x | Captura de video y preprocesamiento de imágenes |
| MediaPipe | 0.10.x | Detección de puntos de referencia de la mano |
| NumPy | 1.24+ | Operaciones numéricas y procesamiento de arreglos |
| Tkinter | (stdlib) | Interfaz gráfica de usuario |
| SpeechRecognition / Whisper | — | Módulo de voz a texto (STT) |
| pyttsx3 / gTTS | — | Síntesis de texto a voz (TTS) |

---

## Instalación

### Prerrequisitos

- Python 3.9 o superior
- Cámara web (integrada o externa)
- Micrófono
- Sistema operativo: Windows 10+, Ubuntu 20.04+ o macOS 12+

### Configuración paso a paso

**1. Clonar el repositorio**

```bash
git clone https://github.com/pipediaz1234/gesturecomm-vision-ai.git
cd gesturecomm-vision-ai
```

**2. Crear y activar un entorno virtual**

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux / macOS
source venv/bin/activate
```

**3. Instalar dependencias**

```bash
pip install -r requirements.txt
```

**4. Verificar acceso a cámara y micrófono**

Asegúrese de que el sistema operativo otorgue permisos a la aplicación para acceder a la cámara y al micrófono antes de ejecutarla.

**5. Ejecutar la aplicación**

```bash
python GestureComm2/sistema_comunicacion.py
```

### `requirements.txt`

```
opencv-python>=4.7.0
mediapipe>=0.10.0
numpy>=1.24.0
pyttsx3>=2.90
SpeechRecognition>=3.10.0
PyAudio>=0.2.13
```

> **Nota:** En Linux, `PyAudio` puede requerir: `sudo apt-get install portaudio19-dev`

---

## Uso del Sistema

Una vez iniciada la aplicación, se presenta una interfaz gráfica con la transmisión en vivo de la cámara y los controles de interacción.

**Usuario (persona con discapacidad auditiva):**
- Posicione la mano dentro del encuadre de la cámara.
- Realice un gesto predefinido correspondiente a un producto o acción.
- Señale con el dedo índice el número deseado (1 al 5) para indicar la cantidad.
- Lea la respuesta transcrita del vendedor en la pantalla.

**Vendedor:**
- Escuche el mensaje de voz sintetizado generado por el sistema.
- Responda verbalmente a través del micrófono.
- Visualice en pantalla la etiqueta del gesto detectado como referencia.

**Gestos soportados:**

| Gesto | Intención Mapeada |
|---|---|
| Gesto MENÚ | "¿Me puede mostrar el menú?" |
| Gesto BEBIDAS | "Quisiera una bebida por favor." |
| Gesto PAPAS | "Quisiera unas papas por favor." |
| Gesto DULCES | "Quisiera unos dulces por favor." |
| Gesto CHOCOLATE | "Quisiera chocolate por favor." |
| Gesto COMPRAR | "Deseo comprar algo." |
| Dedo índice sobre número | Selección de cantidad (1 al 5) |

> El conjunto de gestos es configurable y puede ampliarse mediante el archivo de configuración del clasificador.

---

## Estructura del Proyecto

```
gesturecomm-vision-ai/
│
├── GestureComm2/
│   └── sistema_comunicacion.py   # Módulo central del sistema
│
├── assets/
│   ├── interfaz-general.png      # Captura de la interfaz general
│   ├── deteccion-menu.png        # Captura de detección de gesto MENU
│   ├── seleccion-cantidad.png    # Captura de selección numérica
│   ├── panel-cliente.png         # Captura del panel de cliente
│   └── respuesta-vendedor.png    # Captura de respuesta del vendedor
│
├── requirements.txt
├── LICENSE
└── README.md
```

---

## Resultados y Validación

El sistema fue validado mediante pruebas funcionales en un entorno simulado de atención comercial. Observaciones principales:

| Métrica | Resultado |
|---|---|
| Tasa de detección de manos | > 95% bajo condiciones de iluminación adecuadas |
| Precisión de reconocimiento de gestos | ~88% sobre el conjunto de gestos definido |
| Latencia promedio gesto-audio | < 1.2 segundos |
| Precisión de transcripción STT | ~90% en entornos con poco ruido |
| Usabilidad del sistema (pruebas informales) | Recepción positiva por parte de los usuarios de prueba |

La validación se realizó con múltiples usuarios ejecutando secuencias de gestos a distancias variables (0.5 m – 1.5 m) y bajo distintas condiciones de iluminación. La precisión de reconocimiento disminuyó notablemente en condiciones de baja luminosidad y fondos complejos, lo cual se refleja en la sección de limitaciones.

---

## Limitaciones

- **Dependencia de iluminación:** La precisión de detección de manos disminuye significativamente en entornos con poca luz o alto contraste.
- **Complejidad del fondo:** Fondos dinámicos o recargados pueden interferir con la extracción de puntos de referencia.
- **Vocabulario de gestos fijo:** El conjunto actual de gestos es limitado y no soporta la Lengua de Señas Colombiana (LSC) completa.
- **Detección de una sola mano:** El sistema rastrea una mano a la vez; los gestos con dos manos no están soportados.
- **Precisión del STT:** El rendimiento del reconocimiento de voz disminuye en entornos ruidosos o con acentos regionales marcados.
- **Dependencia de hardware:** Requiere cámara web y micrófono funcionales; no existe respaldo sin conexión para el módulo STT.

---

## Futuras Mejoras

- **Integración de modelo de lengua de señas:** Entrenar un clasificador de aprendizaje profundo (CNN o basado en Transformers) para soportar un conjunto más amplio de señas de la Lengua de Señas Colombiana (LSC).
- **Soporte de gestos con dos manos:** Ampliar la integración de MediaPipe para procesar ambas manos simultáneamente.
- **Motor STT sin conexión:** Integrar Whisper (local) o Vosk para transcripción offline independiente del micrófono.
- **Sustracción adaptativa de fondo:** Implementar preprocesamiento robusto para manejar fondos dinámicos.
- **Despliegue móvil:** Portar los módulos principales a una aplicación móvil (Android/iOS) para mayor accesibilidad.
- **Personalización del usuario:** Permitir a los usuarios definir y entrenar mapeos de gestos personalizados.
- **Registro en base de datos:** Almacenar sesiones de interacción para análisis y mejora continua del sistema.

---

## Autores

Desarrollado como proyecto universitario de ingeniería de software y visión por computador.

| Nombre | Rol |
|---|---|
| Andrés Felipe Díaz Campos | Módulo de visión por computador y clasificación de gestos |
| Yisela Katerine Forero Silva | Diseño de interfaz gráfica, integración TTS/STT y pruebas del sistema |
| Fabián Alberto Valero Ardila | Diseño de arquitectura, máquina de estados y documentación |

---

## Licencia

Este proyecto está licenciado bajo la [Licencia MIT](LICENSE).

```
MIT License — Copyright (c) 2026 Andrés Felipe Díaz Campos
Libre para usar, modificar y distribuir con atribución.
```

---

*Este proyecto fue desarrollado con el objetivo de promover la inclusión tecnológica y mejorar la calidad de vida de las personas con discapacidad auditiva en sus interacciones comerciales cotidianas.*
