"""Rekall internationalization (i18n) support."""

from __future__ import annotations

from pathlib import Path

# Supported languages with their display names
LANGUAGES = {
    "en": "English",
    "fr": "Français",
    "es": "Español",
    "zh": "中文",
    "ar": "العربية",
}

# Default language
DEFAULT_LANG = "en"

# Current language (runtime state)
_current_lang: str = DEFAULT_LANG

# Translation strings
TRANSLATIONS = {
    # ==========================================================================
    # Main Menu
    # ==========================================================================
    "menu.language": {
        "en": "Language",
        "fr": "Langue",
        "es": "Idioma",
        "zh": "语言",
        "ar": "اللغة",
    },
    "menu.language.desc": {
        "en": "Change interface language",
        "fr": "Changer la langue",
        "es": "Cambiar el idioma",
        "zh": "更改界面语言",
        "ar": "تغيير اللغة",
    },
    "menu.setup": {
        "en": "Setup",
        "fr": "Configuration",
        "es": "Configuración",
        "zh": "设置",
        "ar": "إعداد",
    },
    "menu.setup.desc": {
        "en": "Configure database location",
        "fr": "Configurer emplacement base",
        "es": "Configurar ubicación de base",
        "zh": "配置数据库位置",
        "ar": "تكوين موقع قاعدة البيانات",
    },
    "menu.install_ide": {
        "en": "Installation & Maintenance",
        "fr": "Installation & Maintenance",
        "es": "Instalación y Mantenimiento",
        "zh": "安装和维护",
        "ar": "التثبيت والصيانة",
    },
    "menu.install_ide.desc": {
        "en": "IDE, backup, restore...",
        "fr": "IDE, backup, restaurer...",
        "es": "IDE, backup, restaurar...",
        "zh": "IDE、备份、恢复...",
        "ar": "IDE، نسخ احتياطي، استعادة...",
    },
    "menu.config": {
        "en": "Configuration & Maintenance",
        "fr": "Install et configuration",
        "es": "Configuración y Mantenimiento",
        "zh": "配置和维护",
        "ar": "التكوين والصيانة",
    },
    "menu.config.desc": {
        "en": "Database, IDE, settings...",
        "fr": "Base, IDE, paramètres...",
        "es": "Base, IDE, ajustes...",
        "zh": "数据库、IDE、设置...",
        "ar": "قاعدة بيانات، IDE، إعدادات...",
    },
    "menu.speckit": {
        "en": "Speckit",
        "fr": "Speckit",
        "es": "Speckit",
        "zh": "Speckit",
        "ar": "Speckit",
    },
    "menu.speckit.desc": {
        "en": "Manage Speckit integration",
        "fr": "Gérer intégration Speckit",
        "es": "Gestionar integración Speckit",
        "zh": "管理Speckit集成",
        "ar": "إدارة تكامل Speckit",
    },
    "menu.research": {
        "en": "Research",
        "fr": "Sources Documentaires",
        "es": "Investigación",
        "zh": "研究",
        "ar": "بحث",
    },
    "menu.research.desc": {
        "en": "Curated sources",
        "fr": "Sources curées",
        "es": "Fuentes curadas",
        "zh": "精选资源",
        "ar": "مصادر منتقاة",
    },
    "menu.add": {
        "en": "Add entry",
        "fr": "Ajouter",
        "es": "Añadir",
        "zh": "添加条目",
        "ar": "إضافة",
    },
    "menu.add.desc": {
        "en": "Add bug/pattern/decision",
        "fr": "Ajouter bug/pattern/décision",
        "es": "Añadir bug/patrón/decisión",
        "zh": "添加bug/模式/决策",
        "ar": "إضافة خطأ/نمط/قرار",
    },
    "menu.search": {
        "en": "Search",
        "fr": "Rechercher",
        "es": "Buscar",
        "zh": "搜索",
        "ar": "بحث",
    },
    "menu.search.desc": {
        "en": "Search the database",
        "fr": "Chercher dans la base",
        "es": "Buscar en la base",
        "zh": "搜索数据库",
        "ar": "البحث في قاعدة البيانات",
    },
    "menu.browse": {
        "en": "Knowledge Base",
        "fr": "Base de souvenirs",
        "es": "Base de conocimiento",
        "zh": "知识库",
        "ar": "قاعدة المعرفة",
    },
    "menu.browse.desc": {
        "en": "Browse, search and add entries",
        "fr": "Parcourir, chercher et ajouter",
        "es": "Explorar, buscar y añadir",
        "zh": "浏览、搜索和添加条目",
        "ar": "تصفح وبحث وإضافة",
    },
    "menu.knowledge_base": {
        "en": "KNOWLEDGE BASE",
        "fr": "BASE DE CONNAISSANCES",
        "es": "BASE DE CONOCIMIENTOS",
        "zh": "知识库",
        "ar": "قاعدة المعرفة",
    },
    "menu.show": {
        "en": "Show",
        "fr": "Afficher",
        "es": "Mostrar",
        "zh": "显示",
        "ar": "عرض",
    },
    "menu.show.desc": {
        "en": "Show entry by ID",
        "fr": "Afficher détail par ID",
        "es": "Mostrar detalle por ID",
        "zh": "按ID显示详情",
        "ar": "عرض التفاصيل بواسطة المعرف",
    },
    "menu.export": {
        "en": "Data",
        "fr": "Sauvegarde et Export",
        "es": "Datos",
        "zh": "数据",
        "ar": "البيانات",
    },
    "menu.export.desc": {
        "en": "Backup, export, import",
        "fr": "Sauvegarde, export, import",
        "es": "Copia, exportar, importar",
        "zh": "备份、导出、导入",
        "ar": "نسخ، تصدير، استيراد",
    },
    "menu.data": {
        "en": "Data Management",
        "fr": "Gestion des données",
        "es": "Gestión de datos",
        "zh": "数据管理",
        "ar": "إدارة البيانات",
    },
    "menu.quit": {
        "en": "Quit",
        "fr": "Quitter",
        "es": "Salir",
        "zh": "退出",
        "ar": "خروج",
    },
    "menu.quit.desc": {
        "en": "Exit (Esc)",
        "fr": "Quitter (Esc)",
        "es": "Salir (Esc)",
        "zh": "退出 (Esc)",
        "ar": "(Esc) خروج",
    },

    # ==========================================================================
    # Banner & Common
    # ==========================================================================
    "banner.subtitle": {
        "en": "Developer Knowledge Management System",
        "fr": "Système de Gestion des Connaissances Développeur",
        "es": "Sistema de Gestión del Conocimiento del Desarrollador",
        "zh": "开发者知识管理系统",
        "ar": "نظام إدارة معرفة المطورين",
    },
    "banner.quote": {
        "en": '"Get your ass to Mars. Quaid... crush those bugs"',
        "fr": '"Get your ass to Mars. Quaid... crush those bugs"',
        "es": '"Get your ass to Mars. Quaid... crush those bugs"',
        "zh": '"Get your ass to Mars. Quaid... crush those bugs"',
        "ar": '"Get your ass to Mars. Quaid... crush those bugs"',
    },
    "common.continue": {
        "en": "Continue...",
        "fr": "Continuer...",
        "es": "Continuar...",
        "zh": "继续...",
        "ar": "متابعة...",
    },
    "common.press_enter": {
        "en": "Press Enter to continue...",
        "fr": "Appuyez sur Entrée...",
        "es": "Presione Enter...",
        "zh": "按回车继续...",
        "ar": "اضغط Enter للمتابعة...",
    },
    "common.back": {
        "en": "← Back",
        "fr": "← Retour",
        "es": "← Volver",
        "zh": "← 返回",
        "ar": "→ رجوع",
    },
    "common.cancel": {
        "en": "Cancel",
        "fr": "Annuler",
        "es": "Cancelar",
        "zh": "取消",
        "ar": "إلغاء",
    },
    "common.confirm": {
        "en": "Confirm",
        "fr": "Confirmer",
        "es": "Confirmar",
        "zh": "确认",
        "ar": "تأكيد",
    },
    "common.yes": {
        "en": "Yes",
        "fr": "Oui",
        "es": "Sí",
        "zh": "是",
        "ar": "نعم",
    },
    "common.no": {
        "en": "No",
        "fr": "Non",
        "es": "No",
        "zh": "否",
        "ar": "لا",
    },
    "common.error": {
        "en": "Error",
        "fr": "Erreur",
        "es": "Error",
        "zh": "错误",
        "ar": "خطأ",
    },
    "common.success": {
        "en": "Success",
        "fr": "Succès",
        "es": "Éxito",
        "zh": "成功",
        "ar": "نجاح",
    },
    "common.goodbye": {
        "en": "Goodbye! Keep crushing those bugs.",
        "fr": "Au revoir ! Continue à écraser ces bugs.",
        "es": "¡Adiós! Sigue aplastando esos bugs.",
        "zh": "再见！继续消灭那些bug。",
        "ar": "وداعاً! استمر في سحق تلك الأخطاء.",
    },
    "common.done": {
        "en": "Done",
        "fr": "Terminé",
        "es": "Hecho",
        "zh": "完成",
        "ar": "تم",
    },

    # ==========================================================================
    # Language Selection
    # ==========================================================================
    "language.title": {
        "en": "Select Language",
        "fr": "Choisir la langue",
        "es": "Seleccionar idioma",
        "zh": "选择语言",
        "ar": "اختر اللغة",
    },
    "language.current": {
        "en": "Current language",
        "fr": "Langue actuelle",
        "es": "Idioma actual",
        "zh": "当前语言",
        "ar": "اللغة الحالية",
    },
    "language.changed": {
        "en": "Language changed to",
        "fr": "Langue changée en",
        "es": "Idioma cambiado a",
        "zh": "语言已更改为",
        "ar": "تم تغيير اللغة إلى",
    },

    # ==========================================================================
    # Entry Types
    # ==========================================================================
    "type.bug": {
        "en": "Bug",
        "fr": "Bug",
        "es": "Bug",
        "zh": "Bug",
        "ar": "خطأ",
    },
    "type.pattern": {
        "en": "Pattern",
        "fr": "Pattern",
        "es": "Patrón",
        "zh": "模式",
        "ar": "نمط",
    },
    "type.decision": {
        "en": "Decision",
        "fr": "Décision",
        "es": "Decisión",
        "zh": "决策",
        "ar": "قرار",
    },
    "type.pitfall": {
        "en": "Pitfall",
        "fr": "Piège",
        "es": "Trampa",
        "zh": "陷阱",
        "ar": "مأزق",
    },
    "type.config": {
        "en": "Config",
        "fr": "Config",
        "es": "Config",
        "zh": "配置",
        "ar": "تكوين",
    },
    "type.reference": {
        "en": "Reference",
        "fr": "Référence",
        "es": "Referencia",
        "zh": "参考",
        "ar": "مرجع",
    },
    "type.snippet": {
        "en": "Snippet",
        "fr": "Snippet",
        "es": "Fragmento",
        "zh": "代码片段",
        "ar": "مقتطف",
    },
    "type.til": {
        "en": "TIL",
        "fr": "TIL",
        "es": "TIL",
        "zh": "今日所学",
        "ar": "تعلمت اليوم",
    },

    # ==========================================================================
    # Setup Menu
    # ==========================================================================
    "setup.title": {
        "en": "Rekall Configuration",
        "fr": "Configuration Rekall",
        "es": "Configuración Rekall",
        "zh": "Rekall配置",
        "ar": "تكوين Rekall",
    },
    "setup.current_source": {
        "en": "Current source",
        "fr": "Source actuelle",
        "es": "Fuente actual",
        "zh": "当前源",
        "ar": "المصدر الحالي",
    },
    "setup.active_db": {
        "en": "Active database",
        "fr": "Base active",
        "es": "Base activa",
        "zh": "活动数据库",
        "ar": "قاعدة البيانات النشطة",
    },
    "setup.global_db": {
        "en": "GLOBAL database",
        "fr": "Base GLOBALE",
        "es": "Base GLOBAL",
        "zh": "全局数据库",
        "ar": "قاعدة البيانات العالمية",
    },
    "setup.local_db": {
        "en": "LOCAL database",
        "fr": "Base LOCALE",
        "es": "Base LOCAL",
        "zh": "本地数据库",
        "ar": "قاعدة البيانات المحلية",
    },
    "setup.not_created": {
        "en": "not created",
        "fr": "non créée",
        "es": "no creada",
        "zh": "未创建",
        "ar": "غير منشأة",
    },
    "setup.use_global": {
        "en": "Use GLOBAL database (existing)",
        "fr": "Utiliser base GLOBALE (existante)",
        "es": "Usar base GLOBAL (existente)",
        "zh": "使用全局数据库（现有）",
        "ar": "استخدام قاعدة البيانات العالمية (موجودة)",
    },
    "setup.create_global": {
        "en": "Create GLOBAL database (XDG)",
        "fr": "Créer base GLOBALE (XDG)",
        "es": "Crear base GLOBAL (XDG)",
        "zh": "创建全局数据库（XDG）",
        "ar": "إنشاء قاعدة بيانات عالمية (XDG)",
    },
    "setup.use_local": {
        "en": "Use LOCAL database (existing)",
        "fr": "Utiliser base LOCALE (existante)",
        "es": "Usar base LOCAL (existente)",
        "zh": "使用本地数据库（现有）",
        "ar": "استخدام قاعدة البيانات المحلية (موجودة)",
    },
    "setup.create_local": {
        "en": "Create LOCAL database (project)",
        "fr": "Créer base LOCALE (projet)",
        "es": "Crear base LOCAL (proyecto)",
        "zh": "创建本地数据库（项目）",
        "ar": "إنشاء قاعدة بيانات محلية (مشروع)",
    },
    "setup.copy_global_to_local": {
        "en": "Copy GLOBAL → LOCAL",
        "fr": "Copier GLOBAL → LOCAL",
        "es": "Copiar GLOBAL → LOCAL",
        "zh": "复制 全局 → 本地",
        "ar": "نسخ عالمي → محلي",
    },
    "setup.copy_local_to_global": {
        "en": "Copy LOCAL → GLOBAL",
        "fr": "Copier LOCAL → GLOBAL",
        "es": "Copiar LOCAL → GLOBAL",
        "zh": "复制 本地 → 全局",
        "ar": "نسخ محلي → عالمي",
    },
    "setup.show_config": {
        "en": "Show detailed config",
        "fr": "Afficher config détaillée",
        "es": "Mostrar config detallada",
        "zh": "显示详细配置",
        "ar": "عرض التكوين المفصل",
    },
    "setup.back": {
        "en": "Back to menu",
        "fr": "Retour au menu",
        "es": "Volver al menú",
        "zh": "返回菜单",
        "ar": "العودة إلى القائمة",
    },

    # ==========================================================================
    # Smart Embeddings Configuration
    # ==========================================================================
    "embeddings.title": {
        "en": "Smart Embeddings Configuration",
        "fr": "Configuration Smart Embeddings",
        "es": "Configuración Smart Embeddings",
        "zh": "智能嵌入配置",
        "ar": "تكوين التضمينات الذكية",
    },
    "embeddings.configure": {
        "en": "Configure Smart Embeddings",
        "fr": "Configurer Smart Embeddings",
        "es": "Configurar Smart Embeddings",
        "zh": "配置智能嵌入",
        "ar": "تكوين التضمينات الذكية",
    },
    "embeddings.description": {
        "en": "Embeddings enable semantic search (find similar entries by meaning, not just keywords).",
        "fr": "Les embeddings permettent la recherche sémantique (trouver des entrées similaires par le sens, pas seulement par mots-clés).",
        "es": "Los embeddings permiten búsqueda semántica (encontrar entradas similares por significado, no solo palabras clave).",
        "zh": "嵌入启用语义搜索（按含义查找相似条目，而不仅仅是关键词）。",
        "ar": "تتيح التضمينات البحث الدلالي (إيجاد مدخلات مشابهة بالمعنى، ليس فقط بالكلمات المفتاحية).",
    },
    "embeddings.warning_download": {
        "en": "⚠ Requires ~90 MB download (first time only)",
        "fr": "⚠ Nécessite ~90 Mo de téléchargement (première fois uniquement)",
        "es": "⚠ Requiere ~90 MB de descarga (solo la primera vez)",
        "zh": "⚠ 需要下载约90 MB（仅首次）",
        "ar": "⚠ يتطلب تحميل ~90 ميجابايت (المرة الأولى فقط)",
    },
    "embeddings.warning_slow": {
        "en": "⚠ May be slow on older machines",
        "fr": "⚠ Peut être lent sur machines anciennes",
        "es": "⚠ Puede ser lento en máquinas antiguas",
        "zh": "⚠ 在旧机器上可能会很慢",
        "ar": "⚠ قد يكون بطيئًا على الأجهزة القديمة",
    },
    "embeddings.enable": {
        "en": "Enable Smart Embeddings",
        "fr": "Activer Smart Embeddings",
        "es": "Activar Smart Embeddings",
        "zh": "启用智能嵌入",
        "ar": "تفعيل التضمينات الذكية",
    },
    "embeddings.disable": {
        "en": "Disable (FTS only)",
        "fr": "Désactiver (FTS uniquement)",
        "es": "Desactivar (solo FTS)",
        "zh": "禁用（仅FTS）",
        "ar": "تعطيل (FTS فقط)",
    },
    "embeddings.status_enabled": {
        "en": "Enabled",
        "fr": "Activé",
        "es": "Activado",
        "zh": "已启用",
        "ar": "مفعّل",
    },
    "embeddings.status_disabled": {
        "en": "Disabled",
        "fr": "Désactivé",
        "es": "Desactivado",
        "zh": "已禁用",
        "ar": "معطّل",
    },
    "embeddings.saved": {
        "en": "Smart Embeddings configuration saved",
        "fr": "Configuration Smart Embeddings sauvegardée",
        "es": "Configuración Smart Embeddings guardada",
        "zh": "智能嵌入配置已保存",
        "ar": "تم حفظ تكوين التضمينات الذكية",
    },
    "embeddings.deps_missing": {
        "en": "Dependencies not installed",
        "fr": "Dépendances non installées",
        "es": "Dependencias no instaladas",
        "zh": "依赖项未安装",
        "ar": "التبعيات غير مثبتة",
    },
    "embeddings.deps_install": {
        "en": "Install with: pip install sentence-transformers numpy",
        "fr": "Installer avec: pip install sentence-transformers numpy",
        "es": "Instalar con: pip install sentence-transformers numpy",
        "zh": "安装方式: pip install sentence-transformers numpy",
        "ar": "التثبيت باستخدام: pip install sentence-transformers numpy",
    },

    # ==========================================================================
    # IDE Integration Menu
    # ==========================================================================
    "ide.title": {
        "en": "IDE/Agent Integrations",
        "fr": "Intégrations IDE/Agent",
        "es": "Integraciones IDE/Agente",
        "zh": "IDE/Agent集成",
        "ar": "تكاملات IDE/Agent",
    },
    "ide.installed": {
        "en": "installed",
        "fr": "installé",
        "es": "instalado",
        "zh": "已安装",
        "ar": "مثبت",
    },
    "ide.not_installed": {
        "en": "not installed",
        "fr": "non installé",
        "es": "no instalado",
        "zh": "未安装",
        "ar": "غير مثبت",
    },
    "ide.not_supported": {
        "en": "not supported",
        "fr": "non supporté",
        "es": "no soportado",
        "zh": "不支持",
        "ar": "غير مدعوم",
    },
    "ide.install_all_local": {
        "en": "Install ALL LOCAL",
        "fr": "Installer TOUT en LOCAL",
        "es": "Instalar TODO LOCAL",
        "zh": "安装全部本地",
        "ar": "تثبيت الكل محلياً",
    },
    "ide.install_all_global": {
        "en": "Install ALL GLOBAL",
        "fr": "Installer TOUT en GLOBAL",
        "es": "Instalar TODO GLOBAL",
        "zh": "安装全部全局",
        "ar": "تثبيت الكل عالمياً",
    },
    "ide.uninstall_all_local": {
        "en": "Uninstall ALL LOCAL",
        "fr": "Désinstaller TOUT LOCAL",
        "es": "Desinstalar TODO LOCAL",
        "zh": "卸载全部本地",
        "ar": "إلغاء تثبيت الكل محلياً",
    },
    "ide.uninstall_all_global": {
        "en": "Uninstall ALL GLOBAL",
        "fr": "Désinstaller TOUT GLOBAL",
        "es": "Desinstalar TODO GLOBAL",
        "zh": "卸载全部全局",
        "ar": "إلغاء تثبيت الكل عالمياً",
    },
    "ide.remaining": {
        "en": "remaining",
        "fr": "restants",
        "es": "restantes",
        "zh": "剩余",
        "ar": "متبقي",
    },
    "ide.manage": {
        "en": "Manage",
        "fr": "Gérer",
        "es": "Gestionar",
        "zh": "管理",
        "ar": "إدارة",
    },
    "ide.install_local": {
        "en": "Install LOCAL (project)",
        "fr": "Installer en LOCAL (projet)",
        "es": "Instalar LOCAL (proyecto)",
        "zh": "安装本地（项目）",
        "ar": "تثبيت محلي (مشروع)",
    },
    "ide.install_global": {
        "en": "Install GLOBAL (~)",
        "fr": "Installer en GLOBAL (~)",
        "es": "Instalar GLOBAL (~)",
        "zh": "安装全局（~）",
        "ar": "تثبيت عالمي (~)",
    },
    "ide.uninstall_local": {
        "en": "Uninstall LOCAL",
        "fr": "Désinstaller LOCAL",
        "es": "Desinstalar LOCAL",
        "zh": "卸载本地",
        "ar": "إلغاء تثبيت محلي",
    },
    "ide.uninstall_global": {
        "en": "Uninstall GLOBAL",
        "fr": "Désinstaller GLOBAL",
        "es": "Desinstalar GLOBAL",
        "zh": "卸载全局",
        "ar": "إلغاء تثبيت عالمي",
    },
    "ide.installation_complete": {
        "en": "Installation complete",
        "fr": "Installation terminée",
        "es": "Instalación completada",
        "zh": "安装完成",
        "ar": "اكتمل التثبيت",
    },
    "ide.uninstallation_complete": {
        "en": "Uninstallation complete",
        "fr": "Désinstallation terminée",
        "es": "Desinstalación completada",
        "zh": "卸载完成",
        "ar": "اكتمل إلغاء التثبيت",
    },

    # ==========================================================================
    # Export/Import Menu
    # ==========================================================================
    "export.title": {
        "en": "Export / Import",
        "fr": "Export / Import",
        "es": "Exportar / Importar",
        "zh": "导出/导入",
        "ar": "تصدير/استيراد",
    },
    "export.archive": {
        "en": "Export (.rekall.zip archive)",
        "fr": "Export (.rekall.zip archive)",
        "es": "Exportar (.rekall.zip archivo)",
        "zh": "导出（.rekall.zip归档）",
        "ar": "تصدير (أرشيف .rekall.zip)",
    },
    "export.markdown": {
        "en": "Export (Markdown)",
        "fr": "Export (Markdown)",
        "es": "Exportar (Markdown)",
        "zh": "导出（Markdown）",
        "ar": "تصدير (Markdown)",
    },
    "export.json": {
        "en": "Export (JSON)",
        "fr": "Export (JSON)",
        "es": "Exportar (JSON)",
        "zh": "导出（JSON）",
        "ar": "تصدير (JSON)",
    },
    "export.new": {
        "en": "New export",
        "fr": "Nouvel export",
        "es": "Nueva exportación",
        "zh": "新导出",
        "ar": "تصدير جديد",
    },
    "export.select_or_new": {
        "en": "Select or create export",
        "fr": "Sélectionner ou créer",
        "es": "Seleccionar o crear",
        "zh": "选择或创建",
        "ar": "اختر أو أنشئ",
    },
    "export.overwrite": {
        "en": "Overwrite",
        "fr": "Écraser",
        "es": "Sobrescribir",
        "zh": "覆盖",
        "ar": "استبدال",
    },
    "export.confirm_overwrite": {
        "en": "Confirm overwrite",
        "fr": "Confirmer écrasement",
        "es": "Confirmar sobrescritura",
        "zh": "确认覆盖",
        "ar": "تأكيد الاستبدال",
    },
    "import.archive": {
        "en": "Import (.rekall.zip archive)",
        "fr": "Import (.rekall.zip archive)",
        "es": "Importar (.rekall.zip archivo)",
        "zh": "导入（.rekall.zip归档）",
        "ar": "استيراد (أرشيف .rekall.zip)",
    },
    "import.external_db": {
        "en": "Import (external knowledge.db)",
        "fr": "Import (knowledge.db externe)",
        "es": "Importar (knowledge.db externo)",
        "zh": "导入（外部knowledge.db）",
        "ar": "استيراد (knowledge.db خارجي)",
    },

    # ==========================================================================
    # Add Entry
    # ==========================================================================
    "add.type": {
        "en": "Entry type",
        "fr": "Type d'entrée",
        "es": "Tipo de entrada",
        "zh": "条目类型",
        "ar": "نوع الإدخال",
    },
    "add.title": {
        "en": "Title",
        "fr": "Titre",
        "es": "Título",
        "zh": "标题",
        "ar": "العنوان",
    },
    "add.tags": {
        "en": "Tags (comma-separated)",
        "fr": "Tags (séparés par virgule)",
        "es": "Etiquetas (separadas por coma)",
        "zh": "标签（逗号分隔）",
        "ar": "الوسوم (مفصولة بفاصلة)",
    },
    "add.project": {
        "en": "Project",
        "fr": "Projet",
        "es": "Proyecto",
        "zh": "项目",
        "ar": "المشروع",
    },
    "add.confidence": {
        "en": "Confidence level",
        "fr": "Niveau de confiance",
        "es": "Nivel de confianza",
        "zh": "置信度",
        "ar": "مستوى الثقة",
    },
    "add.content": {
        "en": "Content (optional)",
        "fr": "Contenu (optionnel)",
        "es": "Contenido (opcional)",
        "zh": "内容（可选）",
        "ar": "المحتوى (اختياري)",
    },
    "add.success": {
        "en": "Entry added",
        "fr": "Entrée ajoutée",
        "es": "Entrada añadida",
        "zh": "条目已添加",
        "ar": "تمت إضافة الإدخال",
    },
    "add.required": {
        "en": "This field is required.",
        "fr": "Ce champ est requis.",
        "es": "Este campo es obligatorio.",
        "zh": "此字段为必填项。",
        "ar": "هذا الحقل مطلوب.",
    },

    # ==========================================================================
    # Search
    # ==========================================================================
    "search.query": {
        "en": "Search query",
        "fr": "Recherche",
        "es": "Buscar",
        "zh": "搜索查询",
        "ar": "استعلام البحث",
    },
    "search.no_results": {
        "en": "No results found.",
        "fr": "Aucun résultat trouvé.",
        "es": "No se encontraron resultados.",
        "zh": "未找到结果。",
        "ar": "لم يتم العثور على نتائج.",
    },
    "search.results_for": {
        "en": "Results for",
        "fr": "Résultats pour",
        "es": "Resultados para",
        "zh": "搜索结果",
        "ar": "نتائج البحث عن",
    },
    "search.results_found": {
        "en": "results found",
        "fr": "résultats trouvés",
        "es": "resultados encontrados",
        "zh": "个结果",
        "ar": "نتيجة",
    },

    # ==========================================================================
    # Browse
    # ==========================================================================
    "browse.no_entries": {
        "en": "No entries in database.",
        "fr": "Aucune entrée dans la base.",
        "es": "No hay entradas en la base.",
        "zh": "数据库中没有条目。",
        "ar": "لا توجد إدخالات في قاعدة البيانات.",
    },
    "browse.entries": {
        "en": "entries",
        "fr": "entrées",
        "es": "entradas",
        "zh": "条目",
        "ar": "إدخالات",
    },
    "browse.navigate": {
        "en": "Up/Down/jk: navigate | Enter: select | q: quit",
        "fr": "Haut/Bas/jk: naviguer | Entrée: sélectionner | q: quitter",
        "es": "Arriba/Abajo/jk: navegar | Enter: seleccionar | q: salir",
        "zh": "上/下/jk: 导航 | 回车: 选择 | q: 退出",
        "ar": "أعلى/أسفل/jk: تنقل | Enter: اختيار | q: خروج",
    },
    "browse.back_to_list": {
        "en": "Back to list",
        "fr": "Retour à la liste",
        "es": "Volver a la lista",
        "zh": "返回列表",
        "ar": "العودة إلى القائمة",
    },
    "browse.edit_entry": {
        "en": "Edit this entry",
        "fr": "Éditer cette entrée",
        "es": "Editar esta entrada",
        "zh": "编辑此条目",
        "ar": "تحرير هذا الإدخال",
    },
    "browse.delete_entry": {
        "en": "Delete this entry",
        "fr": "Supprimer cette entrée",
        "es": "Eliminar esta entrada",
        "zh": "删除此条目",
        "ar": "حذف هذا الإدخال",
    },
    "browse.confirm_delete": {
        "en": "Delete '{title}'?",
        "fr": "Supprimer '{title}' ?",
        "es": "¿Eliminar '{title}'?",
        "zh": "删除 '{title}'？",
        "ar": "حذف '{title}'؟",
    },
    "browse.deleted": {
        "en": "Entry deleted!",
        "fr": "Entrée supprimée !",
        "es": "¡Entrada eliminada!",
        "zh": "条目已删除！",
        "ar": "تم حذف الإدخال!",
    },
    "browse.delete_error": {
        "en": "Deletion failed",
        "fr": "Échec de la suppression",
        "es": "Error al eliminar",
        "zh": "删除失败",
        "ar": "فشل الحذف",
    },
    "browse.links_warning": {
        "en": "{count} link(s) will be removed",
        "fr": "{count} lien(s) seront supprimés",
        "es": "{count} enlace(s) serán eliminados",
        "zh": "将删除 {count} 个链接",
        "ar": "سيتم حذف {count} رابط(روابط)",
    },
    "browse.confirm_yes": {
        "en": "Yes, delete",
        "fr": "Oui, supprimer",
        "es": "Sí, eliminar",
        "zh": "是，删除",
        "ar": "نعم، حذف",
    },
    "browse.confirm_no": {
        "en": "No, cancel",
        "fr": "Non, annuler",
        "es": "No, cancelar",
        "zh": "否，取消",
        "ar": "لا، إلغاء",
    },
    "browse.updated": {
        "en": "Entry updated!",
        "fr": "Entrée mise à jour !",
        "es": "¡Entrada actualizada!",
        "zh": "条目已更新！",
        "ar": "تم تحديث الإدخال!",
    },

    # ==========================================================================
    # Actions
    # ==========================================================================
    "action.actions": {
        "en": "Actions",
        "fr": "Actions",
        "es": "Acciones",
        "zh": "操作",
        "ar": "إجراءات",
    },
    "action.back": {
        "en": "Back",
        "fr": "Retour",
        "es": "Volver",
        "zh": "返回",
        "ar": "رجوع",
    },
    "action.project": {
        "en": "Project",
        "fr": "Projet",
        "es": "Proyecto",
        "zh": "项目",
        "ar": "مشروع",
    },

    # ==========================================================================
    # IDE Management (single)
    # ==========================================================================
    "ide.location": {
        "en": "Location",
        "fr": "Emplacement",
        "es": "Ubicación",
        "zh": "位置",
        "ar": "الموقع",
    },
    "ide.status": {
        "en": "Status",
        "fr": "Statut",
        "es": "Estado",
        "zh": "状态",
        "ar": "الحالة",
    },
    "ide.path": {
        "en": "Path",
        "fr": "Chemin",
        "es": "Ruta",
        "zh": "路径",
        "ar": "المسار",
    },
    "ide.confirm_uninstall": {
        "en": "Confirm uninstall {loc}?",
        "fr": "Confirmer la désinstallation {loc} ?",
        "es": "¿Confirmar desinstalación {loc}?",
        "zh": "确认卸载 {loc}？",
        "ar": "تأكيد إلغاء التثبيت {loc}؟",
    },
    "ide.yes_uninstall": {
        "en": "Yes, uninstall all {loc}",
        "fr": "Oui, désinstaller tout {loc}",
        "es": "Sí, desinstalar todo {loc}",
        "zh": "是，卸载全部 {loc}",
        "ar": "نعم، إلغاء تثبيت الكل {loc}",
    },
    "ide.installed_at": {
        "en": "{name} installed {loc}",
        "fr": "{name} installé en {loc}",
        "es": "{name} instalado en {loc}",
        "zh": "{name} 已安装 {loc}",
        "ar": "{name} مثبت في {loc}",
    },
    "ide.uninstalled": {
        "en": "{name} uninstalled ({loc})",
        "fr": "{name} désinstallé ({loc})",
        "es": "{name} desinstalado ({loc})",
        "zh": "{name} 已卸载 ({loc})",
        "ar": "{name} تم إلغاء التثبيت ({loc})",
    },
    "ide.was_not_installed": {
        "en": "{name} was not installed {loc}",
        "fr": "{name} n'était pas installé en {loc}",
        "es": "{name} no estaba instalado en {loc}",
        "zh": "{name} 未安装在 {loc}",
        "ar": "{name} لم يكن مثبتاً في {loc}",
    },
    "ide.integrations": {
        "en": "IDE Integrations",
        "fr": "Intégrations IDE",
        "es": "Integraciones IDE",
        "zh": "IDE集成",
        "ar": "تكاملات IDE",
    },
    "ide.install": {
        "en": "Install",
        "fr": "Installer",
        "es": "Instalar",
        "zh": "安装",
        "ar": "تثبيت",
    },
    "ide.uninstall": {
        "en": "Uninstall",
        "fr": "Désinstaller",
        "es": "Desinstalar",
        "zh": "卸载",
        "ar": "إلغاء التثبيت",
    },

    # ==========================================================================
    # Speckit
    # ==========================================================================
    "speckit.title": {
        "en": "Speckit Integration Manager",
        "fr": "Gestionnaire d'intégration Speckit",
        "es": "Gestor de integración Speckit",
        "zh": "Speckit集成管理器",
        "ar": "مدير تكامل Speckit",
    },
    "speckit.component": {
        "en": "Component",
        "fr": "Composant",
        "es": "Componente",
        "zh": "组件",
        "ar": "المكون",
    },
    "speckit.file_missing": {
        "en": "File missing",
        "fr": "Fichier manquant",
        "es": "Archivo faltante",
        "zh": "文件缺失",
        "ar": "الملف مفقود",
    },
    "speckit.select_install": {
        "en": "Select components to install...",
        "fr": "Sélectionner composants à installer...",
        "es": "Seleccionar componentes a instalar...",
        "zh": "选择要安装的组件...",
        "ar": "اختر المكونات للتثبيت...",
    },
    "speckit.select_uninstall": {
        "en": "Select components to uninstall...",
        "fr": "Sélectionner composants à désinstaller...",
        "es": "Seleccionar componentes a desinstalar...",
        "zh": "选择要卸载的组件...",
        "ar": "اختر المكونات لإلغاء التثبيت...",
    },
    "speckit.install_all": {
        "en": "Install ALL components",
        "fr": "Installer TOUS les composants",
        "es": "Instalar TODOS los componentes",
        "zh": "安装所有组件",
        "ar": "تثبيت جميع المكونات",
    },
    "speckit.uninstall_all": {
        "en": "Uninstall ALL components",
        "fr": "Désinstaller TOUS les composants",
        "es": "Desinstalar TODOS los componentes",
        "zh": "卸载所有组件",
        "ar": "إلغاء تثبيت جميع المكونات",
    },
    "speckit.all_installed": {
        "en": "All components are already installed.",
        "fr": "Tous les composants sont déjà installés.",
        "es": "Todos los componentes ya están instalados.",
        "zh": "所有组件已安装。",
        "ar": "جميع المكونات مثبتة بالفعل.",
    },
    "speckit.none_installed": {
        "en": "No components are installed.",
        "fr": "Aucun composant n'est installé.",
        "es": "Ningún componente está instalado.",
        "zh": "没有组件已安装。",
        "ar": "لا توجد مكونات مثبتة.",
    },
    "speckit.select_toggle": {
        "en": "Space=toggle, Enter=confirm",
        "fr": "Espace=basculer, Entrée=confirmer",
        "es": "Espacio=alternar, Enter=confirmar",
        "zh": "空格=切换，回车=确认",
        "ar": "مسافة=تبديل، إدخال=تأكيد",
    },
    "speckit.all_select": {
        "en": "[All] Select/Deselect All",
        "fr": "[Tout] Sélectionner/Désélectionner tout",
        "es": "[Todo] Seleccionar/Deseleccionar todo",
        "zh": "[全部] 全选/取消全选",
        "ar": "[الكل] تحديد/إلغاء تحديد الكل",
    },
    "speckit.none_selected": {
        "en": "No components selected.",
        "fr": "Aucun composant sélectionné.",
        "es": "Ningún componente seleccionado.",
        "zh": "未选择组件。",
        "ar": "لم يتم تحديد مكونات.",
    },
    "speckit.preview": {
        "en": "Preview",
        "fr": "Aperçu",
        "es": "Vista previa",
        "zh": "预览",
        "ar": "معاينة",
    },
    "speckit.apply_changes": {
        "en": "Apply these changes?",
        "fr": "Appliquer ces changements ?",
        "es": "¿Aplicar estos cambios?",
        "zh": "应用这些更改？",
        "ar": "تطبيق هذه التغييرات؟",
    },
    "speckit.yes_action": {
        "en": "Yes, {action} {count} component(s)",
        "fr": "Oui, {action} {count} composant(s)",
        "es": "Sí, {action} {count} componente(s)",
        "zh": "是，{action} {count} 个组件",
        "ar": "نعم، {action} {count} مكون(ات)",
    },
    "speckit.skipped": {
        "en": "Skipped",
        "fr": "Ignorés",
        "es": "Omitidos",
        "zh": "已跳过",
        "ar": "تم التخطي",
    },
    "speckit.errors": {
        "en": "Errors",
        "fr": "Erreurs",
        "es": "Errores",
        "zh": "错误",
        "ar": "أخطاء",
    },
    "speckit.removed": {
        "en": "Removed",
        "fr": "Supprimés",
        "es": "Eliminados",
        "zh": "已删除",
        "ar": "تمت الإزالة",
    },
    "speckit.yes_install": {
        "en": "Yes, install",
        "fr": "Oui, installer",
        "es": "Sí, instalar",
        "zh": "是，安装",
        "ar": "نعم، تثبيت",
    },
    "speckit.yes_uninstall": {
        "en": "Yes, uninstall",
        "fr": "Oui, désinstaller",
        "es": "Sí, desinstalar",
        "zh": "是，卸载",
        "ar": "نعم، إلغاء تثبيت",
    },
    "speckit.yes_install_all": {
        "en": "Yes, install all",
        "fr": "Oui, tout installer",
        "es": "Sí, instalar todo",
        "zh": "是，全部安装",
        "ar": "نعم، تثبيت الكل",
    },
    "speckit.yes_uninstall_all": {
        "en": "Yes, uninstall all",
        "fr": "Oui, tout désinstaller",
        "es": "Sí, desinstalar todo",
        "zh": "是，全部卸载",
        "ar": "نعم، إلغاء تثبيت الكل",
    },
    "speckit.remove_integration": {
        "en": "Remove all Rekall integration?",
        "fr": "Supprimer toute l'intégration Rekall ?",
        "es": "¿Eliminar toda la integración Rekall?",
        "zh": "删除所有Rekall集成？",
        "ar": "إزالة جميع تكامل Rekall؟",
    },
    "speckit.note_regex": {
        "en": "Note: Files are cleaned via regex, not restored from backup.",
        "fr": "Note : Les fichiers sont nettoyés par regex, pas restaurés depuis une sauvegarde.",
        "es": "Nota: Los archivos se limpian con regex, no se restauran desde copia.",
        "zh": "注意：文件通过正则表达式清理，不是从备份恢复。",
        "ar": "ملاحظة: يتم تنظيف الملفات عبر التعبيرات النمطية، وليس استعادتها من النسخة الاحتياطية.",
    },

    # ==========================================================================
    # Research
    # ==========================================================================
    "research.no_files": {
        "en": "No research files found.",
        "fr": "Aucun fichier de recherche trouvé.",
        "es": "No se encontraron archivos de investigación.",
        "zh": "未找到研究文件。",
        "ar": "لم يتم العثور على ملفات بحث.",
    },
    "research.choose_topic": {
        "en": "Choose research topic",
        "fr": "Choisir un sujet de recherche",
        "es": "Elegir tema de investigación",
        "zh": "选择研究主题",
        "ar": "اختر موضوع البحث",
    },
    "research.files": {
        "en": "files",
        "fr": "fichiers",
        "es": "archivos",
        "zh": "文件",
        "ar": "ملفات",
    },
    "research.topic": {
        "en": "Topic",
        "fr": "Sujet",
        "es": "Tema",
        "zh": "主题",
        "ar": "الموضوع",
    },

    # ==========================================================================
    # Browse details
    # ==========================================================================
    "browse.type": {
        "en": "Type",
        "fr": "Type",
        "es": "Tipo",
        "zh": "类型",
        "ar": "النوع",
    },
    "browse.confidence": {
        "en": "Confidence",
        "fr": "Confiance",
        "es": "Confianza",
        "zh": "置信度",
        "ar": "الثقة",
    },
    "browse.tags": {
        "en": "Tags",
        "fr": "Tags",
        "es": "Etiquetas",
        "zh": "标签",
        "ar": "الوسوم",
    },
    "browse.content": {
        "en": "Content",
        "fr": "Contenu",
        "es": "Contenido",
        "zh": "内容",
        "ar": "المحتوى",
    },
    "browse.created": {
        "en": "Created",
        "fr": "Créé",
        "es": "Creado",
        "zh": "创建于",
        "ar": "تم الإنشاء",
    },
    "browse.updated_at": {
        "en": "Updated",
        "fr": "Modifié",
        "es": "Actualizado",
        "zh": "更新于",
        "ar": "تم التحديث",
    },
    "browse.id": {
        "en": "ID",
        "fr": "ID",
        "es": "ID",
        "zh": "ID",
        "ar": "المعرف",
    },
    "browse.status": {
        "en": "Status",
        "fr": "Statut",
        "es": "Estado",
        "zh": "状态",
        "ar": "الحالة",
    },
    "browse.no_content": {
        "en": "No content",
        "fr": "Pas de contenu",
        "es": "Sin contenido",
        "zh": "无内容",
        "ar": "لا يوجد محتوى",
    },
    "browse.preview": {
        "en": "Preview",
        "fr": "Aperçu",
        "es": "Vista previa",
        "zh": "预览",
        "ar": "معاينة",
    },
    "browse.access": {
        "en": "Access",
        "fr": "Accès",
        "es": "Acceso",
        "zh": "访问",
        "ar": "الوصول",
    },
    "browse.score": {
        "en": "Score",
        "fr": "Score",
        "es": "Puntuación",
        "zh": "分数",
        "ar": "النتيجة",
    },
    "browse.links_in": {
        "en": "In",
        "fr": "In",
        "es": "Ent",
        "zh": "入",
        "ar": "داخل",
    },
    "browse.links_out": {
        "en": "Out",
        "fr": "Out",
        "es": "Sal",
        "zh": "出",
        "ar": "خارج",
    },
    "browse.legend_title": {
        "en": "Column Legend",
        "fr": "Légende des colonnes",
        "es": "Leyenda de columnas",
        "zh": "列说明",
        "ar": "دليل الأعمدة",
    },
    "browse.graph_title": {
        "en": "Knowledge Graph",
        "fr": "Graphe de connexions",
        "es": "Grafo de conexiones",
        "zh": "知识图谱",
        "ar": "رسم المعرفة",
    },
    "browse.legend_content": {
        "en": """[bold]─── Identification ───[/bold]
[cyan]Type[/cyan]      bug, pattern, decision, pitfall, config, reference
[cyan]Project[/cyan]   Associated project name
[cyan]Title[/cyan]     Entry title (truncated in table)

[bold]─── Timestamps ───[/bold]
[cyan]Created[/cyan]   When the entry was first created
[cyan]Updated[/cyan]   Last modification date

[bold]─── Cognitive Metrics ───[/bold]
[cyan]Conf[/cyan]      Confidence level 0-5 (how reliable is this?)
[cyan]Access[/cyan]    Number of times you consulted this entry
[cyan]Score[/cyan]     Consolidation score 0.00-1.00
            [red]< 0.40[/red] fragile  [yellow]0.40-0.70[/yellow] moderate  [green]> 0.70[/green] solid

[bold]─── Knowledge Graph ───[/bold]
[cyan]In[/cyan]        Incoming links (other entries reference this one)
[cyan]Out[/cyan]       Outgoing links (this entry references others)""",
        "fr": """[bold]─── Identification ───[/bold]
[cyan]Type[/cyan]      bug, pattern, decision, pitfall, config, reference
[cyan]Projet[/cyan]    Nom du projet associé
[cyan]Titre[/cyan]     Titre de l'entrée (tronqué dans le tableau)

[bold]─── Dates ───[/bold]
[cyan]Créé[/cyan]      Date de création de l'entrée
[cyan]Modifié[/cyan]   Date de dernière modification

[bold]─── Métriques cognitives ───[/bold]
[cyan]Conf[/cyan]      Niveau de confiance 0-5 (fiabilité de l'info)
[cyan]Accès[/cyan]     Nombre de fois que tu as consulté cette entrée
[cyan]Score[/cyan]     Score de consolidation 0.00-1.00
            [red]< 0.40[/red] fragile  [yellow]0.40-0.70[/yellow] modéré  [green]> 0.70[/green] solide

[bold]─── Knowledge Graph ───[/bold]
[cyan]In[/cyan]        Liens entrants (autres entrées qui référencent celle-ci)
[cyan]Out[/cyan]       Liens sortants (entrées référencées par celle-ci)""",
        "es": """[bold]─── Identificación ───[/bold]
[cyan]Tipo[/cyan]      bug, pattern, decision, pitfall, config, reference
[cyan]Proyecto[/cyan]  Nombre del proyecto asociado
[cyan]Título[/cyan]    Título de la entrada

[bold]─── Fechas ───[/bold]
[cyan]Creado[/cyan]    Fecha de creación
[cyan]Actual.[/cyan]   Fecha de última actualización

[bold]─── Métricas cognitivas ───[/bold]
[cyan]Conf[/cyan]      Nivel de confianza 0-5
[cyan]Acceso[/cyan]    Número de consultas
[cyan]Punt.[/cyan]     Puntuación de consolidación 0.00-1.00
            [red]< 0.40[/red] frágil  [yellow]0.40-0.70[/yellow] moderado  [green]> 0.70[/green] sólido

[bold]─── Knowledge Graph ───[/bold]
[cyan]Ent[/cyan]       Enlaces entrantes
[cyan]Sal[/cyan]       Enlaces salientes""",
        "zh": """[bold]─── 标识 ───[/bold]
[cyan]类型[/cyan]      bug, pattern, decision, pitfall, config, reference
[cyan]项目[/cyan]      关联项目名称
[cyan]标题[/cyan]      条目标题

[bold]─── 时间戳 ───[/bold]
[cyan]创建[/cyan]      创建日期
[cyan]更新[/cyan]      最后更新日期

[bold]─── 认知指标 ───[/bold]
[cyan]信任[/cyan]      信任级别 0-5
[cyan]访问[/cyan]      访问次数
[cyan]分数[/cyan]      巩固分数 0.00-1.00
            [red]< 0.40[/red] 脆弱  [yellow]0.40-0.70[/yellow] 中等  [green]> 0.70[/green] 稳固

[bold]─── 知识图谱 ───[/bold]
[cyan]入[/cyan]        入链接
[cyan]出[/cyan]        出链接""",
        "ar": """[bold]─── التعريف ───[/bold]
[cyan]النوع[/cyan]     bug, pattern, decision, pitfall, config, reference
[cyan]المشروع[/cyan]   اسم المشروع المرتبط
[cyan]العنوان[/cyan]   عنوان الإدخال

[bold]─── التواريخ ───[/bold]
[cyan]إنشاء[/cyan]     تاريخ الإنشاء
[cyan]تحديث[/cyan]     تاريخ آخر تحديث

[bold]─── المقاييس المعرفية ───[/bold]
[cyan]ثقة[/cyan]       مستوى الثقة 0-5
[cyan]وصول[/cyan]      عدد مرات الوصول
[cyan]نتيجة[/cyan]     نتيجة التوحيد 0.00-1.00
            [red]< 0.40[/red] هش  [yellow]0.40-0.70[/yellow] معتدل  [green]> 0.70[/green] صلب

[bold]─── رسم المعرفة ───[/bold]
[cyan]داخل[/cyan]      روابط واردة
[cyan]خارج[/cyan]      روابط صادرة""",
    },

    # ==========================================================================
    # Edit entry
    # ==========================================================================
    "edit.title": {
        "en": "Edit entry",
        "fr": "Édition de l'entrée",
        "es": "Editar entrada",
        "zh": "编辑条目",
        "ar": "تحرير الإدخال",
    },
    "edit.keep_current": {
        "en": "Leave empty to keep current value",
        "fr": "Laisser vide pour garder la valeur actuelle",
        "es": "Dejar vacío para mantener el valor actual",
        "zh": "留空以保留当前值",
        "ar": "اتركه فارغاً للاحتفاظ بالقيمة الحالية",
    },
    "edit.current_content": {
        "en": "Current content",
        "fr": "Contenu actuel",
        "es": "Contenido actual",
        "zh": "当前内容",
        "ar": "المحتوى الحالي",
    },
    "edit.new_content": {
        "en": "New content (or Enter to keep)",
        "fr": "Nouveau contenu (ou Entrée pour garder)",
        "es": "Nuevo contenido (o Enter para mantener)",
        "zh": "新内容（或回车保留）",
        "ar": "محتوى جديد (أو Enter للاحتفاظ)",
    },
    "edit.none": {
        "en": "none",
        "fr": "aucun",
        "es": "ninguno",
        "zh": "无",
        "ar": "لا شيء",
    },

    # ==========================================================================
    # Show entry
    # ==========================================================================
    "show.entry_id": {
        "en": "Entry ID (or prefix)",
        "fr": "ID de l'entrée (ou préfixe)",
        "es": "ID de entrada (o prefijo)",
        "zh": "条目ID（或前缀）",
        "ar": "معرف الإدخال (أو البادئة)",
    },
    "show.not_found": {
        "en": "Entry not found",
        "fr": "Entrée non trouvée",
        "es": "Entrada no encontrada",
        "zh": "未找到条目",
        "ar": "الإدخال غير موجود",
    },

    # ==========================================================================
    # Table headers
    # ==========================================================================
    "table.description": {
        "en": "Description",
        "fr": "Description",
        "es": "Descripción",
        "zh": "描述",
        "ar": "الوصف",
    },
    "table.local": {
        "en": "Local",
        "fr": "Local",
        "es": "Local",
        "zh": "本地",
        "ar": "محلي",
    },
    "table.global": {
        "en": "Global",
        "fr": "Global",
        "es": "Global",
        "zh": "全局",
        "ar": "عالمي",
    },
    "table.parameter": {
        "en": "Parameter",
        "fr": "Paramètre",
        "es": "Parámetro",
        "zh": "参数",
        "ar": "المعامل",
    },
    "table.value": {
        "en": "Value",
        "fr": "Valeur",
        "es": "Valor",
        "zh": "值",
        "ar": "القيمة",
    },

    # ==========================================================================
    # Config details
    # ==========================================================================
    "config.detailed": {
        "en": "Detailed Configuration",
        "fr": "Configuration Détaillée",
        "es": "Configuración Detallada",
        "zh": "详细配置",
        "ar": "التكوين المفصل",
    },
    "config.source": {
        "en": "Source",
        "fr": "Source",
        "es": "Fuente",
        "zh": "来源",
        "ar": "المصدر",
    },
    "config.config_dir": {
        "en": "Config dir",
        "fr": "Dossier config",
        "es": "Dir config",
        "zh": "配置目录",
        "ar": "مجلد التكوين",
    },
    "config.data_dir": {
        "en": "Data dir",
        "fr": "Dossier données",
        "es": "Dir datos",
        "zh": "数据目录",
        "ar": "مجلد البيانات",
    },
    "config.cache_dir": {
        "en": "Cache dir",
        "fr": "Dossier cache",
        "es": "Dir caché",
        "zh": "缓存目录",
        "ar": "مجلد التخزين المؤقت",
    },
    "config.db_path": {
        "en": "DB path",
        "fr": "Chemin DB",
        "es": "Ruta DB",
        "zh": "数据库路径",
        "ar": "مسار قاعدة البيانات",
    },
    "config.db_exists": {
        "en": "DB exists",
        "fr": "DB existe",
        "es": "DB existe",
        "zh": "数据库存在",
        "ar": "قاعدة البيانات موجودة",
    },
    "config.not_set": {
        "en": "not set",
        "fr": "non défini",
        "es": "no definido",
        "zh": "未设置",
        "ar": "غير محدد",
    },

    # ==========================================================================
    # Migration
    # ==========================================================================
    "migrate.title": {
        "en": "Migration",
        "fr": "Migration",
        "es": "Migración",
        "zh": "迁移",
        "ar": "الترحيل",
    },
    "migrate.source": {
        "en": "Source",
        "fr": "Source",
        "es": "Fuente",
        "zh": "源",
        "ar": "المصدر",
    },
    "migrate.destination": {
        "en": "Destination",
        "fr": "Destination",
        "es": "Destino",
        "zh": "目标",
        "ar": "الوجهة",
    },
    "migrate.dest_exists": {
        "en": "Destination already exists!",
        "fr": "La destination existe déjà !",
        "es": "¡El destino ya existe!",
        "zh": "目标已存在！",
        "ar": "الوجهة موجودة بالفعل!",
    },
    "migrate.overwrite": {
        "en": "Overwrite destination",
        "fr": "Écraser la destination",
        "es": "Sobrescribir destino",
        "zh": "覆盖目标",
        "ar": "الكتابة فوق الوجهة",
    },
    "migrate.confirm_copy": {
        "en": "Confirm copy?",
        "fr": "Confirmer la copie ?",
        "es": "¿Confirmar copia?",
        "zh": "确认复制？",
        "ar": "تأكيد النسخ؟",
    },
    "migrate.yes_copy": {
        "en": "Yes, copy database",
        "fr": "Oui, copier la base",
        "es": "Sí, copiar la base",
        "zh": "是，复制数据库",
        "ar": "نعم، نسخ قاعدة البيانات",
    },
    "migrate.copied": {
        "en": "Database copied",
        "fr": "Base copiée",
        "es": "Base copiada",
        "zh": "数据库已复制",
        "ar": "تم نسخ قاعدة البيانات",
    },

    # ==========================================================================
    # Setup Global/Local
    # ==========================================================================
    "setup.global_install": {
        "en": "Global Installation (XDG)",
        "fr": "Installation Globale (XDG)",
        "es": "Instalación Global (XDG)",
        "zh": "全局安装（XDG）",
        "ar": "التثبيت العالمي (XDG)",
    },
    "setup.local_install": {
        "en": "Local Installation (Project)",
        "fr": "Installation Locale (Projet)",
        "es": "Instalación Local (Proyecto)",
        "zh": "本地安装（项目）",
        "ar": "التثبيت المحلي (مشروع)",
    },
    "setup.config": {
        "en": "Config",
        "fr": "Config",
        "es": "Config",
        "zh": "配置",
        "ar": "التكوين",
    },
    "setup.data": {
        "en": "Data",
        "fr": "Données",
        "es": "Datos",
        "zh": "数据",
        "ar": "البيانات",
    },
    "setup.cache": {
        "en": "Cache",
        "fr": "Cache",
        "es": "Caché",
        "zh": "缓存",
        "ar": "التخزين المؤقت",
    },
    "setup.db": {
        "en": "DB",
        "fr": "DB",
        "es": "DB",
        "zh": "数据库",
        "ar": "قاعدة البيانات",
    },
    "setup.folder": {
        "en": "Folder",
        "fr": "Dossier",
        "es": "Carpeta",
        "zh": "文件夹",
        "ar": "المجلد",
    },
    "setup.db_exists": {
        "en": "Database already exists.",
        "fr": "La base de données existe déjà.",
        "es": "La base de datos ya existe.",
        "zh": "数据库已存在。",
        "ar": "قاعدة البيانات موجودة بالفعل.",
    },
    "setup.open_existing": {
        "en": "Open existing database",
        "fr": "Ouvrir la base existante",
        "es": "Abrir base existente",
        "zh": "打开现有数据库",
        "ar": "فتح قاعدة البيانات الموجودة",
    },
    "setup.create_db": {
        "en": "Create database?",
        "fr": "Créer la base de données ?",
        "es": "¿Crear la base de datos?",
        "zh": "创建数据库？",
        "ar": "إنشاء قاعدة البيانات؟",
    },
    "setup.yes_create_global": {
        "en": "Yes, create global database",
        "fr": "Oui, créer la base globale",
        "es": "Sí, crear base global",
        "zh": "是，创建全局数据库",
        "ar": "نعم، إنشاء قاعدة بيانات عالمية",
    },
    "setup.global_initialized": {
        "en": "Global database initialized",
        "fr": "Base globale initialisée",
        "es": "Base global inicializada",
        "zh": "全局数据库已初始化",
        "ar": "تم تهيئة قاعدة البيانات العالمية",
    },
    "setup.use_without_options": {
        "en": "Use 'rekall' without options to use this database.",
        "fr": "Utilisez 'rekall' sans options pour utiliser cette base.",
        "es": "Use 'rekall' sin opciones para usar esta base.",
        "zh": "使用不带选项的 'rekall' 来使用此数据库。",
        "ar": "استخدم 'rekall' بدون خيارات لاستخدام قاعدة البيانات هذه.",
    },
    "setup.gitignore_created": {
        "en": "A .gitignore file will be created with suggestions.",
        "fr": "Un fichier .gitignore sera créé avec des suggestions.",
        "es": "Se creará un archivo .gitignore con sugerencias.",
        "zh": "将创建一个带有建议的 .gitignore 文件。",
        "ar": "سيتم إنشاء ملف .gitignore مع اقتراحات.",
    },
    "setup.version_db": {
        "en": "Version DB in Git?",
        "fr": "Versionner la base dans Git ?",
        "es": "¿Versionar la DB en Git?",
        "zh": "在Git中版本控制数据库？",
        "ar": "إصدار قاعدة البيانات في Git؟",
    },
    "setup.version_share_team": {
        "en": "Version DB (share with team)",
        "fr": "Versionner la DB (partage équipe)",
        "es": "Versionar DB (compartir equipo)",
        "zh": "版本控制数据库（团队共享）",
        "ar": "إصدار قاعدة البيانات (مشاركة الفريق)",
    },
    "setup.exclude_local": {
        "en": "Exclude DB from Git (local data)",
        "fr": "Exclure la DB du Git (données locales)",
        "es": "Excluir DB de Git (datos locales)",
        "zh": "从Git排除数据库（本地数据）",
        "ar": "استبعاد قاعدة البيانات من Git (بيانات محلية)",
    },
    "setup.local_initialized": {
        "en": "Local project initialized",
        "fr": "Projet local initialisé",
        "es": "Proyecto local inicializado",
        "zh": "本地项目已初始化",
        "ar": "تم تهيئة المشروع المحلي",
    },
    "setup.auto_detect": {
        "en": "Rekall will automatically detect .rekall/ in this folder.",
        "fr": "Rekall détectera automatiquement .rekall/ dans ce dossier.",
        "es": "Rekall detectará automáticamente .rekall/ en esta carpeta.",
        "zh": "Rekall将自动检测此文件夹中的.rekall/。",
        "ar": "سيكتشف Rekall تلقائياً .rekall/ في هذا المجلد.",
    },
    "setup.global_active": {
        "en": "Global database already active",
        "fr": "Base globale déjà active",
        "es": "Base global ya activa",
        "zh": "全局数据库已激活",
        "ar": "قاعدة البيانات العالمية نشطة بالفعل",
    },
    "setup.local_active": {
        "en": "Local database already active",
        "fr": "Base locale déjà active",
        "es": "Base local ya activa",
        "zh": "本地数据库已激活",
        "ar": "قاعدة البيانات المحلية نشطة بالفعل",
    },

    # ==========================================================================
    # Import/Export details
    # ==========================================================================
    "import.filename": {
        "en": "Archive filename (without .rekall.zip)",
        "fr": "Nom du fichier archive (sans .rekall.zip)",
        "es": "Nombre del archivo (sin .rekall.zip)",
        "zh": "归档文件名（不含.rekall.zip）",
        "ar": "اسم ملف الأرشيف (بدون .rekall.zip)",
    },
    "import.output_filename": {
        "en": "Output filename (without .{fmt})",
        "fr": "Nom du fichier de sortie (sans .{fmt})",
        "es": "Nombre del archivo de salida (sin .{fmt})",
        "zh": "输出文件名（不含.{fmt}）",
        "ar": "اسم ملف الإخراج (بدون .{fmt})",
    },
    "import.no_entries": {
        "en": "No entries to export.",
        "fr": "Aucune entrée à exporter.",
        "es": "No hay entradas para exportar.",
        "zh": "没有条目可导出。",
        "ar": "لا توجد إدخالات للتصدير.",
    },
    "import.exported": {
        "en": "Exported {count} entries to {path}",
        "fr": "Exporté {count} entrées vers {path}",
        "es": "Exportadas {count} entradas a {path}",
        "zh": "已导出 {count} 条目到 {path}",
        "ar": "تم تصدير {count} إدخالات إلى {path}",
    },
    "import.archive_path": {
        "en": "Archive path (.rekall.zip file)",
        "fr": "Chemin archive (.rekall.zip)",
        "es": "Ruta del archivo (.rekall.zip)",
        "zh": "归档路径（.rekall.zip文件）",
        "ar": "مسار الأرشيف (ملف .rekall.zip)",
    },
    "import.select_archive": {
        "en": "Select archive to import",
        "fr": "Sélectionner une archive",
        "es": "Seleccionar archivo a importar",
        "zh": "选择要导入的归档",
        "ar": "اختر الأرشيف للاستيراد",
    },
    "import.other_file": {
        "en": "Other file...",
        "fr": "Autre fichier...",
        "es": "Otro archivo...",
        "zh": "其他文件...",
        "ar": "ملف آخر...",
    },
    "import.no_archives_found": {
        "en": "No archives found",
        "fr": "Aucune archive trouvée",
        "es": "No se encontraron archivos",
        "zh": "未找到归档",
        "ar": "لم يتم العثور على أرشيفات",
    },
    "import.file_not_found": {
        "en": "File not found",
        "fr": "Fichier introuvable",
        "es": "Archivo no encontrado",
        "zh": "文件未找到",
        "ar": "الملف غير موجود",
    },
    "import.invalid_archive": {
        "en": "Invalid or corrupted archive",
        "fr": "Archive invalide ou corrompue",
        "es": "Archivo inválido o corrupto",
        "zh": "无效或损坏的归档",
        "ar": "أرشيف غير صالح أو تالف",
    },
    "import.validation_failed": {
        "en": "Archive validation failed",
        "fr": "Validation de l'archive échouée",
        "es": "Validación del archivo fallida",
        "zh": "归档验证失败",
        "ar": "فشل التحقق من الأرشيف",
    },
    "import.archive_info": {
        "en": "Archive info",
        "fr": "Info archive",
        "es": "Info archivo",
        "zh": "归档信息",
        "ar": "معلومات الأرشيف",
    },
    "import.version": {
        "en": "Version",
        "fr": "Version",
        "es": "Versión",
        "zh": "版本",
        "ar": "الإصدار",
    },
    "import.entries": {
        "en": "Entries",
        "fr": "Entrées",
        "es": "Entradas",
        "zh": "条目",
        "ar": "إدخالات",
    },
    "import.nothing_to_import": {
        "en": "Nothing to import.",
        "fr": "Rien à importer.",
        "es": "Nada que importar.",
        "zh": "没有可导入的内容。",
        "ar": "لا شيء للاستيراد.",
    },
    "import.conflict_strategy": {
        "en": "Conflict resolution strategy",
        "fr": "Stratégie de résolution des conflits",
        "es": "Estrategia de resolución de conflictos",
        "zh": "冲突解决策略",
        "ar": "استراتيجية حل التعارضات",
    },
    "import.skip_conflicts": {
        "en": "Skip conflicts (keep local)",
        "fr": "Ignorer conflits (garder local)",
        "es": "Omitir conflictos (mantener local)",
        "zh": "跳过冲突（保留本地）",
        "ar": "تخطي التعارضات (الاحتفاظ بالمحلي)",
    },
    "import.replace_conflicts": {
        "en": "Replace conflicts (backup first)",
        "fr": "Remplacer conflits (backup d'abord)",
        "es": "Reemplazar conflictos (backup primero)",
        "zh": "替换冲突（先备份）",
        "ar": "استبدال التعارضات (نسخ احتياطي أولاً)",
    },
    "import.merge_conflicts": {
        "en": "Merge conflicts (create new entries)",
        "fr": "Fusionner conflits (créer nouvelles entrées)",
        "es": "Fusionar conflictos (crear nuevas entradas)",
        "zh": "合并冲突（创建新条目）",
        "ar": "دمج التعارضات (إنشاء إدخالات جديدة)",
    },
    "import.cancel": {
        "en": "Cancel import",
        "fr": "Annuler import",
        "es": "Cancelar importación",
        "zh": "取消导入",
        "ar": "إلغاء الاستيراد",
    },
    "import.success": {
        "en": "Import completed successfully!",
        "fr": "Import terminé avec succès !",
        "es": "¡Importación completada con éxito!",
        "zh": "导入成功完成！",
        "ar": "اكتمل الاستيراد بنجاح!",
    },
    "import.added": {
        "en": "Added",
        "fr": "Ajoutées",
        "es": "Añadidas",
        "zh": "已添加",
        "ar": "تمت الإضافة",
    },
    "import.replaced": {
        "en": "Replaced",
        "fr": "Remplacées",
        "es": "Reemplazadas",
        "zh": "已替换",
        "ar": "تم الاستبدال",
    },
    "import.merged": {
        "en": "Merged",
        "fr": "Fusionnées",
        "es": "Fusionadas",
        "zh": "已合并",
        "ar": "تم الدمج",
    },
    "import.skipped": {
        "en": "Skipped",
        "fr": "Ignorées",
        "es": "Omitidas",
        "zh": "已跳过",
        "ar": "تم التخطي",
    },
    "import.backup": {
        "en": "Backup",
        "fr": "Backup",
        "es": "Copia",
        "zh": "备份",
        "ar": "نسخة احتياطية",
    },
    "import.failed": {
        "en": "Import failed",
        "fr": "Import échoué",
        "es": "Importación fallida",
        "zh": "导入失败",
        "ar": "فشل الاستيراد",
    },
    "import.external_db_path": {
        "en": "Path to external knowledge.db",
        "fr": "Chemin vers knowledge.db externe",
        "es": "Ruta a knowledge.db externo",
        "zh": "外部knowledge.db路径",
        "ar": "مسار knowledge.db الخارجي",
    },
    "import.external_db_label": {
        "en": "External database",
        "fr": "Base externe",
        "es": "Base externa",
        "zh": "外部数据库",
        "ar": "قاعدة بيانات خارجية",
    },
    "import.file": {
        "en": "File",
        "fr": "Fichier",
        "es": "Archivo",
        "zh": "文件",
        "ar": "ملف",
    },
    "import.types": {
        "en": "Types",
        "fr": "Types",
        "es": "Tipos",
        "zh": "类型",
        "ar": "الأنواع",
    },
    "import.no_entries_external": {
        "en": "No entries in external database.",
        "fr": "Aucune entrée dans la base externe.",
        "es": "No hay entradas en la base externa.",
        "zh": "外部数据库中没有条目。",
        "ar": "لا توجد إدخالات في قاعدة البيانات الخارجية.",
    },

    # ==========================================================================
    # Links (Cognitive Memory)
    # ==========================================================================
    "link.created": {
        "en": "Created link",
        "fr": "Lien créé",
        "es": "Enlace creado",
        "zh": "已创建链接",
        "ar": "تم إنشاء الرابط",
    },
    "link.deleted": {
        "en": "Deleted {count} link(s)",
        "fr": "{count} lien(s) supprimé(s)",
        "es": "{count} enlace(s) eliminado(s)",
        "zh": "已删除 {count} 个链接",
        "ar": "تم حذف {count} رابط(روابط)",
    },
    "link.not_found": {
        "en": "No links found",
        "fr": "Aucun lien trouvé",
        "es": "No se encontraron enlaces",
        "zh": "未找到链接",
        "ar": "لم يتم العثور على روابط",
    },
    "link.related_to": {
        "en": "Related to",
        "fr": "Lié à",
        "es": "Relacionado con",
        "zh": "相关于",
        "ar": "مرتبط بـ",
    },
    "link.outgoing": {
        "en": "Outgoing",
        "fr": "Sortants",
        "es": "Salientes",
        "zh": "出站",
        "ar": "الصادرة",
    },
    "link.incoming": {
        "en": "Incoming",
        "fr": "Entrants",
        "es": "Entrantes",
        "zh": "入站",
        "ar": "الواردة",
    },
    "link.total": {
        "en": "Total: {count} links",
        "fr": "Total : {count} liens",
        "es": "Total: {count} enlaces",
        "zh": "共计：{count} 个链接",
        "ar": "المجموع: {count} روابط",
    },
    "link.type.related": {
        "en": "related",
        "fr": "lié",
        "es": "relacionado",
        "zh": "相关",
        "ar": "مرتبط",
    },
    "link.type.supersedes": {
        "en": "supersedes",
        "fr": "remplace",
        "es": "reemplaza",
        "zh": "替代",
        "ar": "يحل محل",
    },
    "link.type.derived_from": {
        "en": "derived from",
        "fr": "dérivé de",
        "es": "derivado de",
        "zh": "源于",
        "ar": "مشتق من",
    },
    "link.type.contradicts": {
        "en": "contradicts",
        "fr": "contredit",
        "es": "contradice",
        "zh": "矛盾",
        "ar": "يناقض",
    },

    # ==========================================================================
    # Memory Types (Cognitive Memory)
    # ==========================================================================
    "memory.episodic": {
        "en": "episodic",
        "fr": "épisodique",
        "es": "episódico",
        "zh": "情景记忆",
        "ar": "عرضي",
    },
    "memory.semantic": {
        "en": "semantic",
        "fr": "sémantique",
        "es": "semántico",
        "zh": "语义记忆",
        "ar": "دلالي",
    },
    "memory.consolidation": {
        "en": "Consolidation",
        "fr": "Consolidation",
        "es": "Consolidación",
        "zh": "巩固度",
        "ar": "التوحيد",
    },
    "memory.access_count": {
        "en": "Access count",
        "fr": "Nombre d'accès",
        "es": "Número de accesos",
        "zh": "访问次数",
        "ar": "عدد الوصول",
    },
    "memory.last_accessed": {
        "en": "Last accessed",
        "fr": "Dernier accès",
        "es": "Último acceso",
        "zh": "最后访问",
        "ar": "آخر وصول",
    },

    # ==========================================================================
    # Stale Entries (Cognitive Memory)
    # ==========================================================================
    "stale.title": {
        "en": "Stale entries",
        "fr": "Entrées obsolètes",
        "es": "Entradas obsoletas",
        "zh": "陈旧条目",
        "ar": "إدخالات قديمة",
    },
    "stale.no_stale": {
        "en": "No stale entries",
        "fr": "Aucune entrée obsolète",
        "es": "No hay entradas obsoletas",
        "zh": "没有陈旧条目",
        "ar": "لا توجد إدخالات قديمة",
    },
    "stale.not_accessed_days": {
        "en": "not accessed in {days}+ days",
        "fr": "non consulté depuis {days}+ jours",
        "es": "no accedido en {days}+ días",
        "zh": "{days}+ 天未访问",
        "ar": "لم يتم الوصول إليه منذ {days}+ يوم",
    },
    "stale.status.fragile": {
        "en": "fragile",
        "fr": "fragile",
        "es": "frágil",
        "zh": "脆弱",
        "ar": "هش",
    },
    "stale.status.fading": {
        "en": "fading",
        "fr": "s'estompe",
        "es": "desvaneciéndose",
        "zh": "淡化中",
        "ar": "يتلاشى",
    },
    "stale.need_attention": {
        "en": "{count} entries need attention",
        "fr": "{count} entrées nécessitent attention",
        "es": "{count} entradas necesitan atención",
        "zh": "{count} 条目需要关注",
        "ar": "{count} إدخالات تحتاج اهتمام",
    },

    # ==========================================================================
    # Review (Spaced Repetition)
    # ==========================================================================
    "review.title": {
        "en": "Review session",
        "fr": "Session de révision",
        "es": "Sesión de repaso",
        "zh": "复习会话",
        "ar": "جلسة مراجعة",
    },
    "review.entries_due": {
        "en": "{count} entries due",
        "fr": "{count} entrées à réviser",
        "es": "{count} entradas pendientes",
        "zh": "{count} 条目待复习",
        "ar": "{count} إدخالات مستحقة",
    },
    "review.no_entries_due": {
        "en": "No entries due for review!",
        "fr": "Aucune entrée à réviser !",
        "es": "¡No hay entradas para repasar!",
        "zh": "没有需要复习的条目！",
        "ar": "لا توجد إدخالات للمراجعة!",
    },
    "review.rate_recall": {
        "en": "Rate your recall",
        "fr": "Notez votre rappel",
        "es": "Califique su recuerdo",
        "zh": "评估您的记忆",
        "ar": "قيّم تذكرك",
    },
    "review.forgot": {
        "en": "Forgot",
        "fr": "Oublié",
        "es": "Olvidado",
        "zh": "忘记",
        "ar": "نسيت",
    },
    "review.hard": {
        "en": "Hard",
        "fr": "Difficile",
        "es": "Difícil",
        "zh": "困难",
        "ar": "صعب",
    },
    "review.good": {
        "en": "Good",
        "fr": "Bien",
        "es": "Bien",
        "zh": "良好",
        "ar": "جيد",
    },
    "review.easy": {
        "en": "Easy",
        "fr": "Facile",
        "es": "Fácil",
        "zh": "容易",
        "ar": "سهل",
    },
    "review.perfect": {
        "en": "Perfect",
        "fr": "Parfait",
        "es": "Perfecto",
        "zh": "完美",
        "ar": "ممتاز",
    },
    "review.next_review": {
        "en": "Next review: in {days} days",
        "fr": "Prochaine révision : dans {days} jours",
        "es": "Próximo repaso: en {days} días",
        "zh": "下次复习：{days} 天后",
        "ar": "المراجعة التالية: خلال {days} يوم",
    },
    "review.overdue": {
        "en": "Overdue: {days} days",
        "fr": "En retard : {days} jours",
        "es": "Atrasado: {days} días",
        "zh": "逾期：{days} 天",
        "ar": "متأخر: {days} يوم",
    },
    "review.complete": {
        "en": "Review complete!",
        "fr": "Révision terminée !",
        "es": "¡Repaso completado!",
        "zh": "复习完成！",
        "ar": "اكتملت المراجعة!",
    },
    "review.reviewed": {
        "en": "Reviewed: {count} entries",
        "fr": "Révisé : {count} entrées",
        "es": "Repasado: {count} entradas",
        "zh": "已复习：{count} 条目",
        "ar": "تمت مراجعة: {count} إدخالات",
    },
    "review.average_recall": {
        "en": "Average recall: {rating}/5",
        "fr": "Rappel moyen : {rating}/5",
        "es": "Recuerdo promedio: {rating}/5",
        "zh": "平均记忆评分：{rating}/5",
        "ar": "متوسط التذكر: {rating}/5",
    },
    "review.session_ended": {
        "en": "Review session ended.",
        "fr": "Session de révision terminée.",
        "es": "Sesión de repaso terminada.",
        "zh": "复习会话已结束。",
        "ar": "انتهت جلسة المراجعة.",
    },

    # ==========================================================================
    # Generalize (Cognitive Memory)
    # ==========================================================================
    "generalize.title": {
        "en": "Generalization",
        "fr": "Généralisation",
        "es": "Generalización",
        "zh": "泛化",
        "ar": "التعميم",
    },
    "generalize.analyzing": {
        "en": "Analyzing {count} episodic entries...",
        "fr": "Analyse de {count} entrées épisodiques...",
        "es": "Analizando {count} entradas episódicas...",
        "zh": "分析 {count} 个情景条目...",
        "ar": "تحليل {count} إدخالات عرضية...",
    },
    "generalize.patterns_found": {
        "en": "Common patterns found",
        "fr": "Patterns communs trouvés",
        "es": "Patrones comunes encontrados",
        "zh": "发现共同模式",
        "ar": "تم العثور على أنماط مشتركة",
    },
    "generalize.draft": {
        "en": "Draft semantic entry",
        "fr": "Brouillon d'entrée sémantique",
        "es": "Borrador de entrada semántica",
        "zh": "语义条目草稿",
        "ar": "مسودة إدخال دلالي",
    },
    "generalize.create_confirm": {
        "en": "Create this entry?",
        "fr": "Créer cette entrée ?",
        "es": "¿Crear esta entrada?",
        "zh": "创建此条目？",
        "ar": "هل تريد إنشاء هذا الإدخال؟",
    },
    "generalize.min_entries": {
        "en": "Need at least 2 entries to generalize",
        "fr": "Besoin d'au moins 2 entrées pour généraliser",
        "es": "Se necesitan al menos 2 entradas para generalizar",
        "zh": "需要至少 2 个条目才能泛化",
        "ar": "تحتاج إلى إدخالين على الأقل للتعميم",
    },

    # ==========================================================================
    # About Section
    # ==========================================================================
    "about.changelog": {
        "en": "Changelog",
        "fr": "Historique des versions",
        "es": "Registro de cambios",
        "zh": "更新日志",
        "ar": "سجل التغييرات",
    },
    "about.version": {
        "en": "Version info",
        "fr": "Infos version",
        "es": "Info de versión",
        "zh": "版本信息",
        "ar": "معلومات الإصدار",
    },
    "about.version_title": {
        "en": "Version Information",
        "fr": "Informations de version",
        "es": "Información de versión",
        "zh": "版本信息",
        "ar": "معلومات الإصدار",
    },
    "about.release_date": {
        "en": "Release date",
        "fr": "Date de sortie",
        "es": "Fecha de lanzamiento",
        "zh": "发布日期",
        "ar": "تاريخ الإصدار",
    },
    "about.changelog_not_found": {
        "en": "Changelog not found",
        "fr": "Historique non trouvé",
        "es": "Registro no encontrado",
        "zh": "未找到更新日志",
        "ar": "سجل التغييرات غير موجود",
    },

    # ==========================================================================
    # Database Maintenance
    # ==========================================================================
    "info.title": {
        "en": "Database Information",
        "fr": "Informations de la base",
        "es": "Información de la base",
        "zh": "数据库信息",
        "ar": "معلومات قاعدة البيانات",
    },
    "info.no_db": {
        "en": "No database found.",
        "fr": "Aucune base trouvée.",
        "es": "No se encontró la base.",
        "zh": "未找到数据库。",
        "ar": "لم يتم العثور على قاعدة بيانات.",
    },
    "info.run_init": {
        "en": "Run 'rekall init' to create one.",
        "fr": "Lancez 'rekall init' pour en créer une.",
        "es": "Ejecute 'rekall init' para crear una.",
        "zh": "运行 'rekall init' 创建数据库。",
        "ar": "شغّل 'rekall init' لإنشاء واحدة.",
    },
    "info.schema": {
        "en": "Schema",
        "fr": "Schéma",
        "es": "Esquema",
        "zh": "架构",
        "ar": "المخطط",
    },
    "info.schema_current": {
        "en": "(current)",
        "fr": "(actuel)",
        "es": "(actual)",
        "zh": "(当前)",
        "ar": "(الحالي)",
    },
    "info.schema_outdated": {
        "en": "(outdated - run init)",
        "fr": "(obsolète - lancer init)",
        "es": "(obsoleto - ejecutar init)",
        "zh": "(过时 - 运行 init)",
        "ar": "(قديم - شغّل init)",
    },
    "info.entries": {
        "en": "Entries",
        "fr": "Entrées",
        "es": "Entradas",
        "zh": "条目",
        "ar": "الإدخالات",
    },
    "info.active": {
        "en": "active",
        "fr": "actives",
        "es": "activas",
        "zh": "活跃",
        "ar": "نشط",
    },
    "info.obsolete": {
        "en": "obsolete",
        "fr": "obsolètes",
        "es": "obsoletas",
        "zh": "过时",
        "ar": "قديم",
    },
    "info.links": {
        "en": "Links",
        "fr": "Liens",
        "es": "Enlaces",
        "zh": "链接",
        "ar": "الروابط",
    },
    "info.size": {
        "en": "Size",
        "fr": "Taille",
        "es": "Tamaño",
        "zh": "大小",
        "ar": "الحجم",
    },
    "backup.created": {
        "en": "Backup created",
        "fr": "Backup créé",
        "es": "Backup creado",
        "zh": "备份已创建",
        "ar": "تم إنشاء النسخة الاحتياطية",
    },
    "backup.size": {
        "en": "Size",
        "fr": "Taille",
        "es": "Tamaño",
        "zh": "大小",
        "ar": "الحجم",
    },
    "backup.no_db": {
        "en": "No database to backup.",
        "fr": "Aucune base à sauvegarder.",
        "es": "No hay base para respaldar.",
        "zh": "没有要备份的数据库。",
        "ar": "لا توجد قاعدة بيانات للنسخ الاحتياطي.",
    },
    "backup.error": {
        "en": "Backup failed",
        "fr": "Backup échoué",
        "es": "Backup fallido",
        "zh": "备份失败",
        "ar": "فشل النسخ الاحتياطي",
    },
    "restore.safety_backup": {
        "en": "Creating safety backup before restore...",
        "fr": "Création backup de sécurité avant restauration...",
        "es": "Creando backup de seguridad antes de restaurar...",
        "zh": "恢复前创建安全备份...",
        "ar": "إنشاء نسخة احتياطية آمنة قبل الاستعادة...",
    },
    "restore.saved": {
        "en": "Saved",
        "fr": "Sauvegardé",
        "es": "Guardado",
        "zh": "已保存",
        "ar": "تم الحفظ",
    },
    "restore.success": {
        "en": "Database restored from",
        "fr": "Base restaurée depuis",
        "es": "Base restaurada desde",
        "zh": "数据库已从以下位置恢复",
        "ar": "تم استعادة قاعدة البيانات من",
    },
    "restore.invalid": {
        "en": "Invalid backup file (integrity check failed).",
        "fr": "Fichier backup invalide (échec vérification intégrité).",
        "es": "Archivo backup inválido (falló verificación de integridad).",
        "zh": "无效的备份文件（完整性检查失败）。",
        "ar": "ملف النسخ الاحتياطي غير صالح (فشل فحص السلامة).",
    },
    "restore.not_found": {
        "en": "Backup file not found",
        "fr": "Fichier backup introuvable",
        "es": "Archivo backup no encontrado",
        "zh": "未找到备份文件",
        "ar": "ملف النسخ الاحتياطي غير موجود",
    },
    "restore.unchanged": {
        "en": "Current database unchanged.",
        "fr": "Base actuelle inchangée.",
        "es": "Base actual sin cambios.",
        "zh": "当前数据库未更改。",
        "ar": "قاعدة البيانات الحالية لم تتغير.",
    },

    # ==========================================================================
    # TUI Maintenance Menu
    # ==========================================================================
    "menu.maintenance": {
        "en": "Installation & Maintenance",
        "fr": "Installation & Maintenance",
        "es": "Instalación y Mantenimiento",
        "zh": "安装和维护",
        "ar": "التثبيت والصيانة",
    },
    "menu.maintenance.desc": {
        "en": "Setup, backup, restore...",
        "fr": "Config, backup, restaurer...",
        "es": "Config, backup, restaurar...",
        "zh": "设置、备份、恢复...",
        "ar": "إعداد، نسخ احتياطي، استعادة...",
    },
    "maintenance.db_info": {
        "en": "Database Info",
        "fr": "Infos base de données",
        "es": "Info base de datos",
        "zh": "数据库信息",
        "ar": "معلومات قاعدة البيانات",
    },
    "maintenance.create_backup": {
        "en": "Create Backup",
        "fr": "Créer un backup",
        "es": "Crear backup",
        "zh": "创建备份",
        "ar": "إنشاء نسخة احتياطية",
    },
    "maintenance.restore_backup": {
        "en": "Restore from Backup",
        "fr": "Restaurer depuis backup",
        "es": "Restaurar desde backup",
        "zh": "从备份恢复",
        "ar": "الاستعادة من نسخة احتياطية",
    },
    "maintenance.select_backup": {
        "en": "Select backup to restore",
        "fr": "Sélectionner backup à restaurer",
        "es": "Seleccionar backup a restaurar",
        "zh": "选择要恢复的备份",
        "ar": "اختر النسخة الاحتياطية للاستعادة",
    },
    "maintenance.no_backups": {
        "en": "No backups found.",
        "fr": "Aucun backup trouvé.",
        "es": "No se encontraron backups.",
        "zh": "未找到备份。",
        "ar": "لم يتم العثور على نسخ احتياطية.",
    },
    "maintenance.confirm_restore": {
        "en": "Restore this backup?",
        "fr": "Restaurer ce backup ?",
        "es": "¿Restaurar este backup?",
        "zh": "恢复此备份？",
        "ar": "استعادة هذه النسخة الاحتياطية؟",
    },

    # ==========================================================================
    # Sources Integration (Feature 009)
    # ==========================================================================
    "source.title": {
        "en": "Source",
        "fr": "Source",
        "es": "Fuente",
        "zh": "来源",
        "ar": "مصدر",
    },
    "source.sources": {
        "en": "Sources",
        "fr": "Sources",
        "es": "Fuentes",
        "zh": "来源",
        "ar": "مصادر",
    },
    "source.domain": {
        "en": "Domain",
        "fr": "Domaine",
        "es": "Dominio",
        "zh": "域名",
        "ar": "نطاق",
    },
    "source.score": {
        "en": "Score",
        "fr": "Score",
        "es": "Puntuación",
        "zh": "评分",
        "ar": "نقاط",
    },
    "source.usage_count": {
        "en": "Usage count",
        "fr": "Nb utilisations",
        "es": "Conteo de uso",
        "zh": "使用次数",
        "ar": "عدد الاستخدامات",
    },
    "source.last_used": {
        "en": "Last used",
        "fr": "Dernière utilisation",
        "es": "Último uso",
        "zh": "上次使用",
        "ar": "آخر استخدام",
    },
    "source.reliability": {
        "en": "Reliability",
        "fr": "Fiabilité",
        "es": "Fiabilidad",
        "zh": "可靠性",
        "ar": "الموثوقية",
    },
    "source.status": {
        "en": "Status",
        "fr": "Statut",
        "es": "Estado",
        "zh": "状态",
        "ar": "الحالة",
    },
    "source.status.active": {
        "en": "Active",
        "fr": "Active",
        "es": "Activa",
        "zh": "活跃",
        "ar": "نشط",
    },
    "source.status.inaccessible": {
        "en": "Inaccessible",
        "fr": "Inaccessible",
        "es": "Inaccesible",
        "zh": "无法访问",
        "ar": "غير متاح",
    },
    "source.status.archived": {
        "en": "Archived",
        "fr": "Archivée",
        "es": "Archivada",
        "zh": "已存档",
        "ar": "مؤرشف",
    },
    "source.decay_rate": {
        "en": "Decay rate",
        "fr": "Taux de déclin",
        "es": "Tasa de decaimiento",
        "zh": "衰减率",
        "ar": "معدل التراجع",
    },
    "source.decay.fast": {
        "en": "Fast (3 months)",
        "fr": "Rapide (3 mois)",
        "es": "Rápido (3 meses)",
        "zh": "快速 (3个月)",
        "ar": "سريع (3 أشهر)",
    },
    "source.decay.medium": {
        "en": "Medium (6 months)",
        "fr": "Moyen (6 mois)",
        "es": "Medio (6 meses)",
        "zh": "中等 (6个月)",
        "ar": "متوسط (6 أشهر)",
    },
    "source.decay.slow": {
        "en": "Slow (12 months)",
        "fr": "Lent (12 mois)",
        "es": "Lento (12 meses)",
        "zh": "慢速 (12个月)",
        "ar": "بطيء (12 شهر)",
    },
    "source.add": {
        "en": "Add source",
        "fr": "Ajouter source",
        "es": "Añadir fuente",
        "zh": "添加来源",
        "ar": "إضافة مصدر",
    },
    "source.remove": {
        "en": "Remove source",
        "fr": "Retirer source",
        "es": "Eliminar fuente",
        "zh": "移除来源",
        "ar": "إزالة مصدر",
    },
    "source.note": {
        "en": "Note",
        "fr": "Note",
        "es": "Nota",
        "zh": "笔记",
        "ar": "ملاحظة",
    },
    "source.note_placeholder": {
        "en": "Optional note (e.g., 'Section on chunking')",
        "fr": "Note optionnelle (ex: 'Section sur chunking')",
        "es": "Nota opcional (ej: 'Sección sobre chunking')",
        "zh": "可选备注 (例如: '分块部分')",
        "ar": "ملاحظة اختيارية (مثل: 'قسم التقسيم')",
    },
    "source.type": {
        "en": "Type",
        "fr": "Type",
        "es": "Tipo",
        "zh": "类型",
        "ar": "نوع",
    },
    "source.type.theme": {
        "en": "Theme",
        "fr": "Thème",
        "es": "Tema",
        "zh": "主题",
        "ar": "موضوع",
    },
    "source.type.url": {
        "en": "URL",
        "fr": "URL",
        "es": "URL",
        "zh": "网址",
        "ar": "رابط",
    },
    "source.type.file": {
        "en": "File",
        "fr": "Fichier",
        "es": "Archivo",
        "zh": "文件",
        "ar": "ملف",
    },
    "source.linked_sources": {
        "en": "Linked sources",
        "fr": "Sources liées",
        "es": "Fuentes vinculadas",
        "zh": "链接的来源",
        "ar": "المصادر المرتبطة",
    },
    "source.no_sources": {
        "en": "No sources linked",
        "fr": "Aucune source liée",
        "es": "Sin fuentes vinculadas",
        "zh": "没有链接的来源",
        "ar": "لا توجد مصادر مرتبطة",
    },
    "entry_source.added": {
        "en": "Source added to entry",
        "fr": "Source ajoutée au souvenir",
        "es": "Fuente añadida a la entrada",
        "zh": "来源已添加到条目",
        "ar": "تمت إضافة المصدر إلى الإدخال",
    },
    "entry_source.removed": {
        "en": "Source removed from entry",
        "fr": "Source retirée du souvenir",
        "es": "Fuente eliminada de la entrada",
        "zh": "来源已从条目中移除",
        "ar": "تمت إزالة المصدر من الإدخال",
    },
    # ==========================================================================
    # Backlinks (Feature 009 - US2)
    # ==========================================================================
    "backlinks.title": {
        "en": "Backlinks",
        "fr": "Rétroliens",
        "es": "Vínculos entrantes",
        "zh": "反向链接",
        "ar": "روابط خلفية",
    },
    "backlinks.cited_by": {
        "en": "Cited by {count} entries",
        "fr": "Cité par {count} souvenirs",
        "es": "Citado por {count} entradas",
        "zh": "被 {count} 个条目引用",
        "ar": "مُستشهد به في {count} إدخالات",
    },
    "backlinks.cited_by_one": {
        "en": "Cited by 1 entry",
        "fr": "Cité par 1 souvenir",
        "es": "Citado por 1 entrada",
        "zh": "被 1 个条目引用",
        "ar": "مُستشهد به في إدخال واحد",
    },
    "backlinks.no_backlinks": {
        "en": "No entries cite this source",
        "fr": "Aucun souvenir ne cite cette source",
        "es": "Ninguna entrada cita esta fuente",
        "zh": "没有条目引用此来源",
        "ar": "لا توجد إدخالات تستشهد بهذا المصدر",
    },
    "backlinks.view_entry": {
        "en": "View entry",
        "fr": "Voir le souvenir",
        "es": "Ver entrada",
        "zh": "查看条目",
        "ar": "عرض الإدخال",
    },
    "source_detail.title": {
        "en": "Source Details",
        "fr": "Détails de la source",
        "es": "Detalles de la fuente",
        "zh": "来源详情",
        "ar": "تفاصيل المصدر",
    },
    "source_detail.domain": {
        "en": "Domain",
        "fr": "Domaine",
        "es": "Dominio",
        "zh": "域名",
        "ar": "النطاق",
    },
    "source_detail.pattern": {
        "en": "URL Pattern",
        "fr": "Motif URL",
        "es": "Patrón URL",
        "zh": "URL 模式",
        "ar": "نمط URL",
    },
    "source_detail.usage": {
        "en": "Usage Statistics",
        "fr": "Statistiques d'utilisation",
        "es": "Estadísticas de uso",
        "zh": "使用统计",
        "ar": "إحصائيات الاستخدام",
    },
    "source_detail.last_used": {
        "en": "Last used",
        "fr": "Dernière utilisation",
        "es": "Último uso",
        "zh": "最后使用",
        "ar": "آخر استخدام",
    },
    "source_detail.never_used": {
        "en": "Never used",
        "fr": "Jamais utilisée",
        "es": "Nunca usada",
        "zh": "从未使用",
        "ar": "لم تُستخدم أبداً",
    },
    # ==========================================================================
    # Sources Menu & Dashboard (Feature 009 - TUI)
    # ==========================================================================
    "menu.sources": {
        "en": "Sources",
        "fr": "Sources Documentaires",
        "es": "Fuentes",
        "zh": "来源",
        "ar": "المصادر",
    },
    "menu.sources.desc": {
        "en": "Manage documentary sources",
        "fr": "Gérer les sources documentaires",
        "es": "Gestionar fuentes documentales",
        "zh": "管理文档来源",
        "ar": "إدارة المصادر الوثائقية",
    },
    "dashboard.top_sources": {
        "en": "Top Sources",
        "fr": "Meilleures Sources",
        "es": "Mejores Fuentes",
        "zh": "热门来源",
        "ar": "أفضل المصادر",
    },
    "dashboard.dormant_sources": {
        "en": "Dormant Sources",
        "fr": "Sources Dormantes",
        "es": "Fuentes Inactivas",
        "zh": "休眠来源",
        "ar": "المصادر الخاملة",
    },
    "dashboard.emerging_sources": {
        "en": "Emerging Sources",
        "fr": "Sources Émergentes",
        "es": "Fuentes Emergentes",
        "zh": "新兴来源",
        "ar": "المصادر الناشئة",
    },
    "dashboard.inaccessible_sources": {
        "en": "Inaccessible Sources",
        "fr": "Sources Inaccessibles",
        "es": "Fuentes Inaccesibles",
        "zh": "无法访问的来源",
        "ar": "المصادر غير المتاحة",
    },
    "dashboard.statistics": {
        "en": "Statistics",
        "fr": "Statistiques",
        "es": "Estadísticas",
        "zh": "统计",
        "ar": "إحصائيات",
    },
    "dashboard.total_sources": {
        "en": "Total sources",
        "fr": "Total sources",
        "es": "Total de fuentes",
        "zh": "来源总数",
        "ar": "إجمالي المصادر",
    },
    "dashboard.total_links": {
        "en": "Total links",
        "fr": "Total liens",
        "es": "Total de enlaces",
        "zh": "链接总数",
        "ar": "إجمالي الروابط",
    },
    "dashboard.avg_score": {
        "en": "Average score",
        "fr": "Score moyen",
        "es": "Puntuación media",
        "zh": "平均分数",
        "ar": "متوسط النقاط",
    },
    "dashboard.verify_links": {
        "en": "Verify link accessibility",
        "fr": "Vérifier l'accessibilité des liens",
        "es": "Verificar accesibilidad de enlaces",
        "zh": "验证链接可访问性",
        "ar": "التحقق من إمكانية الوصول إلى الروابط",
    },
    "dashboard.add_source": {
        "en": "Add new source",
        "fr": "Ajouter une source",
        "es": "Añadir nueva fuente",
        "zh": "添加新来源",
        "ar": "إضافة مصدر جديد",
    },
    "sources.add_to_entry": {
        "en": "Add source to entry",
        "fr": "Ajouter une source au souvenir",
        "es": "Añadir fuente a la entrada",
        "zh": "添加来源到条目",
        "ar": "إضافة مصدر إلى الإدخال",
    },
    "sources.select_type": {
        "en": "Select source type",
        "fr": "Sélectionner le type de source",
        "es": "Seleccionar tipo de fuente",
        "zh": "选择来源类型",
        "ar": "اختر نوع المصدر",
    },
    "sources.enter_theme": {
        "en": "Enter theme name",
        "fr": "Entrer le nom du thème",
        "es": "Introducir nombre del tema",
        "zh": "输入主题名称",
        "ar": "أدخل اسم الموضوع",
    },
    "sources.enter_url": {
        "en": "Enter URL",
        "fr": "Entrer l'URL",
        "es": "Introducir URL",
        "zh": "输入 URL",
        "ar": "أدخل URL",
    },
    "sources.enter_file": {
        "en": "Enter file path",
        "fr": "Entrer le chemin du fichier",
        "es": "Introducir ruta del archivo",
        "zh": "输入文件路径",
        "ar": "أدخل مسار الملف",
    },
    "sources.optional_note": {
        "en": "Optional note",
        "fr": "Note optionnelle",
        "es": "Nota opcional",
        "zh": "可选备注",
        "ar": "ملاحظة اختيارية",
    },
    "sources.manage": {
        "en": "Manage sources",
        "fr": "Gérer les sources",
        "es": "Gestionar fuentes",
        "zh": "管理来源",
        "ar": "إدارة المصادر",
    },
    "sources.verify_title": {
        "en": "Verify Links",
        "fr": "Vérifier les liens",
        "es": "Verificar enlaces",
        "zh": "验证链接",
        "ar": "التحقق من الروابط",
    },
    "sources.verify_force": {
        "en": "Force re-check all",
        "fr": "Forcer la revérification",
        "es": "Forzar reverificación",
        "zh": "强制重新检查",
        "ar": "فرض إعادة التحقق",
    },
    # ==========================================================================
    # Sources Autonomes (Feature 010)
    # ==========================================================================
    # Seed sources (migrated from speckit)
    "source.seed": {
        "en": "Seed",
        "fr": "Initiale",
        "es": "Semilla",
        "zh": "种子",
        "ar": "بذرة",
    },
    "source.seed.desc": {
        "en": "Source migrated from speckit research",
        "fr": "Source migrée depuis recherche speckit",
        "es": "Fuente migrada de investigación speckit",
        "zh": "从 speckit 研究迁移的来源",
        "ar": "مصدر تم ترحيله من بحث speckit",
    },
    "source.promoted": {
        "en": "Promoted",
        "fr": "Promue",
        "es": "Promocionada",
        "zh": "已推广",
        "ar": "مرقّى",
    },
    "source.promoted.desc": {
        "en": "Automatically promoted based on usage",
        "fr": "Promue automatiquement selon l'utilisation",
        "es": "Promocionada automáticamente según el uso",
        "zh": "根据使用情况自动推广",
        "ar": "تمت الترقية تلقائياً بناءً على الاستخدام",
    },
    # Role (hub/authority/unclassified)
    "source.role": {
        "en": "Role",
        "fr": "Rôle",
        "es": "Rol",
        "zh": "角色",
        "ar": "دور",
    },
    "source.role.hub": {
        "en": "Hub",
        "fr": "Hub",
        "es": "Hub",
        "zh": "枢纽",
        "ar": "محور",
    },
    "source.role.hub.desc": {
        "en": "Aggregator (Reddit, HN, StackOverflow)",
        "fr": "Agrégateur (Reddit, HN, StackOverflow)",
        "es": "Agregador (Reddit, HN, StackOverflow)",
        "zh": "聚合器 (Reddit, HN, StackOverflow)",
        "ar": "مجمّع (Reddit, HN, StackOverflow)",
    },
    "source.role.authority": {
        "en": "Authority",
        "fr": "Autorité",
        "es": "Autoridad",
        "zh": "权威",
        "ar": "سلطة",
    },
    "source.role.authority.desc": {
        "en": "Official docs (MDN, Python docs)",
        "fr": "Docs officiels (MDN, docs Python)",
        "es": "Docs oficiales (MDN, docs Python)",
        "zh": "官方文档 (MDN, Python 文档)",
        "ar": "وثائق رسمية (MDN, Python docs)",
    },
    "source.role.unclassified": {
        "en": "Unclassified",
        "fr": "Non classée",
        "es": "Sin clasificar",
        "zh": "未分类",
        "ar": "غير مصنف",
    },
    # Theme management
    "source.theme": {
        "en": "Theme",
        "fr": "Thème",
        "es": "Tema",
        "zh": "主题",
        "ar": "موضوع",
    },
    "source.themes": {
        "en": "Themes",
        "fr": "Thèmes",
        "es": "Temas",
        "zh": "主题",
        "ar": "مواضيع",
    },
    "source.add_theme": {
        "en": "Add theme",
        "fr": "Ajouter thème",
        "es": "Añadir tema",
        "zh": "添加主题",
        "ar": "إضافة موضوع",
    },
    "source.theme_added": {
        "en": "Theme '{theme}' added to source",
        "fr": "Thème '{theme}' ajouté à la source",
        "es": "Tema '{theme}' añadido a la fuente",
        "zh": "主题 '{theme}' 已添加到来源",
        "ar": "تمت إضافة الموضوع '{theme}' إلى المصدر",
    },
    # Migration
    "source.migrate": {
        "en": "Migrate sources",
        "fr": "Migrer les sources",
        "es": "Migrar fuentes",
        "zh": "迁移来源",
        "ar": "ترحيل المصادر",
    },
    "source.migrate.dry_run": {
        "en": "Dry run (no changes)",
        "fr": "Simulation (sans modifications)",
        "es": "Simulación (sin cambios)",
        "zh": "模拟运行（无更改）",
        "ar": "تشغيل تجريبي (بدون تغييرات)",
    },
    "source.migrate.success": {
        "en": "Migration complete: {imported} imported, {updated} updated",
        "fr": "Migration terminée : {imported} importées, {updated} mises à jour",
        "es": "Migración completada: {imported} importadas, {updated} actualizadas",
        "zh": "迁移完成：已导入 {imported}，已更新 {updated}",
        "ar": "اكتملت الترحيل: تم استيراد {imported}، تم تحديث {updated}",
    },
    # Promotion/recalculation
    "source.recalculate": {
        "en": "Recalculate scores",
        "fr": "Recalculer les scores",
        "es": "Recalcular puntuaciones",
        "zh": "重新计算分数",
        "ar": "إعادة حساب النقاط",
    },
    "source.recalculate.success": {
        "en": "Recalculation complete: {promoted} promoted, {demoted} demoted",
        "fr": "Recalcul terminé : {promoted} promues, {demoted} rétrogradées",
        "es": "Recálculo completado: {promoted} promocionadas, {demoted} degradadas",
        "zh": "重新计算完成：{promoted} 已推广，{demoted} 已降级",
        "ar": "اكتمل إعادة الحساب: {promoted} تمت ترقيتها، {demoted} تم تخفيضها",
    },
    # Classification
    "source.classify": {
        "en": "Classify source",
        "fr": "Classifier la source",
        "es": "Clasificar fuente",
        "zh": "分类来源",
        "ar": "تصنيف المصدر",
    },
    "source.classify.success": {
        "en": "Source classified as {role}",
        "fr": "Source classifiée comme {role}",
        "es": "Fuente clasificada como {role}",
        "zh": "来源已分类为 {role}",
        "ar": "تم تصنيف المصدر كـ {role}",
    },
    # Suggest/API
    "source.suggest": {
        "en": "Suggest sources",
        "fr": "Suggérer des sources",
        "es": "Sugerir fuentes",
        "zh": "建议来源",
        "ar": "اقتراح المصادر",
    },
    "source.suggest.no_results": {
        "en": "No sources found for theme '{theme}'",
        "fr": "Aucune source trouvée pour le thème '{theme}'",
        "es": "No se encontraron fuentes para el tema '{theme}'",
        "zh": "未找到主题 '{theme}' 的来源",
        "ar": "لم يتم العثور على مصادر للموضوع '{theme}'",
    },
    # Stats
    "source.stats": {
        "en": "Source statistics",
        "fr": "Statistiques des sources",
        "es": "Estadísticas de fuentes",
        "zh": "来源统计",
        "ar": "إحصائيات المصادر",
    },
    "source.stats.total": {
        "en": "Total sources",
        "fr": "Total sources",
        "es": "Total de fuentes",
        "zh": "来源总数",
        "ar": "إجمالي المصادر",
    },
    "source.stats.seeds": {
        "en": "Seed sources",
        "fr": "Sources initiales",
        "es": "Fuentes semilla",
        "zh": "种子来源",
        "ar": "مصادر البذرة",
    },
    "source.stats.promoted": {
        "en": "Promoted sources",
        "fr": "Sources promues",
        "es": "Fuentes promocionadas",
        "zh": "推广来源",
        "ar": "المصادر المرقّاة",
    },
    # Dashboard sections (Feature 010 - US6)
    "dashboard.seeds": {
        "en": "Seed Sources",
        "fr": "Sources Initiales",
        "es": "Fuentes Semilla",
        "zh": "种子来源",
        "ar": "مصادر البذرة",
    },
    "dashboard.seeds.desc": {
        "en": "Sources migrated from speckit research",
        "fr": "Sources migrées depuis recherche speckit",
        "es": "Fuentes migradas de investigación speckit",
        "zh": "从 speckit 研究迁移的来源",
        "ar": "المصادر المرحّلة من بحث speckit",
    },
    "dashboard.promoted": {
        "en": "Promoted Sources",
        "fr": "Sources Promues",
        "es": "Fuentes Promocionadas",
        "zh": "推广来源",
        "ar": "المصادر المرقّاة",
    },
    "dashboard.promoted.desc": {
        "en": "Automatically promoted based on usage",
        "fr": "Promues automatiquement selon l'utilisation",
        "es": "Promocionadas automáticamente según el uso",
        "zh": "根据使用情况自动推广",
        "ar": "تمت ترقيتها تلقائياً بناءً على الاستخدام",
    },
    "dashboard.role.hub": {
        "en": "Hubs",
        "fr": "Hubs",
        "es": "Hubs",
        "zh": "枢纽",
        "ar": "المحاور",
    },
    "dashboard.role.authority": {
        "en": "Authorities",
        "fr": "Autorités",
        "es": "Autoridades",
        "zh": "权威",
        "ar": "السلطات",
    },
    "dashboard.role.unclassified": {
        "en": "Unclassified",
        "fr": "Non classées",
        "es": "Sin clasificar",
        "zh": "未分类",
        "ar": "غير مصنف",
    },
    # Citation quality
    "source.citation_quality": {
        "en": "Citation Quality",
        "fr": "Qualité de citation",
        "es": "Calidad de cita",
        "zh": "引用质量",
        "ar": "جودة الاستشهاد",
    },
    "source.citation_quality.desc": {
        "en": "Quality factor based on co-citations (PR-Index)",
        "fr": "Facteur qualité basé sur les co-citations (PR-Index)",
        "es": "Factor de calidad basado en co-citas (PR-Index)",
        "zh": "基于共引的质量因子 (PR-Index)",
        "ar": "عامل الجودة بناءً على الاستشهادات المشتركة (PR-Index)",
    },
    # ==========================================================================
    # Sources Medallion - Inbox Bronze (Feature 013)
    # ==========================================================================
    "inbox.title": {
        "en": "URL Inbox",
        "fr": "Boîte d'URLs",
        "es": "Bandeja de URLs",
        "zh": "URL 收件箱",
        "ar": "صندوق وارد URLs",
    },
    "inbox.title.desc": {
        "en": "URLs captured from AI CLI tools",
        "fr": "URLs capturées depuis les outils CLI IA",
        "es": "URLs capturadas de herramientas CLI IA",
        "zh": "从 AI CLI 工具捕获的 URLs",
        "ar": "عناوين URL الملتقطة من أدوات CLI للذكاء الاصطناعي",
    },
    "inbox.import": {
        "en": "Import URLs",
        "fr": "Importer les URLs",
        "es": "Importar URLs",
        "zh": "导入 URLs",
        "ar": "استيراد URLs",
    },
    "inbox.import.success": {
        "en": "{count} URLs imported from {source}",
        "fr": "{count} URLs importées depuis {source}",
        "es": "{count} URLs importadas desde {source}",
        "zh": "从 {source} 导入了 {count} 个 URLs",
        "ar": "تم استيراد {count} URLs من {source}",
    },
    "inbox.import.no_new": {
        "en": "No new URLs to import",
        "fr": "Aucune nouvelle URL à importer",
        "es": "No hay nuevas URLs para importar",
        "zh": "没有新的 URLs 可导入",
        "ar": "لا توجد URLs جديدة للاستيراد",
    },
    "inbox.stats": {
        "en": "Inbox statistics",
        "fr": "Statistiques de la boîte",
        "es": "Estadísticas de la bandeja",
        "zh": "收件箱统计",
        "ar": "إحصائيات صندوق الوارد",
    },
    "inbox.stats.total": {
        "en": "Total URLs",
        "fr": "Total URLs",
        "es": "Total URLs",
        "zh": "URLs 总数",
        "ar": "إجمالي URLs",
    },
    "inbox.stats.pending": {
        "en": "Pending enrichment",
        "fr": "En attente d'enrichissement",
        "es": "Pendientes de enriquecimiento",
        "zh": "待丰富",
        "ar": "بانتظار الإثراء",
    },
    "inbox.stats.quarantine": {
        "en": "In quarantine",
        "fr": "En quarantaine",
        "es": "En cuarentena",
        "zh": "隔离中",
        "ar": "في الحجر",
    },
    "inbox.clear": {
        "en": "Clear inbox",
        "fr": "Vider la boîte",
        "es": "Vaciar bandeja",
        "zh": "清空收件箱",
        "ar": "مسح صندوق الوارد",
    },
    "inbox.clear.confirm": {
        "en": "Clear all {count} URLs from inbox?",
        "fr": "Supprimer les {count} URLs de la boîte ?",
        "es": "¿Eliminar las {count} URLs de la bandeja?",
        "zh": "清空收件箱中的 {count} 个 URLs?",
        "ar": "مسح جميع {count} URLs من صندوق الوارد؟",
    },
    "inbox.quarantine": {
        "en": "Quarantine",
        "fr": "Quarantaine",
        "es": "Cuarentena",
        "zh": "隔离区",
        "ar": "الحجر",
    },
    "inbox.quarantine.desc": {
        "en": "Invalid URLs (localhost, file://, etc.)",
        "fr": "URLs invalides (localhost, file://, etc.)",
        "es": "URLs inválidas (localhost, file://, etc.)",
        "zh": "无效 URLs (localhost, file://, 等.)",
        "ar": "URLs غير صالحة (localhost، file://، إلخ.)",
    },
    "inbox.cli_source": {
        "en": "CLI Source",
        "fr": "Source CLI",
        "es": "Fuente CLI",
        "zh": "CLI 来源",
        "ar": "مصدر CLI",
    },
    "inbox.captured_at": {
        "en": "Captured",
        "fr": "Capturé",
        "es": "Capturado",
        "zh": "捕获时间",
        "ar": "تم الالتقاط",
    },
    "inbox.project": {
        "en": "Project",
        "fr": "Projet",
        "es": "Proyecto",
        "zh": "项目",
        "ar": "مشروع",
    },
    "inbox.url": {
        "en": "URL",
        "fr": "URL",
        "es": "URL",
        "zh": "链接",
        "ar": "الرابط",
    },
    "inbox.domain": {
        "en": "Domain",
        "fr": "Domaine",
        "es": "Dominio",
        "zh": "域名",
        "ar": "النطاق",
    },
    "inbox.status": {
        "en": "Status",
        "fr": "Statut",
        "es": "Estado",
        "zh": "状态",
        "ar": "الحالة",
    },
    "inbox.status.pending": {
        "en": "Pending",
        "fr": "En attente",
        "es": "Pendiente",
        "zh": "待处理",
        "ar": "معلق",
    },
    "inbox.status.enriched": {
        "en": "Enriched",
        "fr": "Enrichi",
        "es": "Enriquecido",
        "zh": "已丰富",
        "ar": "مُثرى",
    },
    "inbox.status.quarantine": {
        "en": "Quarantine",
        "fr": "Quarantaine",
        "es": "Cuarentena",
        "zh": "隔离",
        "ar": "الحجر",
    },
    "inbox.view_quarantine": {
        "en": "View quarantine",
        "fr": "Voir quarantaine",
        "es": "Ver cuarentena",
        "zh": "查看隔离",
        "ar": "عرض الحجر",
    },
    "inbox.view_all": {
        "en": "View all",
        "fr": "Voir tout",
        "es": "Ver todo",
        "zh": "查看全部",
        "ar": "عرض الكل",
    },
    "inbox.delete": {
        "en": "Delete",
        "fr": "Supprimer",
        "es": "Eliminar",
        "zh": "删除",
        "ar": "حذف",
    },
    "inbox.delete.confirm": {
        "en": "Delete {url}?",
        "fr": "Supprimer {url} ?",
        "es": "¿Eliminar {url}?",
        "zh": "删除 {url}？",
        "ar": "حذف {url}؟",
    },
    "inbox.delete.success": {
        "en": "Entry deleted",
        "fr": "Entrée supprimée",
        "es": "Entrada eliminada",
        "zh": "已删除条目",
        "ar": "تم حذف الإدخال",
    },
    "inbox.empty": {
        "en": "Inbox is empty",
        "fr": "Inbox vide",
        "es": "Bandeja vacía",
        "zh": "收件箱为空",
        "ar": "البريد الوارد فارغ",
    },
    "inbox.time_ago": {
        "en": "{time} ago",
        "fr": "il y a {time}",
        "es": "hace {time}",
        "zh": "{time}前",
        "ar": "منذ {time}",
    },
    "inbox.time.minutes": {
        "en": "{n}m",
        "fr": "{n}min",
        "es": "{n}min",
        "zh": "{n}分钟",
        "ar": "{n}د",
    },
    "inbox.time.hours": {
        "en": "{n}h",
        "fr": "{n}h",
        "es": "{n}h",
        "zh": "{n}小时",
        "ar": "{n}س",
    },
    "inbox.time.days": {
        "en": "{n}d",
        "fr": "{n}j",
        "es": "{n}d",
        "zh": "{n}天",
        "ar": "{n}ي",
    },
    # ==========================================================================
    # Sources Medallion - Staging Silver (Feature 013)
    # ==========================================================================
    "staging.title": {
        "en": "Staging Area",
        "fr": "Zone de préparation",
        "es": "Área de preparación",
        "zh": "暂存区",
        "ar": "منطقة التجهيز",
    },
    "staging.title.desc": {
        "en": "Enriched URLs awaiting promotion",
        "fr": "URLs enrichies en attente de promotion",
        "es": "URLs enriquecidas esperando promoción",
        "zh": "等待推广的已丰富 URLs",
        "ar": "عناوين URL المُثراة في انتظار الترقية",
    },
    "staging.enrich": {
        "en": "Enrich URLs",
        "fr": "Enrichir les URLs",
        "es": "Enriquecer URLs",
        "zh": "丰富 URLs",
        "ar": "إثراء URLs",
    },
    "staging.enrich.success": {
        "en": "{count} URLs enriched",
        "fr": "{count} URLs enrichies",
        "es": "{count} URLs enriquecidas",
        "zh": "已丰富 {count} 个 URLs",
        "ar": "تم إثراء {count} URLs",
    },
    "staging.enrich.error": {
        "en": "Failed to enrich {url}: {error}",
        "fr": "Échec d'enrichissement de {url}: {error}",
        "es": "Error al enriquecer {url}: {error}",
        "zh": "丰富 {url} 失败: {error}",
        "ar": "فشل إثراء {url}: {error}",
    },
    "staging.stats": {
        "en": "Staging statistics",
        "fr": "Statistiques de préparation",
        "es": "Estadísticas de preparación",
        "zh": "暂存区统计",
        "ar": "إحصائيات منطقة التجهيز",
    },
    "staging.stats.total": {
        "en": "Total staged",
        "fr": "Total en préparation",
        "es": "Total en preparación",
        "zh": "暂存总数",
        "ar": "إجمالي التجهيز",
    },
    "staging.stats.eligible": {
        "en": "Eligible for promotion",
        "fr": "Éligibles à la promotion",
        "es": "Elegibles para promoción",
        "zh": "可推广",
        "ar": "مؤهل للترقية",
    },
    "staging.stats.promoted": {
        "en": "Already promoted",
        "fr": "Déjà promues",
        "es": "Ya promocionadas",
        "zh": "已推广",
        "ar": "تمت ترقيتها بالفعل",
    },
    "staging.domain": {
        "en": "Domain",
        "fr": "Domaine",
        "es": "Dominio",
        "zh": "域名",
        "ar": "النطاق",
    },
    "staging.content_type": {
        "en": "Content Type",
        "fr": "Type de contenu",
        "es": "Tipo de contenido",
        "zh": "内容类型",
        "ar": "نوع المحتوى",
    },
    "staging.citations": {
        "en": "Citations",
        "fr": "Citations",
        "es": "Citas",
        "zh": "引用数",
        "ar": "الاستشهادات",
    },
    "staging.projects": {
        "en": "Projects",
        "fr": "Projets",
        "es": "Proyectos",
        "zh": "项目数",
        "ar": "المشاريع",
    },
    "staging.score": {
        "en": "Score",
        "fr": "Score",
        "es": "Puntuación",
        "zh": "分数",
        "ar": "النقاط",
    },
    "staging.indicator.eligible": {
        "en": "⬆ Eligible",
        "fr": "⬆ Éligible",
        "es": "⬆ Elegible",
        "zh": "⬆ 可推广",
        "ar": "⬆ مؤهل",
    },
    "staging.indicator.close": {
        "en": "→ Close",
        "fr": "→ Proche",
        "es": "→ Cerca",
        "zh": "→ 接近",
        "ar": "→ قريب",
    },
    "staging.drop": {
        "en": "Drop from staging",
        "fr": "Retirer de préparation",
        "es": "Eliminar de preparación",
        "zh": "从暂存区移除",
        "ar": "إزالة من التجهيز",
    },
    # ==========================================================================
    # Sources Medallion - Promotion (Feature 013)
    # ==========================================================================
    "promotion.title": {
        "en": "Promotion",
        "fr": "Promotion",
        "es": "Promoción",
        "zh": "推广",
        "ar": "الترقية",
    },
    "promotion.auto": {
        "en": "Auto-promote",
        "fr": "Promotion automatique",
        "es": "Promoción automática",
        "zh": "自动推广",
        "ar": "ترقية تلقائية",
    },
    "promotion.auto.success": {
        "en": "{count} sources promoted to Gold",
        "fr": "{count} sources promues en Gold",
        "es": "{count} fuentes promocionadas a Gold",
        "zh": "{count} 个来源已推广到 Gold",
        "ar": "تمت ترقية {count} مصادر إلى Gold",
    },
    "promotion.auto.none": {
        "en": "No eligible sources to promote",
        "fr": "Aucune source éligible à promouvoir",
        "es": "No hay fuentes elegibles para promocionar",
        "zh": "没有符合条件的来源可推广",
        "ar": "لا توجد مصادر مؤهلة للترقية",
    },
    "promotion.success": {
        "en": "Source promoted successfully",
        "fr": "Source promue avec succès",
        "es": "Fuente promocionada con éxito",
        "zh": "来源推广成功",
        "ar": "تمت ترقية المصدر بنجاح",
    },
    "promotion.manual": {
        "en": "Manual promote",
        "fr": "Promotion manuelle",
        "es": "Promoción manual",
        "zh": "手动推广",
        "ar": "ترقية يدوية",
    },
    "promotion.manual.success": {
        "en": "Source promoted to Gold: {url}",
        "fr": "Source promue en Gold : {url}",
        "es": "Fuente promocionada a Gold: {url}",
        "zh": "来源已推广到 Gold: {url}",
        "ar": "تمت ترقية المصدر إلى Gold: {url}",
    },
    "promotion.demote": {
        "en": "Demote",
        "fr": "Rétrograder",
        "es": "Degradar",
        "zh": "降级",
        "ar": "تخفيض",
    },
    "promotion.demote.success": {
        "en": "Source demoted: {url}",
        "fr": "Source rétrogradée : {url}",
        "es": "Fuente degradada: {url}",
        "zh": "来源已降级: {url}",
        "ar": "تم تخفيض المصدر: {url}",
    },
    "promotion.demote.error": {
        "en": "Cannot demote: source not promoted",
        "fr": "Impossible de rétrograder : source non promue",
        "es": "No se puede degradar: fuente no promocionada",
        "zh": "无法降级：来源未被推广",
        "ar": "لا يمكن التخفيض: المصدر غير مرقّى",
    },
    "promotion.threshold": {
        "en": "Promotion threshold",
        "fr": "Seuil de promotion",
        "es": "Umbral de promoción",
        "zh": "推广阈值",
        "ar": "عتبة الترقية",
    },
    "promotion.threshold.current": {
        "en": "Current threshold: {value}",
        "fr": "Seuil actuel : {value}",
        "es": "Umbral actual: {value}",
        "zh": "当前阈值: {value}",
        "ar": "العتبة الحالية: {value}",
    },
    "promotion.weights": {
        "en": "Promotion weights",
        "fr": "Poids de promotion",
        "es": "Pesos de promoción",
        "zh": "推广权重",
        "ar": "أوزان الترقية",
    },
    "promotion.weight.citations": {
        "en": "Citations weight",
        "fr": "Poids des citations",
        "es": "Peso de citas",
        "zh": "引用权重",
        "ar": "وزن الاستشهادات",
    },
    "promotion.weight.projects": {
        "en": "Projects weight",
        "fr": "Poids des projets",
        "es": "Peso de proyectos",
        "zh": "项目权重",
        "ar": "وزن المشاريع",
    },
    "promotion.weight.recency": {
        "en": "Recency weight",
        "fr": "Poids de récence",
        "es": "Peso de recencia",
        "zh": "时效权重",
        "ar": "وزن الحداثة",
    },
    "promotion.decay": {
        "en": "Temporal decay",
        "fr": "Déclin temporel",
        "es": "Decaimiento temporal",
        "zh": "时间衰减",
        "ar": "الانحلال الزمني",
    },
    # Connector messages
    "connector.claude": {
        "en": "Claude Code",
        "fr": "Claude Code",
        "es": "Claude Code",
        "zh": "Claude Code",
        "ar": "Claude Code",
    },
    "connector.cursor": {
        "en": "Cursor IDE",
        "fr": "Cursor IDE",
        "es": "Cursor IDE",
        "zh": "Cursor IDE",
        "ar": "Cursor IDE",
    },
    "connector.not_available": {
        "en": "Connector {name} not available",
        "fr": "Connecteur {name} non disponible",
        "es": "Conector {name} no disponible",
        "zh": "连接器 {name} 不可用",
        "ar": "الموصل {name} غير متاح",
    },
    "connector.history_not_found": {
        "en": "No history found for {name}",
        "fr": "Aucun historique trouvé pour {name}",
        "es": "No se encontró historial para {name}",
        "zh": "未找到 {name} 的历史记录",
        "ar": "لم يتم العثور على سجل لـ {name}",
    },
    # ==========================================================================
    # Tags & Filtres (Feature 012 - Sources Organisation)
    # ==========================================================================
    # Tags management
    "tags.title": {
        "en": "Tags",
        "fr": "Tags",
        "es": "Etiquetas",
        "zh": "标签",
        "ar": "علامات",
    },
    "tags.add": {
        "en": "Add tags",
        "fr": "Ajouter des tags",
        "es": "Añadir etiquetas",
        "zh": "添加标签",
        "ar": "إضافة علامات",
    },
    "tags.remove": {
        "en": "Remove tag",
        "fr": "Retirer le tag",
        "es": "Eliminar etiqueta",
        "zh": "移除标签",
        "ar": "إزالة علامة",
    },
    "tags.edit": {
        "en": "Edit tags",
        "fr": "Modifier les tags",
        "es": "Editar etiquetas",
        "zh": "编辑标签",
        "ar": "تعديل العلامات",
    },
    "tags.browse_by_tag": {
        "en": "Browse by tag",
        "fr": "Parcourir par tag",
        "es": "Explorar por etiqueta",
        "zh": "按标签浏览",
        "ar": "تصفح حسب العلامة",
    },
    "tags.no_tags": {
        "en": "No tags",
        "fr": "Aucun tag",
        "es": "Sin etiquetas",
        "zh": "没有标签",
        "ar": "لا توجد علامات",
    },
    "tags.enter_tags": {
        "en": "Enter tags (comma-separated)",
        "fr": "Entrer les tags (séparés par virgule)",
        "es": "Introducir etiquetas (separadas por coma)",
        "zh": "输入标签（逗号分隔）",
        "ar": "أدخل العلامات (مفصولة بفاصلة)",
    },
    "tags.current": {
        "en": "Current tags",
        "fr": "Tags actuels",
        "es": "Etiquetas actuales",
        "zh": "当前标签",
        "ar": "العلامات الحالية",
    },
    "tags.added": {
        "en": "Tag '{tag}' added",
        "fr": "Tag '{tag}' ajouté",
        "es": "Etiqueta '{tag}' añadida",
        "zh": "标签 '{tag}' 已添加",
        "ar": "تمت إضافة علامة '{tag}'",
    },
    "tags.removed": {
        "en": "Tag '{tag}' removed",
        "fr": "Tag '{tag}' retiré",
        "es": "Etiqueta '{tag}' eliminada",
        "zh": "标签 '{tag}' 已移除",
        "ar": "تمت إزالة علامة '{tag}'",
    },
    "tags.count": {
        "en": "{tag} ({count})",
        "fr": "{tag} ({count})",
        "es": "{tag} ({count})",
        "zh": "{tag} ({count})",
        "ar": "{tag} ({count})",
    },
    "tags.bulk_add": {
        "en": "Add tag to selection",
        "fr": "Ajouter un tag à la sélection",
        "es": "Añadir etiqueta a la selección",
        "zh": "为选中项添加标签",
        "ar": "إضافة علامة للتحديد",
    },
    "tags.bulk_remove": {
        "en": "Remove tag from selection",
        "fr": "Retirer un tag de la sélection",
        "es": "Eliminar etiqueta de la selección",
        "zh": "从选中项移除标签",
        "ar": "إزالة علامة من التحديد",
    },
    # Filters
    "filter.title": {
        "en": "Advanced Search",
        "fr": "Recherche avancée",
        "es": "Búsqueda avanzada",
        "zh": "高级搜索",
        "ar": "بحث متقدم",
    },
    "filter.apply": {
        "en": "Apply filters",
        "fr": "Appliquer les filtres",
        "es": "Aplicar filtros",
        "zh": "应用筛选",
        "ar": "تطبيق المرشحات",
    },
    "filter.save": {
        "en": "Save this view",
        "fr": "Sauvegarder cette vue",
        "es": "Guardar esta vista",
        "zh": "保存此视图",
        "ar": "حفظ هذا العرض",
    },
    "filter.saved_views": {
        "en": "My views",
        "fr": "Mes vues",
        "es": "Mis vistas",
        "zh": "我的视图",
        "ar": "عروضي",
    },
    "filter.no_results": {
        "en": "No sources match the filters",
        "fr": "Aucune source ne correspond aux filtres",
        "es": "Ninguna fuente coincide con los filtros",
        "zh": "没有符合筛选条件的来源",
        "ar": "لا توجد مصادر تطابق المرشحات",
    },
    "filter.by_score": {
        "en": "Filter by score",
        "fr": "Filtrer par score",
        "es": "Filtrar por puntuación",
        "zh": "按分数筛选",
        "ar": "تصفية حسب الدرجة",
    },
    "filter.by_status": {
        "en": "Filter by status",
        "fr": "Filtrer par statut",
        "es": "Filtrar por estado",
        "zh": "按状态筛选",
        "ar": "تصفية حسب الحالة",
    },
    "filter.by_role": {
        "en": "Filter by role",
        "fr": "Filtrer par rôle",
        "es": "Filtrar por rol",
        "zh": "按角色筛选",
        "ar": "تصفية حسب الدور",
    },
    "filter.by_freshness": {
        "en": "Filter by freshness",
        "fr": "Filtrer par fraîcheur",
        "es": "Filtrar por frescura",
        "zh": "按新鲜度筛选",
        "ar": "تصفية حسب الحداثة",
    },
    "filter.by_text": {
        "en": "Search in text",
        "fr": "Rechercher dans le texte",
        "es": "Buscar en texto",
        "zh": "在文本中搜索",
        "ar": "البحث في النص",
    },
    "filter.score_range": {
        "en": "Score range ({min}-{max})",
        "fr": "Plage de score ({min}-{max})",
        "es": "Rango de puntuación ({min}-{max})",
        "zh": "分数范围 ({min}-{max})",
        "ar": "نطاق الدرجة ({min}-{max})",
    },
    "filter.freshness_days": {
        "en": "Used in last {days} days",
        "fr": "Utilisé dans les {days} derniers jours",
        "es": "Usado en los últimos {days} días",
        "zh": "最近 {days} 天内使用",
        "ar": "تم استخدامه في آخر {days} أيام",
    },
    "filter.clear": {
        "en": "Clear filters",
        "fr": "Effacer les filtres",
        "es": "Borrar filtros",
        "zh": "清除筛选",
        "ar": "مسح المرشحات",
    },
    # Saved views
    "view.name": {
        "en": "View name",
        "fr": "Nom de la vue",
        "es": "Nombre de la vista",
        "zh": "视图名称",
        "ar": "اسم العرض",
    },
    "view.saved": {
        "en": "View '{name}' saved",
        "fr": "Vue '{name}' sauvegardée",
        "es": "Vista '{name}' guardada",
        "zh": "视图 '{name}' 已保存",
        "ar": "تم حفظ العرض '{name}'",
    },
    "view.deleted": {
        "en": "View '{name}' deleted",
        "fr": "Vue '{name}' supprimée",
        "es": "Vista '{name}' eliminada",
        "zh": "视图 '{name}' 已删除",
        "ar": "تم حذف العرض '{name}'",
    },
    "view.applied": {
        "en": "View '{name}' applied",
        "fr": "Vue '{name}' appliquée",
        "es": "Vista '{name}' aplicada",
        "zh": "视图 '{name}' 已应用",
        "ar": "تم تطبيق العرض '{name}'",
    },
    "view.no_views": {
        "en": "No saved views",
        "fr": "Aucune vue sauvegardée",
        "es": "No hay vistas guardadas",
        "zh": "没有保存的视图",
        "ar": "لا توجد عروض محفوظة",
    },
    "view.delete_confirm": {
        "en": "Delete this view?",
        "fr": "Supprimer cette vue ?",
        "es": "¿Eliminar esta vista?",
        "zh": "删除此视图？",
        "ar": "هل تريد حذف هذا العرض؟",
    },
    # Bulk selection
    "bulk.select_mode": {
        "en": "Selection mode",
        "fr": "Mode sélection",
        "es": "Modo selección",
        "zh": "选择模式",
        "ar": "وضع التحديد",
    },
    "bulk.selected": {
        "en": "{count} selected",
        "fr": "{count} sélectionnée(s)",
        "es": "{count} seleccionada(s)",
        "zh": "已选择 {count} 个",
        "ar": "تم تحديد {count}",
    },
    "bulk.actions": {
        "en": "Bulk actions",
        "fr": "Actions groupées",
        "es": "Acciones masivas",
        "zh": "批量操作",
        "ar": "إجراءات جماعية",
    },
}


def get_lang() -> str:
    """Get the current language code."""
    return _current_lang


def set_lang(lang: str) -> None:
    """Set the current language."""
    global _current_lang
    if lang in LANGUAGES:
        _current_lang = lang
        _save_lang_preference(lang)


def t(key: str, **kwargs) -> str:
    """Get translated string for key.

    Args:
        key: Translation key (e.g., "menu.search")
        **kwargs: Format arguments for string interpolation

    Returns:
        Translated string, or key if not found
    """
    if key not in TRANSLATIONS:
        return key

    translations = TRANSLATIONS[key]
    text = translations.get(_current_lang, translations.get(DEFAULT_LANG, key))

    if kwargs:
        try:
            text = text.format(**kwargs)
        except (KeyError, ValueError):
            pass

    return text


def _get_lang_config_path() -> Path:
    """Get path to language preference file."""
    from rekall.paths import PathResolver
    paths = PathResolver.resolve()
    return paths.config_dir / "language"


def _save_lang_preference(lang: str) -> None:
    """Save language preference to config."""
    try:
        config_path = _get_lang_config_path()
        config_path.parent.mkdir(parents=True, exist_ok=True)
        config_path.write_text(lang)
    except Exception:
        pass  # Silently fail if can't save


def load_lang_preference() -> None:
    """Load language preference from config."""
    global _current_lang
    try:
        config_path = _get_lang_config_path()
        if config_path.exists():
            lang = config_path.read_text().strip()
            if lang in LANGUAGES:
                _current_lang = lang
    except Exception:
        pass  # Use default if can't load
