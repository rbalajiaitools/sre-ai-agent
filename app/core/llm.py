"""LLM provider factory supporting OpenAI, Azure OpenAI, and Anthropic."""

from typing import Any

from langchain_openai import ChatOpenAI, AzureChatOpenAI
from langchain_core.language_models import BaseChatModel

from app.core.config import LLMSettings


class LLMFactory:
    """Factory for creating LLM instances based on configuration."""

    @staticmethod
    def create_llm(settings: LLMSettings) -> BaseChatModel:
        """Create an LLM instance based on provider configuration.

        Args:
            settings: LLM configuration settings

        Returns:
            BaseChatModel: Configured LLM instance

        Raises:
            ValueError: If provider is not supported or required credentials are missing
        """
        provider = settings.provider.lower()

        if provider == "openai":
            return LLMFactory._create_openai(settings)
        elif provider == "azure":
            return LLMFactory._create_azure_openai(settings)
        elif provider == "anthropic":
            return LLMFactory._create_anthropic(settings)
        else:
            raise ValueError(
                f"Unsupported LLM provider: {provider}. "
                f"Supported providers: openai, azure, anthropic"
            )

    @staticmethod
    def _create_openai(settings: LLMSettings) -> ChatOpenAI:
        """Create OpenAI LLM instance.

        Args:
            settings: LLM configuration settings

        Returns:
            ChatOpenAI: Configured OpenAI LLM

        Raises:
            ValueError: If API key is missing
        """
        if not settings.openai_api_key:
            raise ValueError("OPENAI_API_KEY is required when using OpenAI provider")

        return ChatOpenAI(
            model=settings.openai_model,
            api_key=settings.openai_api_key,
            temperature=settings.temperature,
            max_tokens=settings.max_tokens,
        )

    @staticmethod
    def _create_azure_openai(settings: LLMSettings) -> AzureChatOpenAI:
        """Create Azure OpenAI LLM instance.

        Args:
            settings: LLM configuration settings

        Returns:
            AzureChatOpenAI: Configured Azure OpenAI LLM

        Raises:
            ValueError: If required Azure credentials are missing
        """
        if not settings.azure_openai_endpoint:
            raise ValueError("AZURE_OPENAI_ENDPOINT is required when using Azure provider")
        if not settings.azure_openai_api_key:
            raise ValueError("AZURE_OPENAI_API_KEY is required when using Azure provider")
        if not settings.azure_openai_deployment_name:
            raise ValueError(
                "AZURE_OPENAI_DEPLOYMENT_NAME is required when using Azure provider"
            )

        return AzureChatOpenAI(
            azure_endpoint=settings.azure_openai_endpoint,
            api_key=settings.azure_openai_api_key,
            deployment_name=settings.azure_openai_deployment_name,
            api_version=settings.azure_openai_api_version,
            temperature=settings.temperature,
            max_tokens=settings.max_tokens,
        )

    @staticmethod
    def _create_anthropic(settings: LLMSettings) -> Any:
        """Create Anthropic LLM instance.

        Args:
            settings: LLM configuration settings

        Returns:
            ChatAnthropic: Configured Anthropic LLM

        Raises:
            ValueError: If API key is missing
        """
        if not settings.anthropic_api_key:
            raise ValueError("ANTHROPIC_API_KEY is required when using Anthropic provider")

        try:
            from langchain_anthropic import ChatAnthropic
        except ImportError:
            raise ImportError(
                "langchain-anthropic is not installed. "
                "Install it with: pip install langchain-anthropic"
            )

        return ChatAnthropic(
            model=settings.anthropic_model,
            api_key=settings.anthropic_api_key,
            temperature=settings.temperature,
            max_tokens=settings.max_tokens,
        )


def get_llm(settings: LLMSettings | None = None) -> BaseChatModel:
    """Get configured LLM instance.

    Args:
        settings: Optional LLM settings. If not provided, loads from environment.

    Returns:
        BaseChatModel: Configured LLM instance
    """
    if settings is None:
        from app.core.config import get_settings
        settings = get_settings().llm

    return LLMFactory.create_llm(settings)
