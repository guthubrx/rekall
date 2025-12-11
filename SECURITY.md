# Security Policy

*[Français](#politique-de-sécurité) | [Español](#política-de-seguridad) | [Deutsch](#sicherheitsrichtlinie) | [中文](#安全政策)*

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 0.3.x   | :white_check_mark: |
| < 0.3   | :x:                |

## Reporting a Vulnerability

**Please do not report security vulnerabilities through public GitHub issues.**

Instead, please report them via email to the project maintainers. You should receive a response within 48 hours.

Please include:
- Type of issue (e.g., buffer overflow, SQL injection, cross-site scripting)
- Full paths of source file(s) related to the issue
- Location of the affected source code (tag/branch/commit or direct URL)
- Step-by-step instructions to reproduce the issue
- Proof-of-concept or exploit code (if possible)
- Impact of the issue

## Security Design

Rekall is designed with security in mind:

- **100% Local**: All data stays on your machine. No cloud, no external APIs, no data transmission.
- **No Network by Default**: Rekall only uses network when you explicitly enable MCP server or semantic search model download.
- **SQLite Database**: Data stored in `~/.local/share/rekall/rekall.db` with standard file permissions.
- **No Credentials Stored**: Rekall doesn't store any passwords, API keys, or authentication tokens.

---

# Politique de Sécurité

## Signaler une Vulnérabilité

**Veuillez ne pas signaler les vulnérabilités de sécurité via les issues GitHub publiques.**

Envoyez plutôt un email aux mainteneurs du projet. Vous devriez recevoir une réponse sous 48 heures.

---

# Política de Seguridad

## Reportar una Vulnerabilidad

**Por favor, no reporte vulnerabilidades de seguridad a través de issues públicos de GitHub.**

En su lugar, repórtelas por correo electrónico a los mantenedores del proyecto. Debería recibir una respuesta dentro de 48 horas.

---

# Sicherheitsrichtlinie

## Eine Schwachstelle melden

**Bitte melden Sie Sicherheitslücken nicht über öffentliche GitHub-Issues.**

Melden Sie diese stattdessen per E-Mail an die Projektbetreuer. Sie sollten innerhalb von 48 Stunden eine Antwort erhalten.

---

# 安全政策

## 报告漏洞

**请不要通过公开的 GitHub Issues 报告安全漏洞。**

请通过电子邮件向项目维护者报告。您应该在 48 小时内收到回复。
