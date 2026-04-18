# ================================================================
#  config.py  —  Configuracion global del proyecto
# ================================================================
import os

BASE_DIR     = os.path.dirname(os.path.abspath(__file__))
DATASET_DIR  = os.path.join(BASE_DIR, "dataset")
MODELS_DIR   = os.path.join(BASE_DIR, "models")
DATASET_FILE = os.path.join(DATASET_DIR, "gestos_dataset.csv")
MODEL_FILE   = os.path.join(MODELS_DIR,  "modelo_gestos.h5")
LABEL_FILE   = os.path.join(MODELS_DIR,  "etiquetas.npy")

# ── Gestos ───────────────────────────────────────────────────────
GESTOS = [
    "hola",
    "comprar",
    "gracias",
    "ayuda",
    "menu",
    "papas",
    "dulces",
    "bebidas",
    "chocolate",
]

# ── Mensajes de voz por gesto ────────────────────────────────────
MENSAJES_GESTO = {
    "hola":      "Hola buenos dias",
    "comprar":   "Deseo comprar algo.",
    "gracias":   "Muchas gracias!",
    "ayuda":     "Necesito ayuda por favor.",
    "menu":      "Me puede mostrar el menu?",
    "papas":     "Quisiera unas papas por favor.",
    "dulces":    "Quisiera dulces por favor.",
    "bebidas":   "Quisiera una bebida por favor.",
    "chocolate": "Quisiera chocolate por favor.",
}

# ── Gestos que muestran imagen de producto ────────────────────────
GESTOS_CON_IMAGEN = ["menu", "papas", "dulces", "bebidas", "chocolate"]

IMAGEN_GESTO = {
    "hola":      None,
    "comprar":   None,
    "gracias":   None,
    "ayuda":     None,
    "menu":      os.path.join(BASE_DIR, "assets", "imagenes", "menu.png"),
    "papas":     os.path.join(BASE_DIR, "assets", "imagenes", "papas.png"),
    "dulces":    os.path.join(BASE_DIR, "assets", "imagenes", "dulces.png"),
    "bebidas":   os.path.join(BASE_DIR, "assets", "imagenes", "bebidas.png"),
    "chocolate": os.path.join(BASE_DIR, "assets", "imagenes", "chocolate.png"),
}

# ── Dataset ──────────────────────────────────────────────────────
FEATURE_SIZE     = 63
MUESTRAS_OBJ     = 80

# ── Modelo ───────────────────────────────────────────────────────
EPOCHS           = 120
BATCH_SIZE       = 32
VALIDATION_SPLIT = 0.20
LEARNING_RATE    = 0.001
DROPOUT_RATE     = 0.30

# ── Inferencia ───────────────────────────────────────────────────
CONFIDENCE_THRESHOLD = 0.85
SMOOTHING_FRAMES     = 10
COOLDOWN_SECONDS     = 3

# ── Camara ───────────────────────────────────────────────────────
CAMERA_INDEX  = 0
FRAME_WIDTH   = 640
FRAME_HEIGHT  = 480

# ── Voz ──────────────────────────────────────────────────────────
SPEECH_LANGUAGE     = "es-CO"
SPEECH_TIMEOUT      = 8
SPEECH_PHRASE_LIMIT = 12

# ── Colores UI ───────────────────────────────────────────────────
COLOR_BG       = "#0D1117"
COLOR_SURFACE  = "#161B22"
COLOR_CARD     = "#1C2128"
COLOR_ACCENT   = "#00D4AA"
COLOR_ACCENT2  = "#FF6B35"
COLOR_TEXT     = "#E6EDF3"
COLOR_TEXT_DIM = "#8B949E"
COLOR_SUCCESS  = "#3FB950"
COLOR_WARNING  = "#D29922"
COLOR_ERROR    = "#F85149"
COLOR_BORDER   = "#30363D"
COLOR_GOLD     = "#FFD700"