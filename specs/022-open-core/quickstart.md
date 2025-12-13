# Quickstart: 022-open-core

## Pour les utilisateurs Home (aucun changement)

```bash
# Installation standard - rien ne change
uv pip install rekall

# Utilisation standard - rien ne change
rekall search "query"
rekall add --type bug "Title"
```

## Pour les développeurs de plugins

### Créer un backend personnalisé

```python
from rekall.infra.interfaces import DatabaseBackend, CacheBackend
from rekall.infra.container import register_backend

class MyCustomCache(CacheBackend):
    """Mon cache personnalisé."""

    def __init__(self, redis_url: str):
        self._client = redis.Redis.from_url(redis_url)

    def get(self, key: str):
        return self._client.get(key)

    def set(self, key: str, value, ttl=None):
        self._client.set(key, value, ex=ttl)

    def delete(self, key: str):
        return bool(self._client.delete(key))

    def clear(self):
        self._client.flushdb()

    def exists(self, key: str):
        return self._client.exists(key)


# Enregistrer le backend personnalisé
register_backend('cache', MyCustomCache('redis://localhost:6379'))
```

### Vérifier le backend actif

```python
from rekall.infra.container import ServiceContainer

container = ServiceContainer.get_instance()
print(f"Database: {type(container.get('database')).__name__}")
print(f"Cache: {type(container.get('cache')).__name__}")
```

## Activer le mode debug

```toml
# ~/.config/rekall/config.toml
[rekall]
debug = true
```

Les logs détaillés des opérations backend seront affichés.

## Tests

```bash
# Lancer tous les tests
pytest tests/

# Tester uniquement les interfaces
pytest tests/unit/test_interfaces.py

# Tester l'intégration des backends
pytest tests/integration/test_backends.py
```

## Prochaines étapes

1. Installer rekall normalement
2. (Optionnel) Créer un backend personnalisé
3. (Optionnel) Activer le mode debug pour diagnostiquer
