import json
import os.path
from typing import Any, Literal

from langchain_openai import ChatOpenAI, OpenAIEmbeddings

from patcher.base import BaseLLMPatcher


class LLMFactory:
    @staticmethod
    def create_llm(
            llm_type: Literal["chat", "embedding"],
            provider: Literal["openai", "lm_studio"],
            patchers: list[BaseLLMPatcher] | None = None,
            **kwargs
    ) -> Any:
        """
        Creates a LangChain-based LLM (Large Language Model) instance based on the specified type and provider.

        This factory method leverages LangChain to create either a "chat" or "embedding" model, and optionally applies
        a series of patchers to modify or enhance the model's behavior.

        Args:
            llm_type (Literal["chat", "embedding"]): The type of LangChain model to create. Can be "chat" or "embedding".
            provider (Literal["openai", "lm_studio"]): The provider of the LangChain model. Can be "openai" or "lm_studio".
            patchers (list[BaseLLMPatcher] | None, optional): A list of LangChain patchers to apply to the model. Defaults to None.
            **kwargs: Additional keyword arguments passed to the underlying LangChain model creation method.

        Returns:
            Any: The created LangChain LLM instance.

        Raises:
            ValueError: If an unsupported LLM type is provided.
        """
        if llm_type == "chat":
            llm_class, configs = ChatModelConfigFactory.create_model(provider, **kwargs)
        elif llm_type == "embedding":
            llm_class, configs = EmbeddingModelConfigFactory.create_model(provider, **kwargs)
        else:
            raise ValueError(f"Unsupported LLM type: {llm_type}")

        if patchers:
            for patcher in patchers:
                llm_class = patcher.from_llm_class(llm_class)
        return llm_class(**configs)

    @staticmethod
    def from_template(key: str, json_path=".template"):
        """
        Creates a LangChain-based LLM instance using a predefined template.

        This method reads a configuration from a JSON template file and creates the corresponding LangChain model.

        Args:
            key (str): The key to look up the configuration in the JSON template file.
            json_path (str, optional): The path to the JSON file containing the LangChain model template. Defaults to ".template".

        Returns:
            Any: The created LangChain LLM instance configured via the template.

        Raises:
            FileNotFoundError: If the specified template file does not exist.
            KeyError: If the key is not found in the template file.
        """
        if not os.path.exists(json_path):
            raise FileNotFoundError(f"Cannot find the template file: {json_path}")
        with open(json_path, "r") as f:
            template = json.load(f)
        if key not in template:
            raise KeyError(f"Cannot find the key in the template: {key}")
        return LLMFactory.create_llm(**template[key])


class ChatModelConfigFactory:
    @classmethod
    def create_model(
            cls,
            provider: Literal["openai", "lm_studio"],
            **kwargs
    ) -> (type, dict):
        """
        Creates a chat model configuration based on the specified provider.

        Args:
            provider (Literal["openai", "lm_studio"]): The provider of the chat model. Can be "openai" or "lm_studio".
            **kwargs: Additional keyword arguments passed to the model creation method.

        Returns:
            tuple: A tuple containing the model class and its configuration dictionary.

        Raises:
            ValueError: If an unsupported provider is specified.
        """
        _create_method = {
            "openai": cls._create_openai,
            "lm_studio": cls._create_lm_studio,
        }.get(provider)
        if _create_method is None:
            raise ValueError(f"Unsupported LLM provider for ChatModel: {provider}")
        return _create_method(**kwargs)

    @classmethod
    def _create_openai(cls, **kwargs: Any) -> (type, dict):
        return ChatOpenAI, kwargs

    @classmethod
    def _create_lm_studio(cls, base_url="http://localhost:1234/v1", api_key="NO_NEED", **kwargs: Any) -> (type, dict):
        return ChatOpenAI, {"base_url": base_url, "api_key": api_key, **kwargs}


class EmbeddingModelConfigFactory:
    @classmethod
    def create_model(
            cls,
            provider: Literal["openai", "lm_studio"],
            **kwargs
    ) -> (type, dict):
        """
        Creates an embedding model configuration based on the specified provider.

        Args:
            provider (Literal["openai", "lm_studio"]): The provider of the embedding model. Can be "openai" or "lm_studio".
            **kwargs: Additional keyword arguments passed to the model creation method.

        Returns:
            tuple: A tuple containing the model class and its configuration dictionary.

        Raises:
            ValueError: If an unsupported provider is specified.
        """
        _create_method = {
            "openai": cls._create_openai,
            "lm_studio": cls._create_lm_studio,
        }.get(provider)
        if _create_method is None:
            raise ValueError(f"Unsupported LLM provider for EmbeddingModel: {provider}")
        return _create_method(**kwargs)

    @classmethod
    def _create_openai(cls, **kwargs: Any) -> (type, dict):
        return OpenAIEmbeddings, kwargs

    @classmethod
    def _create_lm_studio(cls, base_url="http://localhost:1234/v1", api_key="NO_NEED", **kwargs: Any) -> (type, dict):
        return OpenAIEmbeddings, {"base_url": base_url, "api_key": api_key, **kwargs}
