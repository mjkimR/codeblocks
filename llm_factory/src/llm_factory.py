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
