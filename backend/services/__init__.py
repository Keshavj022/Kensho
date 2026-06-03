"""
Services package.

NOTE: this __init__ intentionally imports nothing. The legacy version eagerly
imported every service (including the Azure ones), which makes a single missing
dependency crash the whole app at import time. Import the specific service module
you need directly, e.g.:

    from backend.services.knowledge_graph_service import knowledge_graph_service
    from backend.services.llm import get_llm
"""
