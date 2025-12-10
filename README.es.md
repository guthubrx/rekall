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

**Traducciones:** [English](README.md) | [Français](README.fr.md) | [Deutsch](README.de.md) | [中文](README.zh-CN.md)

---

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

### Conecta tu asistente de IA

Para Claude Code, Cursor, o cualquier herramienta compatible con MCP:

```bash
rekall mcp  # Expone Rekall a tu IA
```

---

## Basado en ciencia

Rekall no es solo conveniente — está construido sobre investigación en ciencias cognitivas:

- **Los grafos de conocimiento** mejoran la precisión de recuperación en un 20%
- **La repetición espaciada** mejora la retención en un 6-9%
- **Memoria episódica vs semántica** es cómo tu cerebro realmente organiza la información
- **La localización de bugs basada en historial** muestra que archivos con bugs pasados son más propensos a tener nuevos

Leímos los papers para que no tengas que hacerlo. Luego construimos una herramienta que los aplica.

---

## Requisitos

- Python 3.9+
- Eso es todo. Sin servicios cloud. Sin claves API (a menos que quieras búsqueda semántica). Sin cuentas.

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
