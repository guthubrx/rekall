<div align="center">

<!-- LOGO: Descomentar cuando logo.png esté listo
<img src="docs/images/logo.png" alt="Logo de Rekall" width="120">
-->

# Rekall

**Tu conocimiento de desarrollador, recordado al instante.**

<p>
  <img src="https://img.shields.io/badge/100%25-Local-blue?style=flat-square" alt="100% Local">
  <img src="https://img.shields.io/badge/Sin_API_Keys-green?style=flat-square" alt="Sin API Keys">
  <img src="https://img.shields.io/badge/MCP-Compatible-purple?style=flat-square" alt="Compatible MCP">
  <img src="https://img.shields.io/badge/Python-3.10+-yellow?style=flat-square" alt="Python 3.10+">
</p>

*"Get your ass to Mars. Quaid... crush those bugs"*

[Documentación](#contenido) · [Instalación](#empezando) · [Integración MCP](#servidor-mcp-funciona-con-cualquier-asistente-ia)

**Traducciones:** [English](README.md) | [Français](README.fr.md) | [Deutsch](README.de.md) | [中文](README.zh-CN.md)

</div>

---

## Contenido

- [TL;DR](#tldr)
- [El Problema](#ya-resolviste-este-problema)
- [La Solución](#qué-pasaría-si-tu-asistente-ia-recordara-por-ti)
- [Cómo Funciona](#un-segundo-cerebro-que-piensa-como-tú)
- [La Interfaz](#la-interfaz)
- [Qué Automatiza](#qué-hace-rekall-por-ti)
- [Tipos de Entradas](#qué-puedes-capturar)
- [Fuentes](#rastrea-tus-fuentes)
- [Privacidad](#100-local-100-tuyo)
- [Empezando](#empezando)
- [Servidor MCP](#servidor-mcp-funciona-con-cualquier-asistente-ia)
- [Integración Speckit](#integrar-con-speckit)
- [Bajo el Capó](#bajo-el-capó-cómo-funciona-la-búsqueda) *(técnico)*
- [Construido sobre Ciencia](#construido-sobre-ciencia) *(investigación)*

---

### TL;DR

**El problema:** Cada desarrollador ha resuelto el mismo bug dos veces. No porque sean descuidados — sino porque los humanos olvidan. Las investigaciones muestran que las empresas Fortune 500 pierden $31.5 mil millones anuales en conocimiento que nunca se captura.

**Nuestro enfoque:** Rekall es una base de conocimiento personal construida sobre investigación en ciencias cognitivas. Estudiamos cómo funciona realmente la memoria humana — memoria episódica vs semántica, repetición espaciada, grafos de conocimiento — y lo aplicamos a los flujos de trabajo de desarrollo.

**Qué hace:** Captura bugs, patrones, decisiones, configuraciones mientras trabajas. Busca por significado, no solo palabras clave — Rekall usa embeddings locales opcionales (all-MiniLM-L6-v2) combinados con búsqueda de texto completo para encontrar entradas relevantes incluso cuando tus palabras no coinciden exactamente. Almacena contexto rico (situación, solución, qué falló) para desambiguar problemas similares después.

**Funciona con tus herramientas:** Rekall expone un servidor MCP compatible con la mayoría de herramientas de desarrollo impulsadas por IA — Claude Code, Claude Desktop, Cursor, Windsurf, Continue.dev, y cualquier cliente compatible con MCP. Un comando (`rekall mcp`) y tu IA consulta tu conocimiento antes de cada corrección.

**Qué automatiza:** Extracción de palabras clave, puntuación de consolidación, detección de patrones, sugerencias de enlaces, programación de revisiones (repetición espaciada SM-2). Te enfocas en capturar — Rekall maneja el resto.

```bash
# Instalar
uv tool install git+https://github.com/guthubrx/rekall.git

# Capturar (modo interactivo te guía)
rekall add bug "CORS falla en Safari" --context-interactive

# Buscar (entiende significado, no solo palabras clave)
rekall search "navegador bloqueando API"

# Conectar a IA (un comando, funciona con Claude/Cursor/Windsurf)
rekall mcp
```

---

<br>

## Ya resolviste este problema.

Hace tres meses, pasaste dos horas depurando un error críptico. Encontraste la solución. Seguiste adelante.

Hoy, el mismo error aparece. Lo miras. Parece familiar. ¿Pero dónde estaba esa solución?

Empiezas desde cero. Otras dos horas perdidas.

**Esto le pasa a cada desarrollador.** Según las investigaciones, las empresas Fortune 500 pierden $31.5 mil millones anuales porque las lecciones aprendidas nunca se capturan. No porque la gente sea descuidada — sino porque somos humanos, y los humanos olvidan.

<br>

## ¿Qué pasaría si tu asistente IA recordara por ti?

Imagina esto: le pides a Claude o Cursor que arregle un bug. Antes de escribir una sola línea de código, revisa tu base de conocimiento personal:

```
🔍 Buscando en tu conocimiento...

Encontradas 2 entradas relevantes:

[1] bug: Error CORS en Safari (85% coincidencia)
    "Agregar credentials: include y headers Access-Control apropiados"
    → Resolviste esto hace 3 meses

[2] pattern: Manejo de solicitudes cross-origin (72% coincidencia)
    "Siempre prueba en Safari - tiene aplicación CORS más estricta"
    → Patrón extraído de 4 bugs similares
```

Tu asistente IA ahora tiene contexto. Sabe qué funcionó antes. No reinventará la rueda — construirá sobre tu experiencia pasada.

**Eso es Rekall.**

<p align="center">
  <img src="docs/screenshots/demo.gif" alt="Rekall en acción" width="700">
</p>

<!--
Marcador de capturas de pantalla - agrega tus imágenes a docs/screenshots/
Opciones:
- demo.gif: GIF animado mostrando el flujo de trabajo (recomendado)
- tui.png: Captura de pantalla de la interfaz de terminal
- search.png: Resultados de búsqueda
- mcp.png: Integración MCP con Claude/Cursor
-->

<br>

## Un segundo cerebro que piensa como tú

> **Idea clave:** Rekall está construido sobre cómo funciona realmente la memoria humana — conectando conocimiento relacionado, extrayendo patrones de episodios, y mostrando información olvidada antes de que se desvanezca.

Rekall no es solo una app para tomar notas. Está construido sobre cómo funciona realmente la memoria humana:

### Tu conocimiento, conectado

Cuando resuelves algo, el conocimiento relacionado aparece automáticamente. ¿Arreglaste un bug de timeout? Rekall te muestra los otros tres problemas de timeout que has resuelto y el patrón de reintentos que extrajiste de ellos.

```
              ┌──────────────┐
              │ Auth Timeout │
              │   (hoy)      │
              └──────┬───────┘
                     │ similar a...
        ┌────────────┼────────────┐
        ▼            ▼            ▼
  ┌──────────┐ ┌──────────┐ ┌──────────┐
  │ DB #47   │ │ API #52  │ │ Cache #61│
  │(2 semanas)│ │ (1 mes)  │ │(3 meses) │
  └────┬─────┘ └────┬─────┘ └──────────┘
       └──────┬─────┘
              ▼
     ┌─────────────────┐
     │ PATRÓN: Reintento│
     │ con backoff     │
     └─────────────────┘
```

### Los eventos se vuelven sabiduría

Cada bug que arreglas es un **episodio** — un evento específico con contexto. Pero emergen patrones. Después de arreglar tres bugs de timeout similares, Rekall te ayuda a extraer el **principio**: "Siempre agrega reintento con backoff exponencial para APIs externas."

Los episodios son materia prima. Los patrones son conocimiento reutilizable.

<br>

### El conocimiento olvidado resurge

Rekall rastrea qué accedes y cuándo. ¿Conocimiento que no has tocado en meses? Te lo recordará antes de que se desvanezca completamente. Piénsalo como repetición espaciada para tu cerebro de desarrollador.

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

Listo. Tu yo futuro te lo agradecerá.

### 2. Busca por significado, no solo palabras clave

¿No recuerdas si lo llamaste "CORS" o "cross-origin"? No importa.

```bash
rekall search "navegador bloqueando mis llamadas API"
```

Rekall entiende el significado. Encuentra entradas relevantes incluso cuando tus palabras no coinciden exactamente.

### 3. Deja que tu asistente IA lo use

Conecta Rekall a Claude, Cursor, o cualquier IA que soporte MCP:

```bash
rekall mcp  # Iniciar el servidor
```

Ahora tu IA consulta tu conocimiento antes de cada corrección. Cita tus soluciones pasadas. Sugiere guardar nuevas. Tu conocimiento se acumula con el tiempo.

---

## La interfaz

### Interfaz de Terminal
```bash
rekall  # Lanzar la interfaz visual
```

```
┌─ Rekall ────────────────────────────────────────────────┐
│  🔍 Buscar: cors safari                                 │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  [1] bug: CORS falla en Safari              85% ██████  │
│      safari, cors, fetch  •  hace 3 meses               │
│      "Agregar credentials: include..."                  │
│                                                         │
│  [2] pattern: Manejo cross-origin           72% █████   │
│      architecture  •  hace 1 mes                        │
│      "Safari tiene aplicación CORS más estricta"        │
│                                                         │
│  [3] reference: Guía MDN CORS               68% ████    │
│      docs, mdn  •  hace 6 meses                         │
│                                                         │
├─────────────────────────────────────────────────────────┤
│  [/] Buscar  [a] Agregar  [Enter] Ver  [q] Salir       │
└─────────────────────────────────────────────────────────┘
```

### Línea de comandos
```bash
rekall add bug "Fix: null pointer en auth" -t auth,null
rekall search "error de autenticación"
rekall show 01HX7...
rekall link 01HX7 01HY2 --type related
rekall review  # Sesión de repetición espaciada
```

<br>

## Qué hace Rekall por ti

> **Filosofía:** Te enfocas en capturar conocimiento. Rekall maneja todo lo demás.

### En cada entrada que agregas

- **Extracción de palabras clave** — Analiza tu título y contenido, sugiere palabras clave relevantes
- **Validación de contexto** — Advierte si la situación/solución es demasiado vaga o genérica
- **Generación de embeddings** — Crea vectores semánticos para búsqueda inteligente (si está habilitado)
- **Indexación automática** — Índice de búsqueda de texto completo actualizado en tiempo real

### En cada búsqueda

- **Coincidencia híbrida** — Combina palabras exactas (FTS5) + significado (embeddings) + activadores (palabras clave)
- **Sin configuración** — Funciona de inmediato, no necesita ajustes
- **Entradas relacionadas** — Muestra conocimiento vinculado automáticamente

### En segundo plano (no haces nada)

- **Seguimiento de acceso** — Cada vista actualiza estadísticas de frecuencia y recencia
- **Puntuación de consolidación** — Calcula qué tan "estable" es cada memoria (60% frecuencia + 40% frescura)
- **Detección de patrones** — Encuentra grupos de entradas similares, sugiere crear un patrón
- **Sugerencias de enlaces** — Detecta entradas relacionadas, propone conexiones
- **Programación de revisiones** — El algoritmo SM-2 planifica tiempos óptimos de revisión (repetición espaciada)
- **Compresión de contexto** — Almacena contexto verboso con 70-85% menos tamaño

### Cuando ejecutas `rekall review`

- **Carga entradas pendientes** — Basado en programación SM-2, no fechas arbitrarias
- **Ajusta dificultad** — Tu calificación (0-5) actualiza el factor de facilidad automáticamente
- **Reprograma** — Calcula la próxima fecha óptima de revisión

---

## ¿Qué puedes capturar?

| Tipo | Para | Ejemplo |
|------|-----|---------|
| `bug` | Problemas que has resuelto | "Safari CORS con credentials" |
| `pattern` | Enfoques reutilizables | "Reintento con backoff exponencial" |
| `decision` | Por qué elegiste X sobre Y | "PostgreSQL sobre MongoDB para este proyecto" |
| `pitfall` | Errores a evitar | "Nunca usar SELECT * en producción" |
| `config` | Configuración que funciona | "Config de depuración Python en VS Code" |
| `reference` | Docs/enlaces útiles | "Esa respuesta de StackOverflow" |
| `snippet` | Código que vale la pena conservar | "Función debounce genérica" |
| `til` | Aprendizajes rápidos | "Git rebase -i puede reordenar commits" |

---

## Rastrea tus fuentes

> **Filosofía:** Cada pieza de conocimiento vino de algún lugar. Rekall te ayuda a rastrear *de dónde* — para evaluar confiabilidad, revisitar fuentes originales, y ver qué fuentes son más valiosas para ti.

### Vincula entradas a sus fuentes

Cuando capturas conocimiento, puedes adjuntar fuentes:

```bash
# Agrega un bug con una fuente URL
rekall add bug "Safari CORS fix" -t cors,safari
# Luego vincula la fuente URL
rekall source link 01HX7... --url "https://stackoverflow.com/q/12345"

# O usa el TUI: abre entrada → Agregar fuente
rekall
```

### Tres tipos de fuentes

| Tipo | Para | Ejemplo |
|------|-----|---------|
| `url` | Páginas web, documentación | Stack Overflow, MDN, posts de blog |
| `theme` | Temas recurrentes o mentores | "Code reviews con Alice", "Reuniones de arquitectura" |
| `file` | Documentos locales | PDFs, docs internos, notas |

### Calificaciones de confiabilidad (Sistema Admiralty)

No todas las fuentes son igualmente confiables. Rekall usa un **Sistema Admiralty** simplificado:

| Calificación | Significado | Ejemplos |
|--------------|-------------|----------|
| **A** | Altamente confiable, autoritativa | Docs oficiales, peer-reviewed, expertos conocidos |
| **B** | Generalmente confiable | Blogs reputados, respuestas SO aceptadas |
| **C** | Cuestionable o no verificada | Posts de foros random, sugerencias no probadas |

### Puntuación personal: Lo que importa *para ti*

Cada fuente tiene una **puntuación personal** (0-100) basada en:

```
Puntuación = Uso × Recencia × Confiabilidad

- Uso: Con qué frecuencia citas esta fuente
- Recencia: Cuándo la usaste por última vez (decae con el tiempo)
- Confiabilidad: A=1.0, B=0.8, C=0.6
```

Las fuentes que usas frecuentemente y recientemente rankean más alto — sin importar cuán "autoritativas" sean globalmente. Tu experiencia personal importa.

### Backlinks: Ve todas las entradas de una fuente

Haz clic en cualquier fuente para ver todas las entradas que la referencian:

```
┌─ Fuente: stackoverflow.com/questions/* ─────────────────┐
│  Confiabilidad: B  │  Puntuación: 85  │  Usada: 12 veces│
├─────────────────────────────────────────────────────────┤
│  Entradas citando esta fuente:                          │
│                                                         │
│  [1] bug: CORS falla en Safari                          │
│  [2] bug: Timeout de Fetch en redes lentas              │
│  [3] pattern: Manejo de errores para llamadas API       │
└─────────────────────────────────────────────────────────┘
```

### Detección de link rot

Las fuentes web pueden desaparecer. Rekall verifica periódicamente las fuentes URL y marca las inaccesibles:

```bash
rekall sources --verify  # Verificar todas las fuentes
rekall sources --status inaccessible  # Listar enlaces rotos
```

El dashboard de Fuentes del TUI muestra:
- **Top fuentes** por puntuación personal
- **Fuentes emergentes** (citadas múltiples veces recientemente)
- **Fuentes dormantes** (no usadas en 6+ meses)
- **Fuentes inaccesibles** (link rot detectado)

---

## 100% local. 100% tuyo.

```
Tu máquina
     │
     ▼
┌─────────────────────────────────────┐
│  ~/.local/share/rekall/             │
│                                     │
│  Todo permanece aquí.               │
│  Sin nube. Sin cuenta. Sin rastreo. │
│                                     │
└─────────────────────────────────────┘
     │
     ▼
  En ningún otro lugar. Nunca.
```

Tu conocimiento es tuyo. Rekall no se comunica con servidores externos. No requiere una cuenta. Funciona sin conexión. Tu historial de depuración, tus decisiones arquitectónicas, tu sabiduría ganada con esfuerzo — todo privado, todo local.

---

## Empezando

### Instalar

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

# Búscalo
rekall search "primer"

# Abre la interfaz visual
rekall
```

---

## Servidor MCP: Funciona con cualquier asistente IA

Rekall expone tu base de conocimiento vía el **Model Context Protocol (MCP)** — el estándar abierto para conectar asistentes IA a herramientas externas.

### Un comando, acceso universal

```bash
rekall mcp  # Iniciar el servidor MCP
```

### Compatible con las principales herramientas IA

| Herramienta | Estado | Configuración |
|------|--------|---------------|
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

### Qué puede hacer tu IA

Una vez conectado, tu asistente IA puede:

- **Buscar** en tu base de conocimiento antes de responder
- **Citar** tus soluciones pasadas en sus respuestas
- **Sugerir** capturar nuevo conocimiento después de resolver problemas
- **Vincular** entradas relacionadas automáticamente
- **Mostrar** patrones a través de tu historial de depuración

Tu conocimiento se acumula automáticamente — cuanto más lo usas, más inteligente se vuelve.

---

## Integrar con Speckit

[Speckit](https://github.com/YOUR_USERNAME/speckit) es un toolkit de desarrollo impulsado por especificaciones. Combinado con Rekall, crea un flujo de trabajo poderoso donde tus especificaciones alimentan tu base de conocimiento.

### ¿Por qué integrar?

- **Las specs se vuelven conocimiento buscable**: Las decisiones tomadas durante la escritura de specs se capturan
- **Emergen patrones**: Las elecciones arquitectónicas comunes aparecen entre proyectos
- **El contexto se preserva**: El "por qué" detrás de las specs nunca se pierde

### Configuración

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
    auto_capture: true  # Captura decisiones automáticamente
    types:
      - decision
      - pattern
      - pitfall
```

3. Durante el trabajo de specs, Speckit:
   - Consultará Rekall para decisiones pasadas relevantes
   - Sugerirá capturar nuevas elecciones arquitectónicas
   - Vinculará specs a entradas de conocimiento relacionadas

### Flujo de trabajo de ejemplo

```bash
# Empezar a especificar una funcionalidad
speckit specify "Sistema de autenticación de usuario"

# Speckit consulta Rekall: "¿Has tomado decisiones de auth antes?"
# → Muestra tu decisión pasada de OAuth vs JWT de otro proyecto

# Después de finalizar la spec
speckit plan

# Rekall captura: decision "JWT para auth stateless en microservicios"
```

<br>

<details>
<summary><h2>Bajo el capó: Cómo funciona la búsqueda</h2></summary>

> **TL;DR:** Búsqueda híbrida combinando FTS5 (50%) + embeddings semánticos (30%) + palabras clave (20%). Modelo local opcional, sin API keys.

Rekall no solo hace coincidencia de palabras clave. Entiende qué quieres decir.

### El problema con la búsqueda simple

Capturaste un bug sobre "error CORS en Safari." Después, buscas "navegador bloqueando llamadas API." Una búsqueda simple de palabras clave no encuentra nada — las palabras no coinciden.

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
    │   FTS5      │        │  Semántica  │        │  Palabras   │
    │  (50%)      │        │   (30%)     │        │  clave (20%)│
    │             │        │             │        │             │
    │ Coincidencia│        │ Significado │        │ Activadores │
    │ de palabras │        │ vía embeds  │        │ estructurados│
    └──────┬──────┘        └──────┬──────┘        └──────┬──────┘
           │                      │                      │
           └───────────────────────┼───────────────────────┘
                                   ▼
                        ┌─────────────────┐
                        │ PUNTUACIÓN FINAL│
                        │  85% coincidencia│
                        └─────────────────┘
```

- **Búsqueda de texto completo (50%)**: SQLite FTS5 encuentra coincidencias exactas y parciales de palabras
- **Búsqueda semántica (30%)**: Los embeddings encuentran contenido conceptualmente similar — "navegador" coincide con "Safari", "bloqueando" coincide con "error CORS"
- **Índice de palabras clave (20%)**: Tus palabras clave de contexto estructurado proporcionan activadores explícitos

### Embeddings locales: Opcional pero poderoso

La búsqueda semántica es **opcional**. Rekall funciona perfectamente solo con búsqueda de texto completo FTS5 — no se requiere modelo.

Pero si quieres comprensión semántica, Rekall usa **all-MiniLM-L6-v2** (23M parámetros), un modelo de embeddings rápido y eficiente que se ejecuta completamente en tu máquina:

- **100% local**: Ningún dato sale de tu computadora, sin API keys, sin nube
- **Rápido**: ~50ms por embedding en un CPU de laptop estándar
- **Pequeño**: ~100MB de huella de memoria
- **Configurable**: Cambia a modelos multilingües (ej: `paraphrase-multilingual-MiniLM-L12-v2`) via config

```bash
# Modo solo FTS (predeterminado, no se necesita modelo)
rekall search "error CORS"

# Habilitar búsqueda semántica (descarga modelo en primer uso)
rekall config set embeddings.enabled true
```

### Doble embedding: El contexto importa

Cuando capturas conocimiento, Rekall almacena dos embeddings:

1. **Embedding de resumen**: Título + contenido + etiquetas — para búsquedas enfocadas
2. **Embedding de contexto**: La situación/solución completa — para búsquedas exploratorias

Esto resuelve un problema fundamental en recuperación: los resúmenes pierden contexto. Si buscas "stack trace Safari", el resumen "Fix CORS" no coincidirá — pero el contexto completo que capturaste (que menciona el stack trace) sí.

### Contexto estructurado: Desambiguación que funciona

Has arreglado 5 bugs de "timeout" diferentes. ¿Cómo encuentras el correcto después? Las palabras clave solas no ayudarán — todos están etiquetados "timeout".

Rekall captura **contexto estructurado** para cada entrada:

```
┌─────────────────────────────────────────────────────────────┐
│  situation        │  "Llamadas API timeout después deploy"  │
│  solution         │  "Aumentado tamaño pool de conexiones"  │
│  what_failed      │  "Lógica de reintento no ayudó"         │
│  trigger_keywords │  ["timeout", "deploy", "connection pool"]│
│  error_messages   │  "ETIMEDOUT después de 30s"             │
│  files_modified   │  ["config/database.yml"]                │
└─────────────────────────────────────────────────────────────┘
```

Cuando buscas, Rekall usa este contexto para desambiguar:

- **"timeout después deploy"** → Encuentra el bug del pool de conexiones (coincide situación)
- **"ETIMEDOUT"** → Encuentra entradas con ese mensaje de error exacto
- **"reintento no funcionó"** → Encuentra entradas donde se intentó reintento y falló

La bandera `--context-interactive` te guía para capturar esto:

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
│  context_blob     │  JSON comprimido (zlib)    │  ~70% menor │
│  context_keywords │  Tabla indexada búsqueda   │  O(1) lookup│
│  emb_summary      │  Vector 384-dim (resumen)  │  Semántico  │
│  emb_context      │  Vector 384-dim (contexto) │  Semántico  │
└─────────────────────────────────────────────────────────────┘
```

El resultado: búsqueda **exhaustiva** (nada se pierde) con **velocidad** (respuestas subsegundo en miles de entradas).

</details>

<br>

<details>
<summary><h2>Construido sobre ciencia</h2></summary>

> **TL;DR:** Grafos de conocimiento (+20% precisión), repetición espaciada (+6-9% retención), recuperación contextual (-67% fallos), todo respaldado por investigación revisada por pares.

Rekall no es una colección de corazonadas — está construido sobre investigación revisada por pares en ciencias cognitivas y recuperación de información. Esto es lo que aprendimos y cómo lo aplicamos:

### Grafos de conocimiento: +20% precisión de recuperación

**Investigación**: Los estudios sobre grafos de conocimiento en sistemas RAG muestran que la información conectada es más fácil de recuperar que los hechos aislados.

**Aplicación**: Rekall te permite vincular entradas con relaciones tipadas (`related`, `supersedes`, `derived_from`, `contradicts`). Cuando buscas, las entradas vinculadas aumentan las puntuaciones entre sí. Cuando arreglas un nuevo bug de timeout, Rekall muestra los otros tres problemas de timeout que has resuelto — y el patrón que extrajiste de ellos.

### Memoria episódica vs semántica: Cómo se organiza tu cerebro

**Investigación**: Tulving (1972) estableció que la memoria humana tiene dos sistemas distintos — episódica (eventos específicos: "Arreglé este bug el martes") y semántica (conocimiento general: "Siempre agrega reintento para APIs externas").

**Aplicación**: Rekall distingue entradas `episodic` (qué pasó) de entradas `semantic` (qué aprendiste). El comando `generalize` te ayuda a extraer patrones de episodios. Esto refleja cómo se desarrolla la experiencia: acumulas experiencias, luego las destilas en principios.

### Repetición espaciada: +6-9% retención

**Investigación**: El efecto de espaciado (Ebbinghaus, 1885) y el algoritmo SM-2 muestran que revisar información a intervalos crecientes mejora dramáticamente la retención.

**Aplicación**: Rekall rastrea cuándo accedes cada entrada y calcula una puntuación de consolidación. El comando `review` muestra conocimiento que está a punto de desvanecerse. El comando `stale` encuentra entradas que no has tocado en meses — antes de que se vuelvan olvidadas.

### Recuperación contextual: -67% fallos de búsqueda

**Investigación**: El paper de Recuperación Contextual de Anthropic mostró que los sistemas RAG tradicionales fallan porque eliminan el contexto al codificar. Agregar 50-100 tokens de contexto reduce los fallos de recuperación en 67%.

**Aplicación**: El contexto estructurado de Rekall (situación, solución, palabras clave) preserva el "por qué" junto con el "qué". La estrategia de doble embedding asegura que tanto las consultas enfocadas como las búsquedas exploratorias encuentren entradas relevantes.

### Divulgación progresiva: -98% uso de tokens

**Investigación**: El blog de ingeniería de Anthropic documentó que devolver resúmenes compactos en lugar de contenido completo reduce el uso de tokens en 98% mientras mantiene el éxito de la tarea.

**Aplicación**: El servidor MCP de Rekall devuelve resultados compactos (id, título, puntuación, fragmento) con una pista para obtener detalles completos. Tu asistente IA obtiene lo que necesita sin inflar su ventana de contexto.

### Puntuación de consolidación: Modelando el olvido

**Investigación**: La curva del olvido muestra que las memorias decaen exponencialmente sin refuerzo. La frecuencia de acceso y la recencia importan.

**Aplicación**: Rekall calcula una puntuación de consolidación para cada entrada:

```python
score = 0.6 × frequency_factor + 0.4 × freshness_factor
```

Las entradas que accedes frecuentemente y recientemente tienen alta consolidación (conocimiento estable). Las entradas que no has tocado en meses tienen baja consolidación (en riesgo de ser olvidadas).

**Leímos los papers para que no tengas que hacerlo. Luego construimos una herramienta que los aplica.**

</details>

<br>

## Aprende más

| Recurso | Descripción |
|----------|-------------|
| [Empezando](docs/getting-started.md) | Instalación y primeros pasos |
| [Referencia CLI](docs/usage.md) | Documentación completa de comandos |
| [Integración MCP](docs/mcp-integration.md) | Conectar a asistentes IA |
| [Arquitectura](docs/architecture.md) | Diagramas técnicos e internos |
| [Contribuir](CONTRIBUTING.md) | Cómo contribuir |
| [Registro de cambios](CHANGELOG.md) | Historial de versiones |

---

## Requisitos

- Python 3.10+
- Eso es todo. Sin servicios en la nube. Sin API keys. Sin cuentas.

---

## Licencia

MIT — Haz lo que quieras con esto.

---

<p align="center">
<strong>Deja de perder conocimiento. Empieza a recordar.</strong>
<br><br>

```bash
uv tool install git+https://github.com/guthubrx/rekall.git
rekall
```
</p>
