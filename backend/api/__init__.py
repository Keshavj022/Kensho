"""
API package.

Intentionally imports nothing: route modules are included explicitly in main.py
(e.g. `from .api.health_routes import router`). The legacy version imported the
Azure-backed routes here, which crashes the app when azure-* isn't installed.
"""
