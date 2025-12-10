# Rekall

```
        ██████╗ ███████╗██╗  ██╗ █████╗ ██╗     ██╗
        ██╔══██╗██╔════╝██║ ██╔╝██╔══██╗██║     ██║
        ██████╔╝█████╗  █████╔╝ ███████║██║     ██║
        ██╔══██╗██╔══╝  ██╔═██╗ ██╔══██║██║     ██║
        ██║  ██║███████╗██║  ██╗██║  ██║███████╗███████╗
        ╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝╚═╝  ╚═╝╚══════╝╚══════╝
```

> *"Get your ass to Mars. Quaid... crush those bugs"*

**Deja de perder conocimiento. Empieza a recordar.**

Rekall es un sistema de gestión del conocimiento para desarrolladores con **memoria cognitiva** y **búsqueda semántica**. No solo almacena tu conocimiento — te ayuda a *recordarlo* y *encontrarlo* como lo hace tu cerebro.

[![Version](https://img.shields.io/badge/version-0.3.0-blue.svg)](CHANGELOG.md)
[![Python](https://img.shields.io/badge/python-3.9+-green.svg)](https://python.org)
[![License](https://img.shields.io/badge/license-MIT-brightgreen.svg)](LICENSE)

**Traducciones:** [English](README.md) | [Français](README.fr.md) | [Deutsch](README.de.md) | [中文](README.zh-CN.md)

---

## ¿Por qué Rekall?

```
Tú (hace 3 meses)            Tú (hoy)
     │                           │
     ▼                           ▼
┌─────────────┐           ┌─────────────┐
│ Fix bug X   │           │ Mismo bug X │
│ 2h investig.│           │ empezar de  │
│ ¡Encontrado!│           │ cero...     │
└─────────────┘           └─────────────┘
     │                           │
     ▼                           ▼
   (perdido)                 (2h más)
```

**Ya resolviste esto.** Pero, ¿dónde estaba esa solución?

Con Rekall:

```
┌─────────────────────────────────────────┐
│ $ rekall search "import circular"       │
│                                         │
│ [1] bug: Fix: import circular en models │
│     Score: ████████░░ 85%               │
│     Situación: Ciclo de import entre    │
│                user.py y profile.py     │
│     Solución: Extraer tipos compartidos │
│               a types/common.py         │
└─────────────────────────────────────────┘
```

**Encontrado en 5 segundos. Sin nube. Sin suscripción.**

---

## Características

| Característica | Descripción |
|----------------|-------------|
| **Búsqueda semántica** | Buscar por significado, no solo palabras clave |
| **Contexto estructurado** | Capturar situación, solución y palabras clave |
| **Grafo de conocimiento** | Vincular entradas relacionadas |
| **Memoria cognitiva** | Distinguir episodios de patrones |
| **Repetición espaciada** | Revisar a intervalos óptimos |
| **Servidor MCP** | Integración con agentes IA (Claude, etc.) |
| **100% Local** | Tus datos nunca salen de tu máquina |
| **Interfaz TUI** | Hermosa interfaz terminal con Textual |

---

## Instalación

```bash
# Con uv (recomendado)
uv tool install git+https://github.com/guthubrx/rekall.git

# Con pipx
pipx install git+https://github.com/guthubrx/rekall.git

# Verificar instalación
rekall version
```

---

## Inicio rápido

### 1. Capturar conocimiento con contexto

```bash
# Entrada simple
rekall add bug "Fix: import circular en models" -t python,import

# Con contexto estructurado (recomendado)
rekall add bug "Fix: import circular" --context-interactive
# > Situación: Ciclo de import entre user.py y profile.py
# > Solución: Extraer tipos compartidos a types/common.py
# > Palabras clave: circular, import, ciclo, refactor
```

### 2. Buscar semánticamente

```bash
# Búsqueda de texto
rekall search "import circular"

# Búsqueda semántica (encuentra conceptos relacionados)
rekall search "ciclo dependencia módulo" --semantic

# Por palabras clave
rekall search --keywords "import,ciclo"
```

### 3. Explorar en TUI

```bash
rekall          # Lanzar interfaz interactiva
```

---

## Contexto estructurado

Cada entrada puede tener contexto rico que la hace encontrable:

```bash
rekall add bug "Error CORS en Safari" --context-json '{
  "situation": "Safari bloquea solicitudes cross-origin a pesar de headers CORS",
  "solution": "Agregar credentials: include y headers Access-Control correctos",
  "trigger_keywords": ["cors", "safari", "cross-origin", "credentials"]
}'
```

O usa el modo interactivo:

```bash
rekall add bug "Error CORS en Safari" --context-interactive
```

---

## Búsqueda semántica

Rekall usa embeddings locales para buscar por significado:

```bash
# Habilitar búsqueda semántica
rekall embeddings --status      # Verificar estado
rekall embeddings --migrate     # Generar embeddings para entradas existentes

# Buscar por significado
rekall search "timeout autenticación" --semantic
```

La búsqueda combina:
- **Búsqueda de texto completo** (50%) - Coincidencia exacta de palabras clave
- **Similaridad semántica** (30%) - Coincidencia por significado
- **Coincidencia de palabras clave** (20%) - Palabras clave del contexto estructurado

---

## Grafo de conocimiento

Conecta entradas relacionadas para construir una red de conocimiento:

```bash
rekall link 01HXYZ 01HABC                      # Crear vínculo
rekall link 01HXYZ 01HABC --type supersedes    # Con tipo de relación
rekall related 01HXYZ                          # Ver conexiones
rekall graph 01HXYZ                            # Visualización ASCII
```

**Tipos de vínculos:** `related`, `supersedes`, `derived_from`, `contradicts`

---

## Memoria cognitiva

Como tu cerebro, Rekall distingue dos tipos de memoria:

### Memoria episódica (Lo que pasó)
```bash
rekall add bug "Timeout auth en API prod 15/12" --memory-type episodic
```

### Memoria semántica (Lo que aprendiste)
```bash
rekall add pattern "Siempre agregar retry backoff para APIs externas" --memory-type semantic
```

### Generalización
```bash
rekall generalize 01HA 01HB 01HC --title "Patrón retry para timeouts"
```

---

## Repetición espaciada

Revisa tu conocimiento a intervalos óptimos con el algoritmo SM-2:

```bash
rekall review              # Iniciar sesión de revisión
rekall review --limit 10   # Revisar 10 entradas
rekall stale               # Encontrar conocimiento olvidado (30+ días)
```

---

## Servidor MCP (Integración IA)

Rekall incluye un servidor MCP para integración con asistentes IA:

```bash
rekall mcp    # Iniciar servidor MCP
```

**Herramientas disponibles:**
- `rekall_search` - Buscar en la base
- `rekall_add` - Agregar entradas
- `rekall_show` - Obtener detalles de entrada
- `rekall_link` - Conectar entradas
- `rekall_suggest` - Obtener sugerencias basadas en embeddings

---

## Integraciones IDE

```bash
rekall install claude     # Claude Code
rekall install cursor     # Cursor AI
rekall install copilot    # GitHub Copilot
rekall install windsurf   # Windsurf
rekall install cline      # Cline
rekall install zed        # Zed
```

---

## Migración y Mantenimiento

```bash
rekall version             # Mostrar versión + info de esquema
rekall changelog           # Mostrar historial de versiones
rekall migrate             # Actualizar esquema de DB (con backup)
rekall migrate --dry-run   # Previsualizar cambios
```

---

## Tipos de entrada

| Tipo | Uso | Ejemplo |
|------|-----|---------|
| `bug` | Bugs corregidos | "Fix: error CORS en Safari" |
| `pattern` | Buenas prácticas | "Pattern: Repository pattern para DB" |
| `decision` | Decisiones de arquitectura | "Decision: Usar Redis para sesiones" |
| `pitfall` | Errores a evitar | "Pitfall: No usar SELECT *" |
| `config` | Tips de configuración | "Config: Debug Python en VS Code" |
| `reference` | Docs externos | "Ref: Documentación React Hooks" |
| `snippet` | Bloques de código | "Snippet: Función debounce" |
| `til` | Aprendizajes rápidos | "TIL: Git rebase -i para squash" |

---

## Datos y Privacidad

**100% local. Cero nube.**

| Plataforma | Ubicación |
|------------|-----------|
| Linux | `~/.local/share/rekall/` |
| macOS | `~/Library/Application Support/rekall/` |
| Windows | `%APPDATA%\rekall\` |

---

## Requisitos

- Python 3.9+
- Sin servicios externos
- Sin internet requerido (excepto descarga opcional del modelo de embedding)
- Sin cuenta necesaria

---

## Licencia

MIT

---

**Deja de perder conocimiento. Empieza a recordar.**

```bash
uv tool install git+https://github.com/guthubrx/rekall.git
rekall
```
