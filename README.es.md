# Rekall

```
        ██████╗ ███████╗██╗  ██╗ █████╗ ██╗     ██╗
        ██╔══██╗██╔════╝██║ ██╔╝██╔══██╗██║     ██║
        ██████╔╝█████╗  █████╔╝ ███████║██║     ██║
        ██╔══██╗██╔══╝  ██╔═██╗ ██╔══██║██║     ██║
        ██║  ██║███████╗██║  ██╗██║  ██║███████╗███████╗
        ╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝╚═╝  ╚═╝╚══════╝╚══════╝
```

<p align="center">
  <img src="https://img.shields.io/badge/100%25-Local-blue?style=flat-square" alt="100% Local">
  <img src="https://img.shields.io/badge/No_API_Keys-green?style=flat-square" alt="No API Keys">
  <img src="https://img.shields.io/badge/MCP-Compatible-purple?style=flat-square" alt="MCP Compatible">
  <img src="https://img.shields.io/badge/Python-3.9+-yellow?style=flat-square" alt="Python 3.9+">
</p>

> *"Get your ass to Mars. Quaid... crush those bugs"*

**Traducciones:** [English](README.md) | [Français](README.fr.md) | [Deutsch](README.de.md) | [中文](README.zh-CN.md)

---

### TL;DR

**El problema:** Todo desarrollador ha resuelto el mismo bug dos veces. No por descuido — porque somos humanos, y los humanos olvidamos. Los estudios muestran que las empresas Fortune 500 pierden 31.5 mil millones de dólares al año en conocimiento nunca capturado.

**Nuestro enfoque:** Rekall es una base de conocimientos personal construida sobre investigación en ciencias cognitivas. Estudiamos cómo funciona realmente la memoria humana — memoria episódica vs semántica, repetición espaciada, grafos de conocimiento — y lo aplicamos a flujos de trabajo de desarrolladores.

**Lo que hace:** Captura bugs, patrones, decisiones, configs mientras trabajas. Busca por significado, no solo palabras clave — Rekall usa embeddings locales opcionales (EmbeddingGemma) combinados con búsqueda full-text para encontrar entradas relevantes incluso cuando tus palabras no coinciden exactamente. Almacena contexto rico (situación, solución, qué falló) para desambiguar problemas similares después.

**Funciona con tus herramientas:** Rekall expone un servidor MCP compatible con la mayoría de herramientas de desarrollo con IA — Claude Code, Claude Desktop, Cursor, Windsurf, Continue.dev, y cualquier cliente MCP. Un comando (`rekall mcp`) y tu IA consulta tu conocimiento antes de cada fix.

**Lo que automatiza:** Extracción de palabras clave, puntaje de consolidación, detección de patrones, sugerencias de enlaces, programación de revisiones (repetición espaciada SM-2). Tú te enfocas en capturar — Rekall maneja el resto.

```bash
# Instalación
uv tool install git+https://github.com/guthubrx/rekall.git

# Captura (el modo interactivo te guía)
rekall add bug "CORS falla en Safari" --context-interactive

# Busca (entiende el significado, no solo palabras clave)
rekall search "navegador bloquea API"

# Conecta tu IA (un comando, funciona con Claude/Cursor/Windsurf)
rekall mcp
```

---

<br>

## Ya resolviste este problema.

Hace tres meses, pasaste dos horas debugueando un error críptico. Encontraste la solución. Seguiste adelante.

Hoy, aparece el mismo error. Lo miras fijamente. Te suena familiar. Pero, ¿dónde estaba esa solución?

Empiezas desde cero. Otras dos horas perdidas.

**Esto le pasa a todos los desarrolladores.** Según estudios, las empresas Fortune 500 pierden 31.5 mil millones de dólares al año porque las lecciones aprendidas nunca se capturan. No por descuido — sino porque somos humanos, y los humanos olvidamos.

---

## ¿Y si tu asistente de IA recordara por ti?

Imagina esto: le pides a Claude o Cursor que arregle un bug. Antes de escribir una sola línea de código, consulta tu base de conocimiento personal:

```
🔍 Buscando en tu conocimiento...

Se encontraron 2 entradas relevantes:

[1] bug: Error CORS en Safari (85% de coincidencia)
    "Agregar credentials: include y los headers Access-Control correctos"
    → Resolviste esto hace 3 meses

[2] pattern: Manejo de solicitudes cross-origin (72% de coincidencia)
    "Siempre probar en Safari - es más estricto con CORS"
    → Patrón extraído de 4 bugs similares
```

Tu asistente de IA ahora tiene contexto. Sabe qué funcionó antes. No reinventará la rueda — construirá sobre tu experiencia pasada.

**Eso es Rekall.**

<p align="center">
  <img src="docs/screenshots/demo.gif" alt="Rekall en acción" width="700">
</p>

---

## Un segundo cerebro que piensa como tú

Rekall no es solo una app de notas. Está construido sobre cómo funciona realmente la memoria humana:

### Tu conocimiento, conectado

Cuando resuelves algo, el conocimiento relacionado aparece automáticamente. ¿Arreglaste un bug de timeout? Rekall te muestra los otros tres problemas de timeout que resolviste y el patrón de retry que extrajiste de ellos.

```
              ┌──────────────┐
              │ Auth Timeout │
              │    (hoy)     │
              └──────┬───────┘
                     │ similar a...
        ┌────────────┼────────────┐
        ▼            ▼            ▼
  ┌──────────┐ ┌──────────┐ ┌──────────┐
  │ DB #47   │ │ API #52  │ │ Cache #61│
  │(2 semanas)│ │ (1 mes)  │ │ (3 meses)│
  └────┬─────┘ └────┬─────┘ └──────────┘
       └──────┬─────┘
              ▼
     ┌─────────────────┐
     │ PATRÓN: Retry   │
     │ con backoff     │
     └─────────────────┘
```

### Los eventos se convierten en sabiduría

Cada bug que arreglas es un **episodio** — un evento específico con contexto. Pero emergen patrones. Después de arreglar tres bugs de timeout similares, Rekall te ayuda a extraer el **principio**: "Siempre agregar retry con backoff exponencial para APIs externas."

Los episodios son materia prima. Los patrones son conocimiento reutilizable.

### El conocimiento olvidado resurge

Rekall rastrea lo que consultas y cuándo. ¿Conocimiento que no has tocado en meses? Te lo recordará antes de que se desvanezca por completo. Piensa en ello como repetición espaciada para tu cerebro de dev.

---

## Cómo funciona en la práctica

### 1. Captura conocimiento mientras trabajas

Después de resolver algo complicado, captúralo en 10 segundos:

```bash
rekall add bug "CORS falla en Safari" --context-interactive
```

Rekall pregunta: *¿Qué estaba pasando? ¿Qué lo arregló? ¿Qué palabras clave deberían activar esto?*

```
> Situación: Safari bloquea solicitudes incluso con headers CORS configurados
> Solución: Agregar credentials: 'include' y Allow-Origin explícito
> Palabras clave: cors, safari, cross-origin, fetch, credentials
```

Listo. Tu yo del futuro te lo agradecerá.

### 2. Busca por significado, no solo palabras clave

¿No recuerdas si lo llamaste "CORS" o "cross-origin"? No importa.

```bash
rekall search "navegador bloqueando mis llamadas API"
```

Rekall entiende el significado. Encuentra entradas relevantes incluso cuando tus palabras no coinciden exactamente.

### 3. Deja que tu asistente de IA lo use

Conecta Rekall a Claude, Cursor, o cualquier IA compatible con MCP:

```bash
rekall mcp  # Inicia el servidor
```

Ahora tu IA consulta tu conocimiento antes de cada corrección. Cita tus soluciones pasadas. Sugiere guardar nuevas. Tu conocimiento se acumula con el tiempo.

---

## La interfaz

### Terminal UI
```bash
rekall  # Lanza la interfaz visual
```

```
┌─ Rekall ────────────────────────────────────────────────┐
│  🔍 Búsqueda: cors safari                               │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  [1] bug: CORS falla en Safari             85% ██████   │
│      safari, cors, fetch  •  hace 3 meses               │
│      "Agregar credentials: include..."                  │
│                                                         │
│  [2] pattern: Manejo cross-origin          72% █████    │
│      arquitectura  •  hace 1 mes                        │
│      "Safari es más estricto con CORS"                  │
│                                                         │
├─────────────────────────────────────────────────────────┤
│  [/] Buscar  [a] Agregar  [Enter] Ver  [q] Salir        │
└─────────────────────────────────────────────────────────┘
```

### Línea de comandos
```bash
rekall add bug "Fix: null pointer en auth" -t auth,null
rekall search "error autenticación"
rekall show 01HX7...
rekall link 01HX7 01HY2 --type related
rekall review  # Sesión de repetición espaciada
```

<br>

## Lo que Rekall hace por ti

> **Filosofía:** Tú te enfocas en capturar tu conocimiento. Rekall maneja todo lo demás.

### Con cada entrada que agregas

- **Extracción de palabras clave** — Analiza tu título y contenido, sugiere keywords relevantes
- **Validación de contexto** — Advierte si la situación/solución es demasiado vaga o genérica
- **Generación de embeddings** — Crea vectores semánticos para búsqueda inteligente (si está habilitado)
- **Indexación automática** — El índice de búsqueda full-text se actualiza en tiempo real

### Con cada búsqueda

- **Matching híbrido** — Combina palabras exactas (FTS5) + significado (embeddings) + disparadores (keywords)
- **Cero configuración** — Funciona out of the box, no necesita tuning
- **Entradas vinculadas** — Muestra automáticamente conocimiento relacionado

### En segundo plano (no haces nada)

- **Tracking de acceso** — Cada consulta actualiza las stats de frecuencia y recencia
- **Puntaje de consolidación** — Calcula qué tan "estable" es cada memoria (60% frecuencia + 40% frescura)
- **Detección de patrones** — Encuentra clusters de entradas similares, sugiere crear un patrón
- **Sugerencias de enlaces** — Detecta entradas relacionadas, propone conexiones
- **Programación de revisiones** — El algoritmo SM-2 programa los momentos óptimos de revisión (repetición espaciada)
- **Compresión de contexto** — Almacena el contexto verboso con 70-85% menos de tamaño

### Cuando ejecutas `rekall review`

- **Carga entradas pendientes** — Basado en la programación SM-2, no fechas arbitrarias
- **Ajusta la dificultad** — Tu calificación (0-5) actualiza el factor de facilidad automáticamente
- **Reprograma** — Calcula la próxima fecha de revisión óptima

---

## ¿Qué puedes capturar?

| Tipo | Para | Ejemplo |
|------|------|---------|
| `bug` | Problemas resueltos | "CORS Safari con credentials" |
| `pattern` | Enfoques reutilizables | "Retry con backoff exponencial" |
| `decision` | Por qué X en lugar de Y | "PostgreSQL en lugar de MongoDB" |
| `pitfall` | Errores a evitar | "Nunca SELECT * en producción" |
| `config` | Config que funciona | "Config debug Python VS Code" |
| `reference` | Docs/enlaces útiles | "Esa respuesta de StackOverflow" |
| `snippet` | Código para guardar | "Función debounce genérica" |
| `til` | Aprendizajes rápidos | "Git rebase -i puede reordenar commits" |

---

## 100% local. 100% tuyo.

```
Tu máquina
     │
     ▼
┌─────────────────────────────────────┐
│  ~/.local/share/rekall/             │
│                                     │
│  Todo se queda aquí.                │
│  Sin nube. Sin cuenta. Sin tracking.│
│                                     │
└─────────────────────────────────────┘
     │
     ▼
  En ningún otro lugar. Nunca.
```

Tu conocimiento es tuyo. Rekall no llama a casa. No requiere cuenta. Funciona offline. Tu historial de debug, tus decisiones de arquitectura, tu sabiduría duramente ganada — todo privado, todo local.

---

## Para empezar

### Instalación

```bash
# Con uv (recomendado)
uv tool install git+https://github.com/guthubrx/rekall.git

# Con pipx
pipx install git+https://github.com/guthubrx/rekall.git
```

### Pruébalo

```bash
# Agrega tu primera entrada
rekall add bug "Mi primer bug capturado" -t test

# Búscala
rekall search "primer"

# Abre la interfaz visual
rekall
```

---

## Servidor MCP: Funciona con cualquier asistente de IA

Rekall expone tu base de conocimientos a través del **Model Context Protocol (MCP)** — el estándar abierto para conectar asistentes de IA con herramientas externas.

### Un comando, acceso universal

```bash
rekall mcp  # Inicia el servidor MCP
```

### Compatible con las principales herramientas de IA

| Herramienta | Estado | Configuración |
|-------------|--------|---------------|
| **Claude Code** | ✅ Nativo | Auto-detectado |
| **Claude Desktop** | ✅ Nativo | Agregar a `claude_desktop_config.json` |
| **Cursor** | ✅ Soportado | Configuración MCP |
| **Windsurf** | ✅ Soportado | Configuración MCP |
| **Continue.dev** | ✅ Soportado | Configuración MCP |
| **Cualquier cliente MCP** | ✅ Compatible | Protocolo MCP estándar |

### Ejemplo de configuración (Claude Desktop)

Agrega a tu `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "rekall": {
      "command": "rekall",
      "args": ["mcp"]
    }
  }
}
```

### Lo que tu IA puede hacer

Una vez conectado, tu asistente de IA puede:

- **Buscar** en tu base de conocimientos antes de responder
- **Citar** tus soluciones pasadas en sus respuestas
- **Sugerir** capturar nuevo conocimiento después de resolver problemas
- **Vincular** automáticamente entradas relacionadas
- **Mostrar** patrones en tu historial de debugging

Tu conocimiento se acumula automáticamente — cuanto más lo usas, más inteligente se vuelve.

---

## Integración con Speckit

[Speckit](https://github.com/YOUR_USERNAME/speckit) es un toolkit de desarrollo impulsado por especificaciones. Combinado con Rekall, crea un flujo de trabajo poderoso donde tus especificaciones alimentan tu base de conocimientos.

### ¿Por qué integrar?

- **Las specs se vuelven conocimiento buscable**: Las decisiones tomadas durante la escritura de specs se capturan
- **Emergen patrones**: Las elecciones arquitectónicas comunes aparecen entre proyectos
- **El contexto se preserva**: El "por qué" detrás de las specs nunca se pierde

### Instalación

1. Instala ambas herramientas:
```bash
uv tool install git+https://github.com/guthubrx/rekall.git
uv tool install git+https://github.com/YOUR_USERNAME/speckit.git
```

2. Configura Speckit para usar Rekall (en tu `.speckit/config.yaml`):
```yaml
integrations:
  rekall:
    enabled: true
    auto_capture: true  # Captura automática de decisiones
    types:
      - decision
      - pattern
      - pitfall
```

3. Durante el trabajo de spec, Speckit:
   - Consulta Rekall para decisiones pasadas relevantes
   - Sugiere capturar nuevas elecciones arquitectónicas
   - Vincula specs con entradas de conocimiento relacionadas

### Ejemplo de flujo de trabajo

```bash
# Empieza a especificar una feature
speckit specify "Sistema de autenticación de usuario"

# Speckit consulta Rekall: "¿Has tomado decisiones de auth antes?"
# → Muestra tu decisión pasada OAuth vs JWT de otro proyecto

# Después de finalizar la spec
speckit plan

# Rekall captura: decision "JWT para auth stateless en microservicios"
```

<br>

<details>
<summary><h2>Bajo el capó: Cómo funciona la búsqueda</h2></summary>

> **TL;DR:** Búsqueda híbrida combinando FTS5 (50%) + embeddings semánticos (30%) + palabras clave (20%). Modelo local opcional, sin claves API.

Rekall no solo hace coincidencia de palabras clave. Entiende lo que quieres decir.

### El problema con la búsqueda simple

Capturaste un bug sobre "Error CORS en Safari." Más tarde, buscas "navegador bloqueando mis llamadas API." Una búsqueda por palabras clave no encuentra nada — las palabras no coinciden.

### Búsqueda híbrida: exhaustiva Y rápida

Rekall combina tres estrategias de búsqueda:

```
┌──────────────────────────────────────────────────────────────┐
│                     TU CONSULTA                              │
│              "navegador bloqueando llamadas API"             │
└──────────────────────────────────┬───────────────────────────┘
                                   │
           ┌───────────────────────┼───────────────────────┐
           ▼                       ▼                       ▼
    ┌─────────────┐        ┌─────────────┐        ┌─────────────┐
    │   FTS5      │        │  Semántica  │        │ Palabras    │
    │  (50%)      │        │   (30%)     │        │ clave (20%) │
    │             │        │             │        │             │
    │ Coincidencia│        │ Significado │        │ Disparadores│
    │ exacta      │        │ via emb.    │        │ estructurados│
    └──────┬──────┘        └──────┬──────┘        └──────┬──────┘
           │                      │                      │
           └───────────────────────┼───────────────────────┘
                                   ▼
                        ┌─────────────────┐
                        │  SCORE FINAL    │
                        │  85% match      │
                        └─────────────────┘
```

- **Búsqueda full-text (50%)**: SQLite FTS5 encuentra coincidencias exactas y parciales
- **Búsqueda semántica (30%)**: Los embeddings encuentran contenido conceptualmente similar — "navegador" coincide con "Safari", "bloqueando" coincide con "error CORS"
- **Índice de palabras clave (20%)**: Tus palabras clave de contexto estructurado proporcionan disparadores explícitos

### Embeddings locales: Opcionales pero potentes

La búsqueda semántica es **opcional**. Rekall funciona perfectamente con búsqueda full-text FTS5 sola — no se requiere modelo.

Pero si quieres comprensión semántica, Rekall usa **EmbeddingGemma** (308M parámetros), un modelo de embedding estado del arte que corre completamente en tu máquina:

- **100% local**: Ningún dato sale de tu computadora, sin claves API, sin nube
- **Multilingüe**: Funciona en más de 100 idiomas
- **Rápido**: ~500ms por embedding en una CPU estándar
- **Ligero**: ~200MB de RAM con cuantización int8

```bash
# Modo solo FTS (por defecto, no se necesita modelo)
rekall search "error CORS"

# Habilitar búsqueda semántica (descarga el modelo en el primer uso)
rekall config set embeddings.enabled true
```

### Doble embedding: El contexto importa

Cuando capturas conocimiento, Rekall almacena dos embeddings:

1. **Embedding de resumen**: Título + contenido + tags — para búsquedas focalizadas
2. **Embedding de contexto**: La situación/solución completa — para búsquedas exploratorias

Esto resuelve un problema fundamental en la recuperación: los resúmenes pierden contexto. Si buscas "stack trace Safari", el resumen "Fix CORS" no coincidirá — pero el contexto completo que capturaste (que menciona el stack trace) sí.

### Contexto estructurado: Desambiguación que funciona

Arreglaste 5 bugs de "timeout" diferentes. ¿Cómo encuentras el correcto después? Las palabras clave solas no ayudan — todos están etiquetados "timeout".

Rekall captura **contexto estructurado** para cada entrada:

```
┌─────────────────────────────────────────────────────────────┐
│  situation        │  "Llamadas API timeout después del deploy" │
│  solution         │  "Aumenté el tamaño del pool de conexiones" │
│  what_failed      │  "La lógica de retry no ayudó"          │
│  trigger_keywords │  ["timeout", "deploy", "pool conexiones"]│
│  error_messages   │  "ETIMEDOUT después de 30s"             │
│  files_modified   │  ["config/database.yml"]                │
└─────────────────────────────────────────────────────────────┘
```

Cuando buscas, Rekall usa este contexto para desambiguar:

- **"timeout después del deploy"** → Encuentra el bug del pool de conexiones (match situación)
- **"ETIMEDOUT"** → Encuentra entradas con ese mensaje de error exacto
- **"retry no funcionó"** → Encuentra entradas donde se probó retry y falló

El flag `--context-interactive` te guía para capturar esto:

```bash
rekall add bug "Timeout en prod" --context-interactive
# Rekall pregunta: ¿Qué estaba pasando? ¿Qué lo arregló? ¿Qué no funcionó?
# Tus respuestas se convierten en contexto de desambiguación buscable
```

### Almacenamiento comprimido

El contexto puede ser verboso. Rekall comprime el contexto estructurado con zlib y mantiene un índice de palabras clave separado para búsqueda rápida:

```
┌─────────────────────────────────────────────────────────────┐
│                 ALMACENAMIENTO DE ENTRADA                   │
├─────────────────────────────────────────────────────────────┤
│  context_blob     │  JSON comprimido (zlib)  │  ~70% menor │
│  context_keywords │  Tabla indexada          │  Lookup O(1)│
│  emb_summary      │  Vector 768-dim          │  Semántico  │
│  emb_context      │  Vector 768-dim          │  Semántico  │
└─────────────────────────────────────────────────────────────┘
```

El resultado: búsqueda **exhaustiva** (nada se pierde) con **velocidad** (respuestas sub-segundo en miles de entradas).

</details>

<br>

<details>
<summary><h2>Basado en ciencia</h2></summary>

Rekall no es una colección de corazonadas — está construido sobre investigación en ciencias cognitivas y recuperación de información revisada por pares. Esto es lo que aprendimos y cómo lo aplicamos:

### Grafos de conocimiento: +20% precisión de recuperación

**Investigación**: Los estudios sobre grafos de conocimiento en sistemas RAG muestran que la información conectada es más fácil de recuperar que los hechos aislados.

**Aplicación**: Rekall te permite vincular entradas con relaciones tipadas (`related`, `supersedes`, `derived_from`, `contradicts`). Cuando buscas, las entradas vinculadas aumentan sus puntajes mutuamente. Cuando arreglas un nuevo bug de timeout, Rekall muestra los otros tres problemas de timeout que resolviste — y el patrón que extrajiste de ellos.

### Memoria episódica vs semántica: Cómo tu cerebro organiza

**Investigación**: Tulving (1972) estableció que la memoria humana tiene dos sistemas distintos — episódico (eventos específicos: "Arreglé este bug el martes") y semántico (conocimiento general: "Siempre agregar retry para APIs externas").

**Aplicación**: Rekall distingue entradas `episodic` (qué pasó) de entradas `semantic` (qué aprendiste). El comando `generalize` te ayuda a extraer patrones de los episodios. Esto refleja cómo se desarrolla la experiencia: acumulas experiencias, luego las destilas en principios.

### Repetición espaciada: +6-9% retención

**Investigación**: El efecto de espaciado (Ebbinghaus, 1885) y el algoritmo SM-2 muestran que revisar información a intervalos crecientes mejora dramáticamente la retención.

**Aplicación**: Rekall rastrea cuándo accedes a cada entrada y calcula un puntaje de consolidación. El comando `review` muestra conocimiento que está por desvanecerse. El comando `stale` encuentra entradas que no has tocado en meses — antes de que se olviden.

### Recuperación contextual: -67% fallos de búsqueda

**Investigación**: El paper Contextual Retrieval de Anthropic mostró que los sistemas RAG tradicionales fallan porque eliminan el contexto al codificar. Agregar 50-100 tokens de contexto reduce los fallos de recuperación en 67%.

**Aplicación**: El contexto estructurado de Rekall (situación, solución, palabras clave) preserva el "por qué" junto con el "qué". La estrategia de doble embedding asegura que tanto las consultas focalizadas como las búsquedas exploratorias encuentren entradas relevantes.

### Divulgación progresiva: -98% uso de tokens

**Investigación**: El blog de ingeniería de Anthropic documentó que devolver resúmenes compactos en lugar de contenido completo reduce el uso de tokens en 98% mientras mantiene el éxito de las tareas.

**Aplicación**: El servidor MCP de Rekall devuelve resultados compactos (id, título, puntaje, extracto) con una pista para obtener detalles completos. Tu asistente IA obtiene lo que necesita sin explotar su ventana de contexto.

### Puntaje de consolidación: Modelando el olvido

**Investigación**: La curva del olvido muestra que los recuerdos se degradan exponencialmente sin refuerzo. La frecuencia y la recencia de acceso importan.

**Aplicación**: Rekall calcula un puntaje de consolidación para cada entrada:

```python
score = 0.6 × factor_frecuencia + 0.4 × factor_frescura
```

Las entradas que accedes frecuente y recientemente tienen alta consolidación (conocimiento estable). Las entradas que no has tocado en meses tienen baja consolidación (en riesgo de ser olvidadas).

---

**Leímos los papers para que no tengas que hacerlo. Luego construimos una herramienta que los aplica.**

</details>

<br>

---

## Más información

| Recurso | Descripción |
|---------|-------------|
| `rekall --help` | Referencia completa de comandos |
| `rekall version` | Versión e info de base de datos |
| `rekall changelog` | Novedades |
| [CHANGELOG.md](CHANGELOG.md) | Historial detallado de versiones |

---

## Requisitos

- Python 3.9+
- Eso es todo. Sin servicios cloud. Sin claves API. Sin cuentas.

---

## Licencia

MIT — Haz lo que quieras con él.

---

<p align="center">
<strong>Deja de perder conocimiento. Empieza a recordar.</strong>
<br><br>

```bash
uv tool install git+https://github.com/guthubrx/rekall.git
rekall
```
</p>
