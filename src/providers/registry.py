"""Provider registry for GirlfriendGPT."""

from __future__ import annotations

from typing import Any, Dict, Optional, Type
from .base import BaseProvider, ProviderConfig


class ProviderRegistry:
    """Registry for LLM providers.

    This class provides:
    - Provider registration
    - Provider lookup
    - Default provider management
    """

    _providers: Dict[str, Type[BaseProvider]] = {}
    _default_provider: Optional[str] = None

    @classmethod
    def register(
        cls, name: str, provider_class: Type[BaseProvider], set_default: bool = False
    ) -> None:
        """Register a provider.

        Args:
            name: Provider name
            provider_class: Provider class
            set_default: Whether to set as default provider
        """
        cls._providers[name] = provider_class
        if set_default or not cls._default_provider:
            cls._default_provider = name

    @classmethod
    def create_provider(
        cls, name: Optional[str] = None, config: Optional[ProviderConfig] = None
    ) -> BaseProvider:
        """Create a provider instance.

        Args:
            name: Provider name (uses default if not specified)
            config: Provider configuration

        Returns:
            Provider instance

        Raises:
            ValueError: If provider not found
        """
        provider_name = name or cls._default_provider
        if not provider_name:
            raise ValueError("No providers registered and no name specified")

        provider_class = cls._providers.get(provider_name)
        if not provider_class:
            raise ValueError(f"Provider '{provider_name}' not found")

        return provider_class(config or ProviderConfig())

    @classmethod
    def get_provider_names(cls) -> list[str]:
        """Get list of registered provider names.

        Returns:
            List of provider names
        """
        return list(cls._providers.keys())

    @classmethod
    def get_default_provider_name(cls) -> Optional[str]:
        """Get the default provider name.

        Returns:
            Default provider name or None
        """
        return cls._default_provider

    @classmethod
    def is_registered(cls, name: str) -> bool:
        """Check if a provider is registered.

        Args:
            name: Provider name

        Returns:
            True if registered
        """
        return name in cls._providers

    @classmethod
    def clear(cls) -> None:
        """Clear all registered providers."""
        cls._providers.clear()
        cls._default_provider = None
