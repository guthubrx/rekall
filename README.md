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

**Translations:** [Français](README.fr.md) | [Español](README.es.md) | [Deutsch](README.de.md) | [中文](README.zh-CN.md)

---

## You've already solved this problem.

Three months ago, you spent two hours debugging a cryptic error. You found the fix. You moved on.

Today, the same error appears. You stare at it. It looks familiar. But where was that solution again?

You start from scratch. Another two hours gone.

**This happens to every developer.** According to research, Fortune 500 companies lose $31.5 billion annually because lessons learned are never captured. Not because people are careless — but because we're human, and humans forget.

---

## What if your AI assistant remembered for you?

Imagine this: you ask Claude or Cursor to fix a bug. Before writing a single line of code, it checks your personal knowledge base:

```
🔍 Searching your knowledge...

Found 2 relevant entries:

[1] bug: CORS error on Safari (85% match)
    "Add credentials: include and proper Access-Control headers"
    → You solved this 3 months ago

[2] pattern: Cross-origin request handling (72% match)
    "Always test on Safari - it has stricter CORS enforcement"
    → Pattern extracted from 4 similar bugs
```

Your AI assistant now has context. It knows what worked before. It won't reinvent the wheel — it'll build on your past experience.

**That's Rekall.**

---

## A second brain that thinks like you do

Rekall isn't just a note-taking app. It's built on how human memory actually works:

### Your knowledge, connected

When you solve something, related knowledge surfaces automatically. Fixed a timeout bug? Rekall shows you the three other timeout issues you've solved and the retry pattern you extracted from them.

```
              ┌──────────────┐
              │ Auth Timeout │
              │   (today)    │
              └──────┬───────┘
                     │ similar to...
        ┌────────────┼────────────┐
        ▼            ▼            ▼
  ┌──────────┐ ┌──────────┐ ┌──────────┐
  │ DB #47   │ │ API #52  │ │ Cache #61│
  │ (2 weeks)│ │ (1 month)│ │ (3 months)│
  └────┬─────┘ └────┬─────┘ └──────────┘
       └──────┬─────┘
              ▼
     ┌─────────────────┐
     │ PATTERN: Retry  │
     │ with backoff    │
     └─────────────────┘
```

### Events become wisdom

Every bug you fix is an **episode** — a specific event with context. But patterns emerge. After fixing three similar timeout bugs, Rekall helps you extract the **principle**: "Always add retry with exponential backoff for external APIs."

Episodes are raw material. Patterns are reusable knowledge.

### Forgotten knowledge resurfaces

Rekall tracks what you access and when. Knowledge you haven't touched in months? It'll remind you before it fades completely. Think of it as spaced repetition for your dev brain.

---

## How it works in practice

### 1. Capture knowledge as you work

After solving something tricky, capture it in 10 seconds:

```bash
rekall add bug "CORS fails on Safari" --context-interactive
```

Rekall asks: *What was happening? What fixed it? What keywords should trigger this?*

```
> Situation: Safari blocks requests even with CORS headers set
> Solution: Add credentials: 'include' and explicit Allow-Origin
> Keywords: cors, safari, cross-origin, fetch, credentials
```

Done. Your future self will thank you.

### 2. Search by meaning, not just keywords

Can't remember if you called it "CORS" or "cross-origin"? Doesn't matter.

```bash
rekall search "browser blocking my API calls"
```

Rekall understands meaning. It finds relevant entries even when your words don't match exactly.

### 3. Let your AI assistant use it

Connect Rekall to Claude, Cursor, or any AI that supports MCP:

```bash
rekall mcp  # Start the server
```

Now your AI consults your knowledge before every fix. It cites your past solutions. It suggests saving new ones. Your knowledge compounds over time.

---

## The interface

### Terminal UI
```bash
rekall  # Launch the visual interface
```

```
┌─ Rekall ────────────────────────────────────────────────┐
│  🔍 Search: cors safari                                 │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  [1] bug: CORS fails on Safari              85% ██████  │
│      safari, cors, fetch  •  3 months ago               │
│      "Add credentials: include..."                      │
│                                                         │
│  [2] pattern: Cross-origin handling         72% █████   │
│      architecture  •  1 month ago                       │
│      "Safari has stricter CORS enforcement"             │
│                                                         │
│  [3] reference: MDN CORS guide              68% ████    │
│      docs, mdn  •  6 months ago                         │
│                                                         │
├─────────────────────────────────────────────────────────┤
│  [/] Search  [a] Add  [Enter] View  [q] Quit            │
└─────────────────────────────────────────────────────────┘
```

### Command line
```bash
rekall add bug "Fix: null pointer in auth" -t auth,null
rekall search "authentication error"
rekall show 01HX7...
rekall link 01HX7 01HY2 --type related
rekall review  # Spaced repetition session
```

---

## What can you capture?

| Type | For | Example |
|------|-----|---------|
| `bug` | Problems you've solved | "Safari CORS with credentials" |
| `pattern` | Reusable approaches | "Retry with exponential backoff" |
| `decision` | Why you chose X over Y | "PostgreSQL over MongoDB for this project" |
| `pitfall` | Mistakes to avoid | "Never use SELECT * in production" |
| `config` | Setup that works | "VS Code Python debugging config" |
| `reference` | Useful docs/links | "That one StackOverflow answer" |
| `snippet` | Code worth keeping | "Generic debounce function" |
| `til` | Quick learnings | "Git rebase -i can reorder commits" |

---

## 100% local. 100% yours.

```
Your machine
     │
     ▼
┌─────────────────────────────────────┐
│  ~/.local/share/rekall/             │
│                                     │
│  Everything stays here.             │
│  No cloud. No account. No tracking. │
│                                     │
└─────────────────────────────────────┘
     │
     ▼
  Nowhere else. Ever.
```

Your knowledge is yours. Rekall doesn't phone home. It doesn't require an account. It works offline. Your debugging history, your architectural decisions, your hard-won wisdom — all private, all local.

---

## Getting started

### Install

```bash
# With uv (recommended)
uv tool install git+https://github.com/guthubrx/rekall.git

# With pipx
pipx install git+https://github.com/guthubrx/rekall.git
```

### Try it

```bash
# Add your first entry
rekall add bug "My first captured bug" -t test

# Search it
rekall search "first"

# Open the visual interface
rekall
```

### Connect your AI assistant

For Claude Code, Cursor, or any MCP-compatible tool:

```bash
rekall mcp  # Exposes Rekall to your AI
```

Now your AI can search your knowledge, suggest links, and help capture new entries — all automatically.

---

## Built on science

Rekall isn't just convenient — it's built on cognitive science research:

- **Knowledge graphs** improve retrieval accuracy by 20% (connected knowledge is easier to find)
- **Spaced repetition** improves retention by 6-9% (reviewing at the right time matters)
- **Episodic vs semantic memory** is how your brain actually organizes information
- **History-based fault localization** shows that files with past bugs are more likely to have new ones

We read the papers so you don't have to. Then we built a tool that applies them.

---

## Learn more

| Resource | Description |
|----------|-------------|
| `rekall --help` | Full command reference |
| `rekall version` | Version and database info |
| `rekall changelog` | What's new |
| [CHANGELOG.md](CHANGELOG.md) | Detailed release history |

---

## Requirements

- Python 3.9+
- That's it. No cloud services. No API keys (unless you want semantic search). No accounts.

---

## License

MIT — Do what you want with it.

---

<p align="center">
<strong>Stop losing knowledge. Start remembering.</strong>
<br><br>

```bash
uv tool install git+https://github.com/guthubrx/rekall.git
rekall
```
</p>
