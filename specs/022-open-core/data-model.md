# Data Model: 022-open-core

**Date**: 2025-12-13
**Feature**: Architecture Open Core

## Entités

### 1. DatabaseBackend (ABC)

Interface abstraite pour tous les backends de base de données.

```python
from abc import ABC, abstractmethod
from typing import Any, Optional, List, Dict

class DatabaseBackend(ABC):
    """Interface abstraite pour les backends de base de données."""

    @abstractmethod
    def connect(self) -> None:
        """Établit la connexion à la base de données."""
        pass

    @abstractmethod
    def close(self) -> None:
        """Ferme la connexion proprement."""
        pass

    @abstractmethod
    def execute(self, query: str, params: Optional[tuple] = None) -> Any:
        """Exécute une requête SQL."""
        pass

    @abstractmethod
    def fetch_one(self, query: str, params: Optional[tuple] = None) -> Optional[Dict]:
        """Récupère une seule ligne."""
        pass

    @abstractmethod
    def fetch_all(self, query: str, params: Optional[tuple] = None) -> List[Dict]:
        """Récupère toutes les lignes."""
        pass

    @abstractmethod
    def is_connected(self) -> bool:
        """Vérifie si la connexion est active."""
        pass
```

**Attributs clés:**
- Pas d'attributs d'instance dans l'ABC
- Les implémentations concrètes définissent leurs propres attributs (path, pool_size, etc.)

### 2. CacheBackend (ABC)

Interface abstraite pour tous les backends de cache.

```python
from abc import ABC, abstractmethod
from typing import Any, Optional

class CacheBackend(ABC):
    """Interface abstraite pour les backends de cache."""

    @abstractmethod
    def get(self, key: str) -> Optional[Any]:
        """Récupère une valeur du cache."""
        pass

    @abstractmethod
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Stocke une valeur dans le cache."""
        pass

    @abstractmethod
    def delete(self, key: str) -> bool:
        """Supprime une entrée du cache."""
        pass

    @abstractmethod
    def clear(self) -> None:
        """Vide tout le cache."""
        pass

    @abstractmethod
    def exists(self, key: str) -> bool:
        """Vérifie si une clé existe."""
        pass
```

### 3. ServiceContainer

Registre central pour les backends, pattern singleton.

```python
class ServiceContainer:
    """Conteneur de services singleton."""

    _instance: Optional['ServiceContainer'] = None
    _backends: Dict[str, Any]
    _initialized: bool

    # Méthodes
    @classmethod
    def get_instance(cls) -> 'ServiceContainer': ...

    def register(self, name: str, backend: Any) -> None: ...
    def get(self, name: str) -> Any: ...
    def has(self, name: str) -> bool: ...
    def reset(self) -> None: ...  # Pour les tests
```

**Attributs:**
| Attribut | Type | Description |
|----------|------|-------------|
| `_instance` | Optional[ServiceContainer] | Instance singleton |
| `_backends` | Dict[str, Any] | Registre des backends |
| `_initialized` | bool | Flag d'initialisation |

### 4. DefaultDatabaseBackend

Implémentation SQLite existante adaptée à l'interface.

```python
class DefaultDatabaseBackend(DatabaseBackend):
    """Implémentation SQLite par défaut."""

    _connection: Optional[sqlite3.Connection]
    _path: Path
    _wal_enabled: bool
```

### 5. DefaultCacheBackend

Implémentation cache local existante adaptée à l'interface.

```python
class DefaultCacheBackend(CacheBackend):
    """Implémentation cache mémoire par défaut."""

    _cache: Dict[str, Any]
    _timestamps: Dict[str, float]
    _max_size: int
```

## Relations

```
┌─────────────────┐       implements       ┌───────────────────────┐
│ DatabaseBackend │◄──────────────────────│ DefaultDatabaseBackend │
│     (ABC)       │                        └───────────────────────┘
└─────────────────┘

┌─────────────────┐       implements       ┌───────────────────────┐
│  CacheBackend   │◄──────────────────────│  DefaultCacheBackend   │
│     (ABC)       │                        └───────────────────────┘
└─────────────────┘

┌──────────────────┐       registers       ┌─────────────────┐
│ ServiceContainer │─────────────────────►│ *Backend (any)  │
└──────────────────┘                       └─────────────────┘
```

## États / Lifecycle

### Backend Lifecycle

```
┌─────────┐     connect()     ┌───────────┐
│ Created │──────────────────►│ Connected │
└─────────┘                   └─────┬─────┘
                                    │
                              execute/fetch
                                    │
                              ┌─────▼─────┐
                              │  Active   │◄──────┐
                              └─────┬─────┘       │
                                    │         retry (x3)
                              error │             │
                                    ▼             │
                              ┌───────────┐       │
                              │  Retry    │───────┘
                              └─────┬─────┘
                                    │ max retries
                                    ▼
                              ┌───────────┐
                              │  Failed   │
                              └───────────┘
```

### ServiceContainer Lifecycle

```
┌─────────────┐    get_instance()    ┌─────────────┐
│ Not Created │─────────────────────►│ Initialized │
└─────────────┘                      └──────┬──────┘
                                            │
                                      register()
                                            │
                                     ┌──────▼──────┐
                                     │  Populated  │
                                     └─────────────┘
```

## Contraintes de validation

1. **Unicité des noms de backend**: Un seul backend par nom dans le container
2. **Type checking**: Les backends doivent implémenter l'ABC correspondante
3. **Thread safety**: Le ServiceContainer doit être thread-safe (lock sur register/get)
