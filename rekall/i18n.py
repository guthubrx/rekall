"""Rekall internationalization (i18n) support."""

from __future__ import annotations

from typing import Optional
from pathlib import Path
import json

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
        "en": "Install IDE",
        "fr": "Install IDE",
        "es": "Instalar IDE",
        "zh": "安装IDE",
        "ar": "تثبيت IDE",
    },
    "menu.install_ide.desc": {
        "en": "Cursor/Claude integrations...",
        "fr": "Intégrations Cursor/Claude...",
        "es": "Integraciones Cursor/Claude...",
        "zh": "Cursor/Claude集成...",
        "ar": "تكاملات Cursor/Claude...",
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
        "fr": "Recherche",
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
        "en": "Browse/Search",
        "fr": "Parcourir/Chercher",
        "es": "Explorar/Buscar",
        "zh": "浏览/搜索",
        "ar": "تصفح/بحث",
    },
    "menu.browse.desc": {
        "en": "Browse all entries",
        "fr": "Parcourir les entrées",
        "es": "Explorar las entradas",
        "zh": "浏览所有条目",
        "ar": "تصفح جميع الإدخالات",
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
        "en": "Export/Import",
        "fr": "Export/Import",
        "es": "Exportar/Importar",
        "zh": "导出/导入",
        "ar": "تصدير/استيراد",
    },
    "menu.export.desc": {
        "en": "Backup/restore .rekall",
        "fr": "Sauvegarder/restaurer .rekall",
        "es": "Guardar/restaurar .rekall",
        "zh": "备份/恢复 .rekall",
        "ar": "نسخ احتياطي/استعادة .rekall",
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
    "browse.updated": {
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
    "import.external_db": {
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
