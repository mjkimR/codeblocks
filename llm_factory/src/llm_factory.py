import json
import os.path
from typing import Any, Literal

from langchain_core.embeddings import Embeddings
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_openai.chat_models.base import BaseChatModel

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
            llm = ChatModelFactory.create_model(provider, **kwargs)
        elif llm_type == "embedding":
            llm = EmbeddingModelFactory.create_model(provider, **kwargs)
        else:
            raise ValueError(f"Unsupported LLM type: {llm_type}")

        if patchers:
            for patcher in patchers:
                llm = patcher.from_llm(llm)
        return llm

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


class ChatModelFactory:
    @staticmethod
    def create_model(
            provider: Literal["openai", "lm_studio"],
            **kwargs
    ) -> BaseChatModel:
        """
        Creates a LangChain-based chat model using the specified provider.

        This factory method selects the appropriate creation method for the given provider and returns a
        LangChain `BaseChatModel` instance.

        Args:
            provider (Literal["openai", "lm_studio"]): The provider of the LangChain chat model. Supported providers are "openai" and "lm_studio".
            **kwargs: Additional keyword arguments passed to the underlying model creation method.

        Returns:
            BaseChatModel: The LangChain chat model instance.

        Raises:
            ValueError: If an unsupported provider is specified.
        """
        _create_method = {
            "openai": ChatModelFactory._create_openai,
            "lm_studio": ChatModelFactory._create_lm_studio,
        }.get(provider)
        if _create_method is None:
            raise ValueError(f"Unsupported LLM provider for ChatModel: {provider}")
        return _create_method(**kwargs)

    @staticmethod
    def _create_openai(**kwargs: Any) -> BaseChatModel:
        return ChatOpenAI(**kwargs)

    @staticmethod
    def _create_lm_studio(base_url="http://localhost:1234/v1", api_key="NO_NEED", **kwargs: Any) -> BaseChatModel:
        return ChatOpenAI(base_url=base_url, api_key=api_key, **kwargs)


class EmbeddingModelFactory:
    @staticmethod
    def create_model(
            provider: Literal["openai", "lm_studio"],
            **kwargs
    ) -> Embeddings:
        """
        Creates a LangChain-based embedding model using the specified provider.

        This factory method selects the appropriate creation method for the given provider and returns a
        LangChain `Embeddings` instance.

        Args:
            provider (Literal["openai", "lm_studio"]): The provider of the LangChain embedding model. Supported providers are "openai" and "lm_studio".
            **kwargs: Additional keyword arguments passed to the underlying model creation method.

        Returns:
            Embeddings: The LangChain embedding model instance.

        Raises:
            ValueError: If an unsupported provider is specified.
        """
        _create_method = {
            "openai": EmbeddingModelFactory._create_openai,
            "lm_studio": EmbeddingModelFactory._create_lm_studio,
        }.get(provider)
        if _create_method is None:
            raise ValueError(f"Unsupported LLM provider for EmbeddingModel: {provider}")
        return _create_method(**kwargs)

    @staticmethod
    def _create_openai(**kwargs: Any) -> Embeddings:
        return OpenAIEmbeddings(**kwargs)

    @staticmethod
    def _create_lm_studio(base_url="http://localhost:1234/v1", api_key="NO_NEED", **kwargs: Any) -> Embeddings:
        return OpenAIEmbeddings(base_url=base_url, api_key=api_key, **kwargs)
