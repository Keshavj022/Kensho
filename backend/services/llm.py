"""LLM factory. Provider order is Azure OpenAI → Gemini → Ollama; importing never
touches the network. Embeddings use Azure when its deployment is set, else Gemini."""
from __future__ import annotations

from functools import lru_cache
from typing import Any, Optional

from loguru import logger

from ..config import settings


class LLMNotConfiguredError(RuntimeError):
    """Raised when no LLM provider (Azure OpenAI, Gemini, or Ollama) is available."""


def azure_available() -> bool:
    return settings.azure_openai_configured


def gemini_available() -> bool:
    return settings.gemini_configured


def ollama_available() -> bool:
    if not settings.OLLAMA_ENABLED:
        return False
    try:
        import langchain_ollama  # noqa: F401

        return True
    except Exception:
        return False


def is_llm_available() -> bool:
    return azure_available() or gemini_available() or ollama_available()


def embeddings_available() -> bool:
    return settings.azure_embeddings_configured or settings.gemini_configured


def providers_in_order() -> list[str]:
    """Available chat providers, Azure OpenAI first (then Gemini, then Ollama)."""
    order = []
    if azure_available():
        order.append("azure")
    if gemini_available():
        order.append("gemini")
    if ollama_available():
        order.append("ollama")
    return order


def default_provider() -> str:
    order = providers_in_order()
    if not order:
        raise LLMNotConfiguredError(
            "No LLM provider available (set AZURE_OPENAI_* or GEMINI_API_KEY, or enable Ollama)"
        )
    return order[0]


def _build_azure(deployment: str, temperature: float):
    if not settings.azure_openai_configured:
        raise LLMNotConfiguredError("AZURE_OPENAI_ENDPOINT / AZURE_OPENAI_API_KEY not set")
    from langchain_openai import AzureChatOpenAI

    logger.debug(f"Building Azure OpenAI chat model: {deployment} (temp={temperature})")
    return AzureChatOpenAI(
        azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
        api_key=settings.AZURE_OPENAI_API_KEY,
        azure_deployment=deployment,
        api_version=settings.AZURE_OPENAI_API_VERSION,
        temperature=temperature,
    )


def _build_gemini(model_name: str, temperature: float):
    if not settings.gemini_configured:
        raise LLMNotConfiguredError("GEMINI_API_KEY is not set")
    from langchain_google_genai import ChatGoogleGenerativeAI

    logger.debug(f"Building Gemini chat model: {model_name} (temp={temperature})")
    return ChatGoogleGenerativeAI(
        model=model_name, google_api_key=settings.GEMINI_API_KEY, temperature=temperature
    )


def _build_ollama(model_name: str, temperature: float):
    from langchain_ollama import ChatOllama

    logger.debug(f"Building Ollama chat model: {model_name} (temp={temperature})")
    return ChatOllama(model=model_name, base_url=settings.OLLAMA_BASE_URL, temperature=temperature)


@lru_cache(maxsize=8)
def get_llm(model_name: Optional[str] = None, temperature: Optional[float] = None):
    """Default Gemini chat model for agents. Cached per (model, temperature)."""
    return _build_gemini(
        model_name or settings.GEMINI_MODEL,
        settings.GEMINI_TEMPERATURE if temperature is None else temperature,
    )


@lru_cache(maxsize=2)
def get_pro_llm(temperature: float = 0.0):
    """Stronger Gemini model — used to escalate hard menu OCR."""
    return _build_gemini(settings.GEMINI_PRO_MODEL, temperature)


@lru_cache(maxsize=4)
def get_ollama_llm(model_name: Optional[str] = None, temperature: Optional[float] = None):
    return _build_ollama(
        model_name or settings.OLLAMA_MODEL,
        settings.OLLAMA_TEMPERATURE if temperature is None else temperature,
    )


@lru_cache(maxsize=8)
def get_azure_llm(deployment: Optional[str] = None, temperature: Optional[float] = None):
    """Default Azure OpenAI chat model (multimodal — also handles menu OCR)."""
    return _build_azure(
        deployment or settings.AZURE_OPENAI_DEPLOYMENT,
        settings.AZURE_OPENAI_TEMPERATURE if temperature is None else temperature,
    )


@lru_cache(maxsize=2)
def get_azure_pro_llm(temperature: float = 0.0):
    """Stronger Azure deployment — used to escalate hard menu OCR."""
    return _build_azure(settings.AZURE_OPENAI_PRO_DEPLOYMENT, temperature)


def get_chat_llm(provider: str, temperature: Optional[float] = None):
    """Build a tool-capable chat model for a provider ('azure'|'gemini'|'ollama')."""
    if provider == "azure":
        return get_azure_llm(temperature=temperature)
    if provider == "gemini":
        return get_llm(temperature=temperature)
    if provider == "ollama":
        return get_ollama_llm(temperature=temperature)
    raise ValueError(f"Unknown LLM provider: {provider}")


@lru_cache(maxsize=1)
def get_embeddings():
    """The single embedding space for every Chroma collection.

    Azure OpenAI embeddings when an embedding deployment is configured, else Gemini.
    """
    if settings.azure_embeddings_configured:
        from langchain_openai import AzureOpenAIEmbeddings

        logger.debug("Using Azure OpenAI embeddings")
        return AzureOpenAIEmbeddings(
            azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
            api_key=settings.AZURE_OPENAI_API_KEY,
            azure_deployment=settings.AZURE_OPENAI_EMBEDDING_DEPLOYMENT,
            api_version=settings.AZURE_OPENAI_API_VERSION,
        )
    if not settings.gemini_configured:
        raise LLMNotConfiguredError("No embedding provider (set AZURE_OPENAI_EMBEDDING_DEPLOYMENT or GEMINI_API_KEY)")
    from langchain_google_genai import GoogleGenerativeAIEmbeddings

    return GoogleGenerativeAIEmbeddings(
        model=settings.GEMINI_EMBEDDING_MODEL, google_api_key=settings.GEMINI_API_KEY
    )


def invoke_with_fallback(messages: Any, *, vision: bool = False, temperature: float = 0.0, use_pro: bool = False):
    """Invoke an LLM for a one-shot call, trying Azure → Gemini → Ollama.

    Used by the OCR + order-resolution call sites (not the agent graphs, which do
    their own graph-level fallback). `vision=True` selects a vision-capable model
    (Azure gpt-4o(-mini) and Gemini are multimodal; Ollama uses its vision model).
    Raises LLMNotConfiguredError if every provider fails.
    """
    errors: list[str] = []
    if azure_available():
        try:
            model = get_azure_pro_llm(temperature) if use_pro else get_azure_llm(temperature=temperature)
            return model.invoke(messages)
        except Exception as e:
            logger.warning(f"Azure OpenAI invoke failed ({'vision' if vision else 'text'}): {e}")
            errors.append(f"azure: {e}")
    if gemini_available():
        try:
            model = get_pro_llm(temperature) if use_pro else get_llm(temperature=temperature)
            return model.invoke(messages)
        except Exception as e:
            logger.warning(f"Gemini invoke failed ({'vision' if vision else 'text'}): {e}")
            errors.append(f"gemini: {e}")
    if ollama_available():
        try:
            model_name = settings.OLLAMA_VISION_MODEL if vision else settings.OLLAMA_MODEL
            return get_ollama_llm(model_name, temperature).invoke(messages)
        except Exception as e:
            logger.warning(f"Ollama invoke failed: {e}")
            errors.append(f"ollama: {e}")
    raise LLMNotConfiguredError("All LLM providers failed: " + " | ".join(errors) if errors else "No LLM provider available")


def reset_llm_caches() -> None:
    """Clear cached clients (tests after mutating env/settings)."""
    get_llm.cache_clear()
    get_pro_llm.cache_clear()
    get_ollama_llm.cache_clear()
    get_azure_llm.cache_clear()
    get_azure_pro_llm.cache_clear()
    get_embeddings.cache_clear()
